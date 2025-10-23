# Midnite Test - Backend Developer Home Test

This project implements a Django REST API endpoint for monitoring user events and triggering alerts based on specific rules.

## Overview

The `/event` endpoint receives user transaction events (deposits/withdrawals) and evaluates them against predefined alert rules to detect unusual activity patterns.

## Features

- **Event Processing**: Accepts deposit and withdrawal events with validation
- **Alert Rules**: Implements 4 specific alert rules:
  - **Code 1100**: Withdraw amount over 100
  - **Code 30**: 3 consecutive withdraws
  - **Code 300**: 3 consecutive increasing deposits (ignoring withdraws)
  - **Code 123**: Accumulative deposit amount over 200 in a 30-second window
- **Database**: PostgreSQL with optimized indexes for efficient querying
- **Testing**: Comprehensive test suite using pytest
- **Docker**: Full containerization with Docker Compose
- **Code Quality**: Black formatting, Flake8 linting, and comprehensive logging
- **Environment Configuration**: Secure environment variable management

## Project Structure

```
midnite_test/
├── events/                    # Main Django app
│   ├── models.py             # User and Event models
│   ├── views.py              # API endpoint
│   ├── serializers.py        # Data validation
│   ├── services.py           # Alert rule engine
│   ├── urls.py               # URL routing
│   ├── admin.py              # Django admin interface
│   └── test_events.py        # Comprehensive test cases
├── midnite_test/             # Django project settings
│   ├── settings.py           # Configuration
│   └── urls.py               # Main URL routing
├── docker-compose.yml        # Docker services
├── Dockerfile                # Django container
├── requirements.txt          # Python dependencies
├── pytest.ini               # Test configuration
├── .flake8                  # Linting configuration
├── pyproject.toml            # Black formatting configuration
├── env.example               # Environment variables template
├── check_code.sh            # Code quality script
├── create_test_users.py     # User creation script
├── test_basic.py            # Basic functionality test
└── manage.py                 # Django management
```

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- PostgreSQL (if running locally)

## 🚀 Quick Start Guide

### **Prerequisites**

- Docker and Docker Compose installed
- Git (optional, for cloning)

### **Step 1: Get the Project**

```bash
# If cloning from git
git clone <repository-url>
cd midnite-test

# Or if you already have the project files
cd midnite-test
```

### **Step 2: Configure Environment Variables**

```bash
# Copy the example environment file
cp env.example .env

# Edit the .env file if you want to customize settings (optional)
# The default values work fine for development
```

**What this does:**

- Creates a `.env` file with environment variables for Docker Compose
- Docker Compose automatically reads these variables
- You can customize database credentials, debug mode, etc. if needed

### **Step 3: Start the Application**

```bash
# Start all services (Django + PostgreSQL)
docker compose up -d

# Check if services are running
docker compose ps
```

### **Step 4: Set Up Database**

```bash
# Apply database migrations
docker compose exec web python manage.py migrate

# Create a superuser for admin access (optional)
docker compose exec web python manage.py createsuperuser
```

### **Step 5: Create Test Users**

```bash
# Create test users for API testing
docker compose exec web python create_test_users.py
```

**Expected Output:**

```
Creating test users...
✅ Created user: John Doe (john@example.com)
✅ Created user: Jane Smith (jane@example.com)
✅ Created user: Bob Johnson (bob@example.com)
✅ Created user: Alice Brown (alice@example.com)

📊 Summary:
Total users in database: 4
Users created this run: 4

🔑 User IDs for API testing:
  ID 1: John Doe (john@example.com)
  ID 2: Jane Smith (jane@example.com)
  ID 3: Bob Johnson (bob@example.com)
  ID 4: Alice Brown (alice@example.com)

✅ Test users created successfully!
```

### **Step 6: Test the API**

**Basic Test:**

```bash
curl -XPOST http://localhost:8000/event/ \
-H 'Content-Type: application/json' \
-d '{"type": "deposit", "amount": "42.00", "user_id": 1, "t": 0}'
```

**Expected Response:**

```json
{ "alert": false, "alert_codes": [], "user_id": 1 }
```

**Error Response (Duplicate Timestamp):**

```json
{
  "error": "Duplicate timestamp",
  "message": "An event with timestamp 1000 already exists",
  "user_id": 1
}
```

**Status Code:** `409 Conflict`

**Error Response (Invalid Timestamp Ordering):**

```json
{
  "error": "Invalid payload",
  "details": {
    "t": [
      "Timestamp 1000 must be greater than the latest timestamp 1761206472304617 in the system"
    ]
  }
}
```

**Status Code:** `400 Bad Request`

**Important Note about Timestamps:**

