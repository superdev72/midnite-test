from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

from events.models import Event, User
from events.services import AlertRuleEngine


class UserModelTest(TestCase):
    """Test cases for User model."""

    def test_user_creation(self):
        """Test creating a user."""
        user = User.objects.create(name="John Doe", email="john@example.com")

        self.assertEqual(user.name, "John Doe")
        self.assertEqual(user.email, "john@example.com")
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)

    def test_user_str_representation(self):
        """Test string representation of User."""
        user = User.objects.create(name="Jane Doe", email="jane@example.com")

        expected = "Jane Doe (jane@example.com)"
        self.assertEqual(str(user), expected)


class EventModelTest(TestCase):
    """Test cases for Event model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(name="Test User", email="test@example.com")

    def test_event_creation(self):
        """Test creating an event."""
        event = Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("50.00"), timestamp=100
        )

        self.assertEqual(event.user, self.user)
        self.assertEqual(event.transaction_type, "deposit")
        self.assertEqual(event.amount, Decimal("50.00"))
        self.assertEqual(event.timestamp, 100)
        self.assertIsNotNone(event.created_at)

    def test_event_str_representation(self):
        """Test string representation of Event."""
        event = Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("25.00"), timestamp=200
        )

        expected = f"User {self.user.name} - withdraw 25.00 at 200"
        self.assertEqual(str(event), expected)


class AlertRuleEngineTest(TestCase):
    """Test cases for AlertRuleEngine."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(name="Test User", email="test@example.com")

    def test_withdraw_over_100(self):
        """Test rule 1100: withdraw amount over 100."""
        # Test amount over 100
        self.assertTrue(AlertRuleEngine.check_withdraw_over_100(self.user, Decimal("150.00")))

        # Test amount exactly 100
        self.assertFalse(AlertRuleEngine.check_withdraw_over_100(self.user, Decimal("100.00")))

        # Test amount under 100
        self.assertFalse(AlertRuleEngine.check_withdraw_over_100(self.user, Decimal("50.00")))

    def test_3_consecutive_withdraws(self):
        """Test rule 30: 3 consecutive withdraws."""
        # Create 3 consecutive withdraws
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("10.00"), timestamp=1
        )
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("20.00"), timestamp=2
        )
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("30.00"), timestamp=3
        )

        self.assertTrue(AlertRuleEngine.check_3_consecutive_withdraws(self.user, 3))

        # Test with only 2 withdraws
        Event.objects.all().delete()
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("10.00"), timestamp=1
        )
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("20.00"), timestamp=2
        )

        self.assertFalse(AlertRuleEngine.check_3_consecutive_withdraws(self.user, 2))

        # Test with mixed transaction types
        Event.objects.all().delete()
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("10.00"), timestamp=1
        )
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("20.00"), timestamp=2
        )
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("30.00"), timestamp=3
        )

        self.assertFalse(AlertRuleEngine.check_3_consecutive_withdraws(self.user, 3))

    def test_3_consecutive_increasing_deposits(self):
        """Test rule 300: 3 consecutive increasing deposits."""
        # Create 3 increasing deposits
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("10.00"), timestamp=1
        )
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("20.00"), timestamp=2
        )
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("30.00"), timestamp=3
        )

        self.assertTrue(AlertRuleEngine.check_3_consecutive_increasing_deposits(self.user, 3))

        # Test with non-increasing deposits
        Event.objects.all().delete()
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("30.00"), timestamp=1
        )
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("20.00"), timestamp=2
        )
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("10.00"), timestamp=3
        )

        self.assertFalse(AlertRuleEngine.check_3_consecutive_increasing_deposits(self.user, 3))

        # Test with mixed transaction types (should ignore withdraws)
        Event.objects.all().delete()
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("10.00"), timestamp=1
        )
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("20.00"), timestamp=2
        )
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("20.00"), timestamp=3
        )
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("30.00"), timestamp=4
        )

        self.assertTrue(AlertRuleEngine.check_3_consecutive_increasing_deposits(self.user, 4))

    def test_accumulative_deposit_over_200_in_30_seconds(self):
        """Test rule 123: accumulative deposit amount over 200 in 30 seconds."""
        # Create deposits totaling over 200 in 30-second window
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("100.00"), timestamp=50
        )
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("150.00"), timestamp=60
        )

        self.assertTrue(
            AlertRuleEngine.check_accumulative_deposit_over_200_in_30_seconds(self.user, 60)
        )

        # Test with deposits outside the window
        Event.objects.all().delete()
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("100.00"), timestamp=10
        )
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("150.00"), timestamp=60
        )

        self.assertFalse(
            AlertRuleEngine.check_accumulative_deposit_over_200_in_30_seconds(self.user, 60)
        )

        # Test with mixed transaction types (should only count deposits)
        Event.objects.all().delete()
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("100.00"), timestamp=50
        )
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("200.00"), timestamp=55
        )
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("150.00"), timestamp=60
        )

        self.assertTrue(
            AlertRuleEngine.check_accumulative_deposit_over_200_in_30_seconds(self.user, 60)
        )

    def test_evaluate_all_rules(self):
        """Test evaluating all rules together."""
        # Test withdraw over 100
        alert_codes = AlertRuleEngine.evaluate_all_rules(
            user=self.user, transaction_type="withdraw", amount=Decimal("150.00"), timestamp=1
        )
        self.assertIn(1100, alert_codes)

        # Test 3 consecutive withdraws - need to create 3 events first
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("10.00"), timestamp=1
        )
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("20.00"), timestamp=2
        )
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("30.00"), timestamp=3
        )

        # Now test with 4th consecutive withdraw
        alert_codes = AlertRuleEngine.evaluate_all_rules(
            user=self.user, transaction_type="withdraw", amount=Decimal("40.00"), timestamp=4
        )
        self.assertIn(30, alert_codes)


