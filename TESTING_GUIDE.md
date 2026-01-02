# Quiz Application - Testing Guide

Complete guide for testing the quiz application using the automated test suite.

---

## Quick Start

```bash
# 1. Install test dependencies
pip install -r test_requirements.txt

# 2. Make sure the quiz server is running
# (In another terminal)
python main.py

# 3. Run all tests
python test_all_endpoints.py
```

---

## Installation

### Install Test Dependencies

```bash
pip install -r test_requirements.txt
```

Or install manually:
```bash
pip install requests websocket-client colorama
```

---

## Running Tests

### Basic Usage

```bash
# Run all tests against localhost
python test_all_endpoints.py
```

### Test Against Remote Server

```bash
# Test against VPS or remote server
python test_all_endpoints.py --url http://your-server-ip:8000
```

### Options

```bash
# Show detailed output
python test_all_endpoints.py --verbose

# Skip WebSocket tests
python test_all_endpoints.py --skip-websocket

# Combine options
python test_all_endpoints.py --url http://192.168.1.100:8000 --verbose
```

---

## Test Categories

The test suite includes **50+ tests** organized into 21 categories:

### 1. Server Health Check
- ✅ Server availability
- ✅ Server response

### 2. Authentication Tests
- ✅ Admin login
- ✅ Invalid login rejection
- ✅ Token generation

### 3. Team Management
- ✅ Create team
- ✅ List teams
- ✅ Update team
- ✅ Duplicate team code rejection

### 4. Session Management
- ✅ Create session
- ✅ List sessions
- ✅ Update session
- ✅ Get session details

### 5. User Management
- ✅ Create quiz master user
- ✅ Create presenter user

### 6. Admin Settings (Screen Sharing Feature)
- ✅ Get all settings
- ✅ Get display mode setting
- ✅ Update display mode
- ✅ Update FPS setting
- ✅ Update quality setting
- ✅ Non-existent setting handling

### 7. Quiz Master Operations
- ✅ Get live sessions
- ✅ Session selection

### 8. Slide Navigation
- ✅ Next slide
- ✅ Previous slide
- ✅ Jump to slide
- ✅ Reveal answer
- ✅ Auto-start quiz

### 9. Timer Tests
- ✅ Start timer
- ✅ Pause timer
- ✅ Reset timer

### 10. Buzzer Tests
- ✅ Unlock buzzers
- ✅ Lock buzzers
- ✅ Buzzer state management

### 11. Score Management
- ✅ Adjust score
- ✅ Undo score
- ✅ Score events

### 12. Display Tests
- ✅ Display snapshot
- ✅ Display data format

### 13. Team Session Assignment
- ✅ Assign teams to session
- ✅ Starting scores

### 14. Round Management
- ✅ Create rounds
- ✅ List rounds
- ✅ Round configuration

### 15. Advanced Settings
- ✅ FPS configuration
- ✅ Quality settings
- ✅ Mode switching

### 16. Authorization & Security
- ✅ Unauthorized access rejection
- ✅ Invalid token rejection
- ✅ Permission validation

### 17. Update Operations
- ✅ Session updates
- ✅ Team updates
- ✅ Data persistence

### 18. WebSocket Connections
- ✅ Display WebSocket
- ✅ Quiz Master WebSocket
- ✅ Presenter WebSocket
- ✅ Connection stability

### 19. API Quality
- ✅ Response format validation
- ✅ Response time testing
- ✅ JSON structure verification

### 20. Edge Cases & Error Handling
- ✅ Duplicate data rejection
- ✅ Empty request body validation
- ✅ Malformed data handling

### 21. Advanced Operations
- ✅ Score undo functionality
- ✅ Slide jump operations
- ✅ Complex workflows

---

## Understanding Test Output

### Test Status Indicators

```
[PASSED] Test Name
        Success message

[FAILED] Test Name
        Error message or reason

[SKIPPED] Test Name
        Reason for skipping
```

### Color Coding

- **🟢 GREEN**: Test passed
- **🔴 RED**: Test failed
- **🟡 YELLOW**: Test skipped

### Summary Report

At the end of test execution, you'll see:

```
================================================================================
TEST SUMMARY
================================================================================
Total Tests:   50
Passed:        48
Failed:        2
Skipped:       0

Failed Tests:
  - Test Name: Error description

Pass Rate: 96.0%
```

---

## Test Prerequisites

### 1. Server Must Be Running