- The `t` field in the request payload contains the **current Unix timestamp** when the API is accessed
- This timestamp is stored directly in the database as the `timestamp` field
- Timestamps must be **globally unique and strictly increasing** across all users
- Uses `BigIntegerField` with `unique=True` constraint to support microsecond precision timestamps
- **Database-level protection**: Duplicate timestamps are prevented by unique constraint
- **Global validation**: Each timestamp must be greater than the latest timestamp in the entire system
- **Error handling**: Returns HTTP 409 Conflict for duplicate timestamps, HTTP 400 for invalid ordering

**Test Alert Rules:**

```bash
# Test withdraw over 100 (Alert 1100)
curl -XPOST http://localhost:8000/event/ \
-H 'Content-Type: application/json' \
-d '{"type": "withdraw", "amount": "150.00", "user_id": 1, "t": 1}'

# Expected: {"alert": true, "alert_codes": [1100], "user_id": 1}

# Test timestamp validation (should fail with decreasing timestamp)
curl -XPOST http://localhost:8000/event/ \
-H 'Content-Type: application/json' \
-d '{"type": "deposit", "amount": "50.00", "user_id": 1, "t": 0}'

# Expected: {"error": "Invalid payload", "details": {"t": ["Timestamp 0 must be greater than the latest timestamp X in the system"]}}
```

### **Step 7: Access Admin Panel (Optional)**

```bash
# Open browser and go to:
http://localhost:8000/admin/

# Login with superuser credentials created in Step 4
```

### **Step 8: Run Tests**

```bash
# Run comprehensive pytest tests (24 test cases)
docker compose exec web python -m pytest events/test_events.py -v

# Run basic functionality test
docker compose exec web python test_basic.py

# Run all code quality checks and tests
docker compose exec web ./check_code.sh
```

### **Step 9: View Logs**

```bash
# View application logs
docker compose logs web

# Follow logs in real-time
docker compose logs -f web
```

### **🛑 Stop the Application**

```bash
# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes data)
docker compose down -v
```

## 🧪 Comprehensive API Testing

### **Test All Alert Rules**

**1. Withdraw Over 100 (Alert 1100):**

```bash
curl -XPOST http://localhost:8000/event/ \
-H 'Content-Type: application/json' \
-d '{"type": "withdraw", "amount": "150.00", "user_id": 1, "t": 1}'
# Expected: {"alert": true, "alert_codes": [1100], "user_id": 1}
```

**2. Three Consecutive Withdraws (Alert 30):**

```bash
# First withdraw
curl -XPOST http://localhost:8000/event/ \
-H 'Content-Type: application/json' \
-d '{"type": "withdraw", "amount": "10.00", "user_id": 2, "t": 1}'

# Second withdraw
curl -XPOST http://localhost:8000/event/ \
-H 'Content-Type: application/json' \
-d '{"type": "withdraw", "amount": "20.00", "user_id": 2, "t": 2}'

# Third withdraw (triggers alert)
curl -XPOST http://localhost:8000/event/ \
-H 'Content-Type: application/json' \
-d '{"type": "withdraw", "amount": "30.00", "user_id": 2, "t": 3}'
# Expected: {"alert": true, "alert_codes": [30], "user_id": 2}
```

**3. Three Consecutive Increasing Deposits (Alert 300):**

```bash
# First deposit
curl -XPOST http://localhost:8000/event/ \
-H 'Content-Type: application/json' \
-d '{"type": "deposit", "amount": "10.00", "user_id": 3, "t": 1}'

# Second deposit
curl -XPOST http://localhost:8000/event/ \
-H 'Content-Type: application/json' \
-d '{"type": "deposit", "amount": "20.00", "user_id": 3, "t": 2}'

# Third deposit (triggers alert)
curl -XPOST http://localhost:8000/event/ \
-H 'Content-Type: application/json' \
-d '{"type": "deposit", "amount": "30.00", "user_id": 3, "t": 3}'
# Expected: {"alert": true, "alert_codes": [300], "user_id": 3}
```

**4. Accumulative Deposits Over 200 in 30s (Alert 123):**

```bash
# First deposit
curl -XPOST http://localhost:8000/event/ \
-H 'Content-Type: application/json' \
-d '{"type": "deposit", "amount": "100.00", "user_id": 4, "t": 50}'

# Second deposit within 30s window (triggers alert)
curl -XPOST http://localhost:8000/event/ \
-H 'Content-Type: application/json' \
-d '{"type": "deposit", "amount": "150.00", "user_id": 4, "t": 60}'
# Expected: {"alert": true, "alert_codes": [123], "user_id": 4}
```

### **Test Error Cases**

**Invalid Transaction Type:**

```bash
curl -XPOST http://localhost:8000/event/ \
-H 'Content-Type: application/json' \
-d '{"type": "invalid", "amount": "42.00", "user_id": 1, "t": 0}'
# Expected: 400 Bad Request
```

**Negative Amount:**