class EventAPITest(APITestCase):
    """Test cases for Event API endpoint."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create(name="API Test User", email="apitest@example.com")

    def test_valid_deposit_event(self):
        """Test valid deposit event."""
        data = {"type": "deposit", "amount": "42.00", "user_id": self.user.id, "t": 10}

        response = self.client.post("/event/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user_id"], self.user.id)
        self.assertIn("alert", response.data)
        self.assertIn("alert_codes", response.data)

        # Verify event was saved
        self.assertEqual(Event.objects.count(), 1)
        event = Event.objects.first()
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.transaction_type, "deposit")
        self.assertEqual(event.amount, Decimal("42.00"))
        self.assertEqual(event.timestamp, 10)

    def test_valid_withdraw_event(self):
        """Test valid withdraw event."""
        data = {"type": "withdraw", "amount": "25.50", "user_id": self.user.id, "t": 20}

        response = self.client.post("/event/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user_id"], self.user.id)
        self.assertFalse(response.data["alert"])  # No alerts triggered
        self.assertEqual(response.data["alert_codes"], [])

    def test_withdraw_over_100_alert(self):
        """Test withdraw over 100 triggers alert 1100."""
        data = {"type": "withdraw", "amount": "150.00", "user_id": self.user.id, "t": 10}

        response = self.client.post("/event/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["alert"])
        self.assertIn(1100, response.data["alert_codes"])

    def test_3_consecutive_withdraws_alert(self):
        """Test 3 consecutive withdraws triggers alert 30."""
        # First two withdraws
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("10.00"), timestamp=1
        )
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("20.00"), timestamp=2
        )

        # Third withdraw
        data = {"type": "withdraw", "amount": "30.00", "user_id": self.user.id, "t": 3}

        response = self.client.post("/event/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["alert"])
        self.assertIn(30, response.data["alert_codes"])

    def test_3_consecutive_increasing_deposits_alert(self):
        """Test 3 consecutive increasing deposits triggers alert 300."""
        # First two increasing deposits
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("10.00"), timestamp=1
        )
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("20.00"), timestamp=2
        )

        # Third increasing deposit
        data = {"type": "deposit", "amount": "30.00", "user_id": self.user.id, "t": 3}

        response = self.client.post("/event/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["alert"])
        self.assertIn(300, response.data["alert_codes"])

    def test_accumulative_deposit_over_200_alert(self):
        """Test accumulative deposit over 200 in 30 seconds triggers alert 123."""
        # First deposit
        Event.objects.create(
            user=self.user, transaction_type="deposit", amount=Decimal("100.00"), timestamp=50
        )

        # Second deposit within 30-second window
        data = {"type": "deposit", "amount": "150.00", "user_id": self.user.id, "t": 60}

        response = self.client.post("/event/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["alert"])
        self.assertIn(123, response.data["alert_codes"])

    def test_multiple_alerts(self):
        """Test multiple alerts triggered simultaneously."""
        # Create scenario that triggers multiple alerts
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("10.00"), timestamp=1
        )
        Event.objects.create(
            user=self.user, transaction_type="withdraw", amount=Decimal("20.00"), timestamp=2
        )

        data = {"type": "withdraw", "amount": "150.00", "user_id": self.user.id, "t": 3}  # Over 100

        response = self.client.post("/event/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["alert"])
        self.assertIn(1100, response.data["alert_codes"])  # Over 100
        self.assertIn(30, response.data["alert_codes"])  # 3 consecutive

    def test_invalid_payload(self):
        """Test invalid payload returns 400."""
        data = {"type": "invalid_type", "amount": "42.00", "user_id": self.user.id, "t": 10}

        response = self.client.post("/event/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_missing_fields(self):
        """Test missing required fields returns 400."""
        data = {
            "type": "deposit",
            "amount": "42.00",
            # Missing user_id and t
        }

        response = self.client.post("/event/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_negative_amount(self):
        """Test negative amount returns 400."""
        data = {"type": "deposit", "amount": "-42.00", "user_id": self.user.id, "t": 10}

        response = self.client.post("/event/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_zero_amount(self):
        """Test zero amount returns 400."""
        data = {"type": "deposit", "amount": "0.00", "user_id": self.user.id, "t": 10}

        response = self.client.post("/event/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_negative_user_id(self):
        """Test negative user_id returns 400."""
        data = {"type": "deposit", "amount": "42.00", "user_id": -1, "t": 10}

        response = self.client.post("/event/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_nonexistent_user_id(self):
        """Test nonexistent user_id returns 400."""
        data = {
            "type": "deposit",
            "amount": "42.00",
            "user_id": 99999,  # Non-existent user
            "t": 10,
        }

        response = self.client.post("/event/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_negative_timestamp(self):
        """Test negative timestamp returns 400."""
        data = {"type": "deposit", "amount": "42.00", "user_id": self.user.id, "t": -1}

        response = self.client.post("/event/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
