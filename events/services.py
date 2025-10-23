import logging
from decimal import Decimal
from typing import List
from .models import Event, User

logger = logging.getLogger(__name__)


class AlertRuleEngine:
    """
    Engine to evaluate alert rules based on user event history.
    """

    @staticmethod
    def check_withdraw_over_100(user: User, amount: Decimal) -> bool:
        """
        Code 1100: A withdraw amount over 100
        """
        logger.debug(f"Checking withdraw over 100 for user {user.name}, amount: {amount}")
        result = amount > Decimal("100.00")
        if result:
            logger.warning(f"Alert 1100 triggered: User {user.name} withdrew {amount} (>100)")
        return result

    @staticmethod
    def check_3_consecutive_withdraws(user: User, timestamp: int) -> bool:
        """
        Code 30: 3 consecutive withdraws
        """
        logger.debug(
            f"Checking 3 consecutive withdraws for user {user.name} at timestamp {timestamp}"
        )

        # Get the last 3 events for this user, ordered by timestamp descending
        recent_events = Event.objects.filter(user=user, timestamp__lte=timestamp).order_by(
            "-timestamp"
        )[:3]

        logger.debug(f"Found {len(recent_events)} recent events for user {user.name}")

        # Check if we have exactly 3 events and all are withdraws
        if len(recent_events) < 3:
            logger.debug(
                f"Not enough events for user {user.name} (need 3, have {len(recent_events)})"
            )
            return False

        result = all(event.transaction_type == "withdraw" for event in recent_events)
        if result:
            logger.warning(f"Alert 30 triggered: User {user.name} made 3 consecutive withdraws")
        return result

    @staticmethod
    def check_3_consecutive_increasing_deposits(user: User, timestamp: int) -> bool:
        """
        Code 300: 3 consecutive increasing deposits (ignoring withdraws)
        """
        logger.debug(
            f"Checking 3 consecutive increasing deposits for user {user.name} "
            f"at timestamp {timestamp}"
        )

        # Get all deposit events for this user up to the current timestamp
        deposit_events = Event.objects.filter(
            user=user, transaction_type="deposit", timestamp__lte=timestamp
        ).order_by("-timestamp")

        logger.debug(f"Found {len(deposit_events)} deposit events for user {user.name}")

        # Need at least 3 deposits
        if len(deposit_events) < 3:
            logger.debug(
                f"Not enough deposits for user {user.name} (need 3, have {len(deposit_events)})"
            )
            return False

        # Check if the last 3 deposits are in increasing order
        last_3_deposits = deposit_events[:3]

        # Check if amounts are increasing (newest to oldest)
        amounts = [deposit.amount for deposit in last_3_deposits]
        logger.debug(f"Last 3 deposit amounts for user {user.name}: {amounts}")

        # For consecutive increasing, we need: amount[0] > amount[1] > amount[2]
        # where amount[0] is the most recent
        result = amounts[0] > amounts[1] > amounts[2]
        if result:
            logger.warning(
                f"Alert 300 triggered: User {user.name} made 3 consecutive increasing deposits"
            )
        return result

    @staticmethod
    def check_accumulative_deposit_over_200_in_30_seconds(user: User, timestamp: int) -> bool:
        """
        Code 123: Accumulative deposit amount over a window of 30 seconds is over 200
        """
        logger.debug(
            f"Checking accumulative deposits over 200 in 30s for user {user.name} "
            f"at timestamp {timestamp}"
        )

        # Get all deposit events for this user in the last 30 seconds
        window_start = timestamp - 30

        deposit_events = Event.objects.filter(
            user=user,
            transaction_type="deposit",
            timestamp__gte=window_start,
            timestamp__lte=timestamp,
        )

        logger.debug(f"Found {len(deposit_events)} deposits in 30s window for user {user.name}")

        # Calculate total deposit amount in the window
        total_amount = sum(event.amount for event in deposit_events)
        logger.debug(f"Total deposit amount in 30s window for user {user.name}: {total_amount}")

        result = total_amount > Decimal("200.00")
        if result:
            logger.warning(
                f"Alert 123 triggered: User {user.name} deposited {total_amount} "
                f"in 30s window (>200)"
            )
        return result

    @classmethod
    def evaluate_all_rules(
        cls, user: User, transaction_type: str, amount: Decimal, timestamp: int
    ) -> List[int]:
        """
        Evaluate all alert rules and return list of triggered alert codes.
        """
        logger.info(
            f"Evaluating alert rules for user {user.name}, {transaction_type} "
            f"{amount} at {timestamp}"
        )

        alert_codes = []

        # Rule 1100: Withdraw amount over 100
        if transaction_type == "withdraw" and cls.check_withdraw_over_100(user, amount):
            alert_codes.append(1100)

        # Rule 30: 3 consecutive withdraws
        if transaction_type == "withdraw" and cls.check_3_consecutive_withdraws(user, timestamp):
            alert_codes.append(30)

        # Rule 300: 3 consecutive increasing deposits
        if transaction_type == "deposit" and cls.check_3_consecutive_increasing_deposits(
            user, timestamp
        ):
            alert_codes.append(300)

        # Rule 123: Accumulative deposit amount over 200 in 30 seconds
        if transaction_type == "deposit" and cls.check_accumulative_deposit_over_200_in_30_seconds(
            user, timestamp
        ):
            alert_codes.append(123)

        logger.info(
            f"Alert evaluation complete for user {user.name}: "
            f"{len(alert_codes)} alerts triggered: {alert_codes}"
        )
        return alert_codes
