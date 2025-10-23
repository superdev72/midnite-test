import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser
from django.db import transaction, IntegrityError

from .serializers import EventSerializer, EventResponseSerializer
from .models import Event, User
from .services import AlertRuleEngine

logger = logging.getLogger(__name__)


class EventView(APIView):
    """
    API endpoint to receive user events and return alert information.
    """

    parser_classes = [JSONParser]

    def post(self, request):
        """
        Process incoming event and return alert status.
        """
        logger.info(f"Received event request: {request.data}")

        # Validate incoming data
        serializer = EventSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid payload received: {serializer.errors}")
            return Response(
                {"error": "Invalid payload", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_data = serializer.validated_data

        # Extract data
        transaction_type = validated_data["type"]
        amount = validated_data["amount"]
        user_id = validated_data["user_id"]
        client_timestamp = validated_data["t"]  # Use client timestamp

        # Get the user object
        user = User.objects.get(id=user_id)

        logger.info(
            f"Processing event: user_id={user_id}, type={transaction_type}, "
            f"amount={amount}, timestamp={client_timestamp}"
        )

        # Use database transaction to ensure data consistency
        try:
            with transaction.atomic():
                # Save the event to database with client timestamp
                Event.objects.create(
                    user=user,
                    transaction_type=transaction_type,
                    amount=amount,
                    timestamp=client_timestamp,
                )
                logger.debug(f"Event saved to database for user {user.name}")

                # Evaluate alert rules
                alert_codes = AlertRuleEngine.evaluate_all_rules(
                    user=user,
                    transaction_type=transaction_type,
                    amount=amount,
                    timestamp=client_timestamp,
                )
        except IntegrityError as e:
            if "timestamp" in str(e) and "unique" in str(e):
                logger.warning(f"Duplicate timestamp {client_timestamp} for user {user.name}")
                return Response(
                    {
                        "error": "Duplicate timestamp",
                        "message": f"An event with timestamp {client_timestamp} already exists",
                        "user_id": user_id,
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            else:
                logger.error(f"Database integrity error: {e}")
                return Response(
                    {"error": "Database error", "message": "Failed to save event"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # Prepare response
        response_data = {
            "alert": len(alert_codes) > 0,
            "alert_codes": alert_codes,
            "user_id": user_id,
        }

        logger.info(
            f"Event processed successfully for user {user.name}: "
            f"alert={response_data['alert']}, codes={alert_codes}"
        )

        # Validate response format
        response_serializer = EventResponseSerializer(data=response_data)
        if not response_serializer.is_valid():
            logger.error(f"Response validation failed: {response_serializer.errors}")
            return Response(
                {"error": "Response validation failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(response_data, status=status.HTTP_200_OK)