```bash
curl -XPOST http://localhost:8000/event/ \
-H 'Content-Type: application/json' \
-d '{"type": "deposit", "amount": "-42.00", "user_id": 1, "t": 0}'
# Expected: 400 Bad Request
```

**Non-existent User:**

```bash
curl -XPOST http://localhost:8000/event/ \
-H 'Content-Type: application/json' \
-d '{"type": "deposit", "amount": "42.00", "user_id": 99999, "t": 0}'
# Expected: 400 Bad Request
```

### **Using Postman**

**Request Configuration:**

- **Method:** `POST`
- **URL:** `http://localhost:8000/event/`
- **Headers:** `Content-Type: application/json`
- **Body (raw JSON):**

```json
{
  "type": "deposit",
  "amount": "42.00",
  "user_id": 1,
  "t": 0
}
```

**Expected Response:**

```json
{
  "alert": false,
  "alert_codes": [],
  "user_id": 1
}
```

## Local Development Setup

1. **Create and activate virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**:

   ```bash
   # Create database
   createdb midnite_test

   # Update settings.py with your database credentials if needed
   ```

4. **Run migrations**:

   ```bash
   python manage.py migrate
   ```

5. **Start development server**:
   ```bash
   python manage.py runserver
   ```

## API Usage

### Endpoint: `POST /event`

**Request Payload**:

```json
{
  "type": "deposit",
  "amount": "42.00",
  "user_id": 1,
  "t": 10
}
```

**Response**:

```json
{
  "alert": true,
  "alert_codes": [30, 123],
  "user_id": 1
}
```

### Field Descriptions

- `type`: Transaction type - either "deposit" or "withdraw"
- `amount`: Transaction amount as decimal string (must be positive)
- `user_id`: Unique user identifier (positive integer)
- `t`: Timestamp in seconds (non-negative integer, always increasing)

### Alert Rules

| Code | Description             | Trigger Condition                  |
| ---- | ----------------------- | ---------------------------------- |
| 1100 | High withdrawal         | Withdraw amount > 100              |
| 30   | Consecutive withdrawals | 3 consecutive withdraws            |
| 300  | Increasing deposits     | 3 consecutive increasing deposits  |
| 123  | High deposit volume     | Deposits > 200 in 30-second window |

## User Management

The API requires users to exist in the database before processing events.

### **Creating Users**

**Via Django Admin:**

1. Access admin panel: `http://127.0.0.1:8000/admin/`
2. Create superuser: `python manage.py createsuperuser`
3. Add users through the admin interface

**Via Script:**

```bash
python create_test_users.py
```

**Via Django Shell:**

```python
from events.models import User
user = User.objects.create(name="John Doe", email="john@example.com")
```

### **User Requirements**

- **Name**: User's full name (max 100 characters)
- **Email**: Unique email address (validated format)
- **ID**: Auto-generated primary key used in API calls

## Code Quality

The project includes comprehensive code quality tools:

### **Black Code Formatter**

```bash
# Format all Python files
black events/ midnite_test/ test_basic.py
```

### **Flake8 Linting**

```bash
# Check code quality
flake8 events/ midnite_test/ test_basic.py
```

### **Automated Quality Checks**

```bash
# Run all quality checks and tests
./check_code.sh
```

## Environment Configuration

The project uses `python-decouple` for secure environment variable management with Docker Compose integration.

### **Environment Variables Setup**

**Step 1: Create Environment File**

```bash
# Copy the example environment file
cp env.example .env
```

**Step 2: Customize Settings (Optional)**

Edit `.env` file to customize your settings:

```bash
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here

# Database Settings (for Docker Compose)
POSTGRES_DB=midnite_test
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password-here
POSTGRES_PORT=5433

# Logging Level
LOG_LEVEL=INFO
```

**Step 3: Docker Compose Integration**

Docker Compose automatically:

- Reads variables from `.env` file
- Uses fallback defaults if variables are missing
- Sets `POSTGRES_HOST=db` automatically for container communication

### **Available Variables**

- `DEBUG`: Enable/disable debug mode (default: True)
- `SECRET_KEY`: Django secret key (default: provided insecure key)
- `POSTGRES_DB`: Database name (default: midnite_test)
- `POSTGRES_USER`: Database user (default: postgres)
- `POSTGRES_PASSWORD`: Database password (default: postgres)
- `POSTGRES_PORT`: Database port (default: 5433)
- `LOG_LEVEL`: Logging level (default: INFO)

### **Port Configuration**

**Default Ports:**

