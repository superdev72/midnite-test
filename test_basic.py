#!/usr/bin/env python
"""
Simple functionality test script.
Run this after starting the Django server.
"""

import os
import sys
import time
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "midnite_test.settings")
django.setup()

# Django imports must be after setup
from events.models import Event, User  # noqa: E402
from events.services import AlertRuleEngine  # noqa: E402


def test_basic_functionality():
    """Test basic functionality without complex setup."""
    print("🧪 Testing basic functionality...")

    # Test 1: User model creation
    print("Test 1: User model creation")
    try:
        user = User(name="Test User", email="test@example.com")
        print(f"✅ User created: {user}")
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        return False

    # Test 2: Event model creation
    print("Test 2: Event model creation")
    try:
        current_timestamp = int(time.time())
        event = Event(
            user=user,
            transaction_type="deposit",
            amount=Decimal("50.00"),
            timestamp=current_timestamp,
        )
        print(f"✅ Event created: {event}")
    except Exception as e:
        print(f"❌ Event creation failed: {e}")
        return False

    # Test 3: Alert rule engine
    print("Test 3: Alert rule engine")
    try:
        # Test withdraw over 100
        result = AlertRuleEngine.check_withdraw_over_100(user, Decimal("150.00"))
        print(f"✅ Withdraw over 100 test: {result}")

        # Test normal amount
        result = AlertRuleEngine.check_withdraw_over_100(user, Decimal("50.00"))
        print(f"✅ Normal amount test: {result}")

    except Exception as e:
        print(f"❌ Alert rule engine test failed: {e}")
        return False

    print("✅ All basic functionality tests passed!")
    return True


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
