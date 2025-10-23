from django.db import models
from django.core.validators import EmailValidator


class User(models.Model):
    """
    Model to store user information.
    """

    name = models.CharField(max_length=100, help_text="User's full name")
    email = models.EmailField(
        unique=True, validators=[EmailValidator()], help_text="User's email address"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.email})"


class Event(models.Model):
    """
    Model to store user events (deposits/withdrawals) for monitoring and alerting.
    """

    TRANSACTION_TYPES = [
        ("deposit", "Deposit"),
        ("withdraw", "Withdraw"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="events",
        help_text="User who performed the transaction",
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES,
        help_text="Type of transaction: deposit or withdraw",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Transaction amount")
    timestamp = models.BigIntegerField(
        unique=True, help_text="Unix timestamp when the event occurred (from client)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["user", "transaction_type", "timestamp"]),
        ]

    def __str__(self):
        return (
            f"User {self.user.name} - {self.transaction_type} " f"{self.amount} at {self.timestamp}"
        )