- **Django Web Server**: `8000` (http://localhost:8000)
- **PostgreSQL Database**: `5433` (changed from 5432 to avoid conflicts)

**Changing Ports:**

If you need to change ports due to conflicts:

**1. Change Database Port:**

```bash
# Edit .env file
POSTGRES_PORT=5434  # Use any available port
```

**2. Change Web Server Port:**

```yaml
# Edit docker-compose.yml
services:
  web:
    ports:
      - "8001:8000" # Change 8001 to any available port
```

**3. Restart Services:**

```bash
docker compose down
docker compose up -d
```

**Common Port Conflicts:**

- **Port 5432**: Often used by local PostgreSQL installations
- **Port 8000**: Sometimes used by other web services
- **Solution**: Use ports 5433+ for database, 8001+ for web server

## Logging

Comprehensive logging is implemented throughout the application:

### **Log Levels**

- **DEBUG**: Detailed rule evaluation and database operations
- **INFO**: Event processing and alert triggers
- **WARNING**: Alert rule violations
- **ERROR**: System errors and validation failures

### **Log Files**

- `logs/django.log`: General Django application logs
- `logs/events.log`: Event processing and alert logs

### **Log Format**

- **Console**: Human-readable format
- **Files**: JSON format for easy parsing and analysis

## Testing

### Run Tests with Docker

```bash
docker compose exec web pytest
```

### Run Tests Locally

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests (24 tests total)
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest events/test_events.py

# Run basic functionality test
pytest test_basic.py

# Run with coverage
pytest --cov=events
```

### Test Categories

- **Model Tests**: Event model creation and validation
- **Service Tests**: Alert rule engine logic
- **API Tests**: Endpoint functionality and error handling
- **Integration Tests**: End-to-end scenarios

## Database Schema

### User Model

```python
class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Event Model

```python
class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    transaction_type = models.CharField(max_length=10)  # 'deposit' or 'withdraw'
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.BigIntegerField(unique=True)  # Client-provided timestamp (Unix time)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Indexes**:

- `(user, timestamp)` - For efficient user event queries
- `(user, transaction_type, timestamp)` - For rule-specific queries
- `(email)` - For user lookup by email

## Performance Considerations

- **Database Indexes**: Optimized for common query patterns
- **Atomic Transactions**: Ensures data consistency during rule evaluation
- **Efficient Queries**: Uses database-level filtering and ordering
- **Minimal Data Transfer**: Only stores necessary event data

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Successful event processing
- `400 Bad Request`: Invalid payload or validation errors
- `500 Internal Server Error`: Server-side errors

## Development Notes

### Testing Framework

The project uses **pytest** for comprehensive testing with **24 test cases** covering:

- **Model Tests**: User and Event model creation and validation
- **Service Tests**: All alert rule engine methods
- **API Tests**: Complete endpoint testing with various scenarios
- **Error Handling**: Invalid payloads, missing fields, edge cases

**Test Structure:**

- `events/test_events.py` - Comprehensive pytest test suite (23 tests)
- `test_basic.py` - Quick functionality verification (1 test)
- `check_code.sh` - Automated quality checks and testing

### Alert Rule Implementation

The alert rules are implemented in `events/services.py` using the `AlertRuleEngine` class:

1. **Rule 1100**: Simple amount comparison for withdrawals
2. **Rule 30**: Queries last 3 events and checks if all are withdrawals
3. **Rule 300**: Filters deposits only and checks for increasing amounts
4. **Rule 123**: Calculates sum of deposits within time window

### Database Optimization

- Uses PostgreSQL-specific features for better performance
- Implements composite indexes for common query patterns
- Leverages database-level ordering and filtering

### Testing Strategy

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Edge Cases**: Boundary conditions and error scenarios
- **Performance Tests**: Database query optimization validation

## Troubleshooting

### Common Issues

1. **Database Connection Error**:

   - Ensure PostgreSQL is running
   - Check database credentials in settings
   - Verify database exists

2. **Docker Issues**:

   - Run `docker compose down` and `docker compose up --build`
   - Check if ports 8000 and 5432 are available

3. **Migration Errors**:

   - Run `python manage.py makemigrations` first
   - Then `python manage.py migrate`

4. **Environment Variable Issues**:

   - **Missing .env file**: Run `cp env.example .env`
   - **Wrong database host**: Ensure `POSTGRES_HOST=db` in Docker (set automatically)
   - **Permission errors**: Check file permissions on `.env` file
   - **Variable not loading**: Restart Docker containers after changing `.env`

5. **Port Conflicts**:

   - **Port 8000 in use**: Change port in `docker-compose.yml` or stop conflicting service
   - **Port 5433 in use**: Change `POSTGRES_PORT` in `.env` file to another port (e.g., 5434)
   - **Port 5432 already used locally**: The default is now 5433 to avoid conflicts

### Debug Mode

Set `DEBUG=True` in settings for detailed error messages during development.

## Production Considerations

- Change `SECRET_KEY` to a secure random value
- Set `DEBUG=False`
- Configure proper database credentials
- Use environment variables for sensitive data
- Implement proper logging and monitoring
- Consider rate limiting for the API endpoint

## License

This project is created for the Midnite backend developer home test.