Before running tests, ensure the quiz server is running:

```bash
# In a separate terminal
python main.py
```

The server should be accessible at `http://localhost:8000` (or your configured URL).

### 2. Database Must Be Initialized

Ensure the database has been initialized:

```bash
# Run database migration
python migrations/001_add_admin_settings.py
```

### 3. Admin User Must Exist

The test suite expects an admin user with credentials:
- **Username**: `admin`
- **Password**: `admin123`

Create this user if it doesn't exist or update credentials in the test file.

---

## Troubleshooting

### Server Not Running

**Error**: `Server Health Check FAILED`

**Solution**:
```bash
# Start the server in another terminal
python main.py

# Then run tests again
python test_all_endpoints.py
```

### WebSocket Tests Failing

**Error**: `websocket-client not installed`

**Solution**:
```bash
pip install websocket-client
```

Or skip WebSocket tests:
```bash
python test_all_endpoints.py --skip-websocket
```

### Connection Refused

**Error**: `Connection refused` or `Connection timeout`

**Solution**:
1. Check if server is running
2. Verify the URL is correct
3. Check firewall settings
4. Try with `--url http://127.0.0.1:8000` instead of `localhost`

### Authentication Failures

**Error**: `Admin Login FAILED`

**Solution**:
1. Verify admin user exists in database
2. Check credentials (default: admin/admin123)
3. Update test file with correct credentials if different

### Database Not Initialized

**Error**: `admin_settings table may not exist`

**Solution**:
```bash
# Run the migration
python migrations/001_add_admin_settings.py
```

---

## Test Environment Setup

### Local Testing

```bash
# 1. Ensure server is running locally
python main.py

# 2. Run tests
python test_all_endpoints.py
```

### VPS/Remote Testing

```bash
# Test against remote server
python test_all_endpoints.py --url http://your-vps-ip:8000
```

### CI/CD Integration

```bash
# In your CI/CD pipeline
pip install -r test_requirements.txt
python main.py &  # Start server in background
sleep 5           # Wait for server to start
python test_all_endpoints.py
```

---

## Interpreting Results

### All Tests Pass ✅

```
Pass Rate: 100%
✓ All tests passed! System is ready for deployment
```

**Action**: Safe to deploy to production

### Some Tests Fail ❌

```
Pass Rate: 85%
✗ Fix failed tests before deployment
```

**Action**:
1. Review failed tests in summary
2. Fix issues
3. Re-run tests
4. Do not deploy until all tests pass

### High Skip Rate ⚠️

```
Skipped: 15
```

**Action**:
1. Install missing dependencies (e.g., websocket-client)
2. Ensure prerequisites are met
3. Re-run tests

---

## Advanced Usage

### Running Specific Test Categories

To run only specific tests, modify the `test_all_endpoints.py` file and comment out unwanted test sections in the `run_all_tests()` method.

### Adding Custom Tests

Add new test methods to the `QuizTester` class:

```python
def test_my_custom_endpoint(self):
    """Test my custom endpoint"""
    success, response = self.make_request(
        "GET",
        "/my/endpoint",
        token=self.admin_token
    )

    msg = "Custom test passed" if success else "Failed"
    self.results.add_result("My Custom Test", success, msg)
    return success
```

Then call it in `run_all_tests()`:

```python
self.print_section("MY CUSTOM TESTS")
self.test_my_custom_endpoint()
```

---

## Performance Benchmarks

Expected performance metrics:

- **Response Time**: < 1000ms per request
- **Test Suite Execution**: 30-60 seconds (all tests)
- **Server Memory**: < 500MB during testing
- **Pass Rate**: Should be 100% on healthy system

---

## Test Coverage

The test suite covers:

- ✅ **100% of REST API endpoints**
- ✅ **WebSocket connections** (all roles)
- ✅ **Authentication & Authorization**
- ✅ **Database operations** (CRUD)
- ✅ **Error handling**
- ✅ **Edge cases**
- ✅ **Security** (unauthorized access)
- ✅ **Screen sharing feature** (all endpoints)

---

## Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r test_requirements.txt
      - name: Start server
        run: python main.py &
      - name: Wait for server
        run: sleep 5
      - name: Run tests
        run: python test_all_endpoints.py
```

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review test output for specific error messages
3. Verify all prerequisites are met
4. Check server logs for backend errors

---

**Last Updated**: 2026-01-02
**Version**: 1.0
**Test Suite**: 50+ comprehensive tests
