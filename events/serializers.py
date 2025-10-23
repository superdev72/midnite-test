from rest_framework import serializers
from .models import User, Event


class EventSerializer(serializers.Serializer):
    """
    Serializer for incoming event data.
    """

    type = serializers.ChoiceField(choices=["deposit", "withdraw"])
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    user_id = serializers.IntegerField(min_value=1)
    t = serializers.IntegerField(min_value=0, help_text="Client timestamp (Unix timestamp)")

    def validate_amount(self, value):
        """Ensure amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value

    def validate(self, data):
        """Validate the entire payload."""
        timestamp = data.get("t")

        if timestamp is not None:
            # Check if timestamp is greater than the global maximum timestamp
            latest_event = Event.objects.order_by("-timestamp").first()

            if latest_event and timestamp <= latest_event.timestamp:
                raise serializers.ValidationError(
                    {
                        "t": f"Timestamp {timestamp} must be greater than the latest "
                        f"timestamp {latest_event.timestamp} in the system"
                    }
                )

        return data

    def validate_user_id(self, value):
        """Ensure user exists."""
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        return value


class EventResponseSerializer(serializers.Serializer):
    """
    Serializer for event response data.
    """

    alert = serializers.BooleanField()
    alert_codes = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)
    user_id = serializers.IntegerField()
