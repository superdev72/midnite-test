#!/usr/bin/env python
"""
Script to create test users for the Midnite API.
Run this after setting up the database.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'midnite_test.settings')
django.setup()

from events.models import User


def create_test_users():
    """Create test users for API testing."""
    print("Creating test users...")
    
    # Create test users
    test_users = [
        {"name": "John Doe", "email": "john@example.com"},
        {"name": "Jane Smith", "email": "jane@example.com"},
        {"name": "Bob Johnson", "email": "bob@example.com"},
        {"name": "Alice Brown", "email": "alice@example.com"},
    ]
    
    created_users = []
    for user_data in test_users:
        user, created = User.objects.get_or_create(
            email=user_data["email"],
            defaults={"name": user_data["name"]}
        )
        if created:
            print(f"✅ Created user: {user}")
            created_users.append(user)
        else:
            print(f"ℹ️  User already exists: {user}")
            created_users.append(user)
    
    print(f"\n📊 Summary:")
    print(f"Total users in database: {User.objects.count()}")
    print(f"Users created this run: {len([u for u in created_users if u.id <= len(test_users)])}")
    
    print(f"\n🔑 User IDs for API testing:")
    for user in created_users:
        print(f"  ID {user.id}: {user.name} ({user.email})")
    
    return created_users


if __name__ == "__main__":
    try:
        users = create_test_users()
        print("\n✅ Test users created successfully!")
        print("You can now run the API tests with these user IDs.")
    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        sys.exit(1)
