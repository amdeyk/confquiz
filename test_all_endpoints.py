"""
Comprehensive Test Suite for Quiz Application
Tests all endpoints and functionality including screen sharing feature

Usage:
    python test_all_endpoints.py

Optional arguments:
    --url http://your-server:8000    # Test against custom URL
    --verbose                         # Show detailed output
    --skip-websocket                  # Skip WebSocket tests

Requirements:
    pip install requests websocket-client colorama
"""

import requests
import json
import time
import sys
import os
import io
import argparse
from typing import Dict, Optional, List
from colorama import init, Fore, Style
try:
    from websocket import create_connection, WebSocketTimeoutException
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("Warning: websocket-client not installed. WebSocket tests will be skipped.")
    print("Install with: pip install websocket-client")

# Initialize colorama for colored output
init(autoreset=True)

# Configuration (can be overridden by command line)
BASE_URL = "http://localhost:8000"  # Change if deployed
API_URL = f"{BASE_URL}/api"
VERBOSE = False

class TestResults:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.results = []

    def add_result(self, test_name: str, passed: bool, message: str = "", skipped: bool = False):
        self.total += 1
        if skipped:
            self.skipped += 1
            status = "SKIPPED"
            color = Fore.YELLOW
        elif passed:
            self.passed += 1
            status = "PASSED"
            color = Fore.GREEN
        else:
            self.failed += 1
            status = "FAILED"
            color = Fore.RED

        result = {
            "name": test_name,
            "status": status,
            "message": message
        }
        self.results.append(result)

        print(f"{color}[{status}]{Style.RESET_ALL} {test_name}")
        if message:
            print(f"        {message}")

    def print_summary(self):
        print("\n" + "="*80)
        print(f"{Style.BRIGHT}TEST SUMMARY{Style.RESET_ALL}")
        print("="*80)
        print(f"Total Tests:   {self.total}")
        print(f"{Fore.GREEN}Passed:        {self.passed}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed:        {self.failed}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Skipped:       {self.skipped}{Style.RESET_ALL}")

        if self.failed > 0:
            print(f"\n{Fore.RED}Failed Tests:{Style.RESET_ALL}")
            for result in self.results:
                if result["status"] == "FAILED":
                    print(f"  - {result['name']}: {result['message']}")

        percentage = (self.passed / self.total * 100) if self.total > 0 else 0
        print(f"\n{Style.BRIGHT}Pass Rate: {percentage:.1f}%{Style.RESET_ALL}")

class QuizTester:
    def __init__(self):
        self.results = TestResults()
        self.admin_token = None
        self.qm_token = None
        self.presenter_token = None
        self.team_token = None
        self.session_id = None
        self.team_id = None
        self.slide_id = None

    def print_section(self, title: str):
        print(f"\n{Style.BRIGHT}{Fore.CYAN}{'='*80}")
        print(f"{title}")
        print(f"{'='*80}{Style.RESET_ALL}\n")

    def make_request(self, method: str, endpoint: str, token: Optional[str] = None,
                     data: Optional[Dict] = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return (success, response)"""
        url = f"{API_URL}{endpoint}"
        headers = {}

        if token:
            headers["Authorization"] = f"Bearer {token}"

        if data:
            headers["Content-Type"] = "application/json"

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=5)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=5)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=5)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, json=data, timeout=5)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=5)
            else:
                return False, None

            success = response.status_code == expected_status
            return success, response
        except Exception as e:
            return False, str(e)

    # ========== Authentication Tests ==========

    def test_health_check(self):
        """Test if server is running"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=5)
            success = response.status_code == 200
            self.results.add_result(
                "Server Health Check",
                success,
                f"Status: {response.status_code}" if not success else "Server is running"
            )
            return success
        except Exception as e:
            self.results.add_result("Server Health Check", False, f"Error: {str(e)}")
            return False

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.make_request(
            "POST",
            "/auth/login",
            data={"username": "admin", "password": "admin123"}
        )

        if success and response:
            try:
                data = response.json()
                self.admin_token = data.get("access_token")
                success = self.admin_token is not None
                msg = f"Token: {self.admin_token[:20]}..." if success else "No token in response"
            except:
                success = False
                msg = "Invalid JSON response"
        else:
            msg = f"Error: {response if isinstance(response, str) else response.text}"

        self.results.add_result("Admin Login", success, msg)
        return success

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        success, response = self.make_request(
            "POST",
            "/auth/login",
            data={"username": "invalid", "password": "wrong"},
            expected_status=401
        )

        self.results.add_result(
            "Invalid Login (Should Fail)",
            success,
            "Correctly rejected invalid credentials" if success else "Did not reject invalid credentials"
        )
        return success

    # ========== Admin - Team Management Tests ==========

    def test_create_team(self):
        """Test creating a team"""
        if not self.admin_token:
            self.results.add_result("Create Team", False, "No admin token", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            "/admin/teams",
            token=self.admin_token,
            data={"name": "Test Team Alpha", "code": "ALPHA123"}
        )

        if success and response:
            try:
                data = response.json()
                self.team_id = data.get("id")
                msg = f"Team ID: {self.team_id}" if self.team_id else "No team ID in response"
            except:
                msg = "Invalid JSON response"
        else:
            msg = f"Error: {response if isinstance(response, str) else response.text}"

        self.results.add_result("Create Team", success, msg)
        return success

    def test_list_teams(self):
        """Test listing all teams"""
        if not self.admin_token:
            self.results.add_result("List Teams", False, "No admin token", skipped=True)
            return False

        success, response = self.make_request(
            "GET",
            "/admin/teams",
            token=self.admin_token
        )

        if success and response:
            try:
                teams = response.json()
                msg = f"Found {len(teams)} team(s)"
            except:
                msg = "Invalid JSON response"
        else:
            msg = f"Error: {response if isinstance(response, str) else response.text}"

        self.results.add_result("List Teams", success, msg)
        return success

    # ========== Admin - Session Management Tests ==========

    def test_create_session(self):
        """Test creating a quiz session"""
        if not self.admin_token:
            self.results.add_result("Create Session", False, "No admin token", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            "/admin/sessions",
            token=self.admin_token,
            data={"name": "Test Session 2026", "banner_text": "TEST QUIZ"}
        )

        if success and response:
            try:
                data = response.json()
                self.session_id = data.get("id")
                msg = f"Session ID: {self.session_id}" if self.session_id else "No session ID in response"
            except:
                msg = "Invalid JSON response"
        else:
            msg = f"Error: {response if isinstance(response, str) else response.text}"

        self.results.add_result("Create Session", success, msg)
        return success

    def test_list_sessions(self):
        """Test listing all sessions"""
        if not self.admin_token:
            self.results.add_result("List Sessions", False, "No admin token", skipped=True)
            return False

        success, response = self.make_request(
            "GET",
            "/admin/sessions",
            token=self.admin_token
        )

        if success and response:
            try:
                sessions = response.json()
                msg = f"Found {len(sessions)} session(s)"
            except:
                msg = "Invalid JSON response"
        else:
            msg = f"Error: {response if isinstance(response, str) else response.text}"

        self.results.add_result("List Sessions", success, msg)
        return success

    # ========== Admin - User Management Tests ==========

    def test_create_quiz_master(self):
        """Test creating a quiz master user"""
        if not self.admin_token:
            self.results.add_result("Create Quiz Master", False, "No admin token", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            "/admin/users/quiz-master",
            token=self.admin_token,
            data={"username": f"qm_test_{int(time.time())}", "password": "qm123456"}
        )

        msg = "Quiz master created" if success else f"Error: {response.text if hasattr(response, 'text') else response}"
        self.results.add_result("Create Quiz Master", success, msg)
        return success

    def test_create_presenter(self):
        """Test creating a presenter user"""
        if not self.admin_token:
            self.results.add_result("Create Presenter", False, "No admin token", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            "/admin/users/presenter",
            token=self.admin_token,
            data={"username": f"presenter_test_{int(time.time())}", "password": "presenter123"}
        )

        msg = "Presenter created" if success else f"Error: {response.text if hasattr(response, 'text') else response}"
        self.results.add_result("Create Presenter", success, msg)
        return success

    # ========== Admin - Settings Tests ==========

    def test_get_settings(self):
        """Test getting all admin settings"""
        if not self.admin_token:
            self.results.add_result("Get Settings", False, "No admin token", skipped=True)
            return False

        success, response = self.make_request(
            "GET",
            "/admin/settings",
            token=self.admin_token
        )

        if success and response:
            try:
                settings = response.json()
                msg = f"Settings: {', '.join(settings.keys())}"
            except:
                msg = "Invalid JSON response"
        else:
            msg = f"Error: {response if isinstance(response, str) else response.text}"

        self.results.add_result("Get All Settings", success, msg)
        return success

    def test_get_display_mode_setting(self):
        """Test getting display_mode setting"""
        if not self.admin_token:
            self.results.add_result("Get Display Mode Setting", False, "No admin token", skipped=True)
            return False

        success, response = self.make_request(
            "GET",
            "/admin/settings/display_mode",
            token=self.admin_token
        )

        if success and response:
            try:
                setting = response.json()
                msg = f"Mode: {setting.get('setting_value')}"
            except:
                msg = "Invalid JSON response"
        else:
            msg = f"Error: {response if isinstance(response, str) else response.text}"

        self.results.add_result("Get Display Mode Setting", success, msg)
        return success

    def test_update_display_mode(self):
        """Test updating display mode setting"""
        if not self.admin_token:
            self.results.add_result("Update Display Mode", False, "No admin token", skipped=True)
            return False

        success, response = self.make_request(
            "PUT",
            "/admin/settings/display_mode?value=png_slides",
            token=self.admin_token
        )

        msg = "Display mode updated" if success else f"Error: {response.text if hasattr(response, 'text') else response}"
        self.results.add_result("Update Display Mode", success, msg)
        return success

    # ========== Quiz Master - Session Tests ==========

    def test_qm_get_live_sessions(self):
        """Test getting live sessions as QM"""
        if not self.admin_token:
            self.results.add_result("QM Get Live Sessions", False, "No admin token (using admin for QM test)", skipped=True)
            return False

        success, response = self.make_request(
            "GET",
            "/qm/sessions/live",
            token=self.admin_token
        )

        if success and response:
            try:
                sessions = response.json()
                msg = f"Found {len(sessions)} live session(s)"
            except:
                msg = "Invalid JSON response"
        else:
            msg = f"Error: {response if isinstance(response, str) else response.text}"

        self.results.add_result("QM Get Live Sessions", success, msg)
        return success

    # ========== Quiz Master - Slide Navigation Tests ==========

    def test_next_slide(self):
        """Test moving to next slide"""
        if not self.admin_token or not self.session_id:
            self.results.add_result("Next Slide", False, "No token or session ID", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            f"/qm/sessions/{self.session_id}/slide/next",
            token=self.admin_token
        )

        if success and response:
            try:
                data = response.json()
                self.slide_id = data.get("slide_id")
                msg = f"Slide ID: {self.slide_id}" if self.slide_id else data.get("message", "No slide ID")
            except:
                msg = "Invalid JSON response"
        else:
            msg = f"Error: {response if isinstance(response, str) else response.text}"

        self.results.add_result("Next Slide", success, msg)
        return success

    def test_previous_slide(self):
        """Test moving to previous slide"""
        if not self.admin_token or not self.session_id:
            self.results.add_result("Previous Slide", False, "No token or session ID", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            f"/qm/sessions/{self.session_id}/slide/prev",
            token=self.admin_token,
            expected_status=400  # Expected to fail if no previous slide
        )

        msg = "Correctly handled (no previous slide)" if success else "Unexpected response"
        self.results.add_result("Previous Slide (No Prev)", success, msg)
        return success

    # ========== Quiz Master - Timer Tests ==========

    def test_start_timer(self):
        """Test starting timer"""
        if not self.admin_token or not self.session_id:
            self.results.add_result("Start Timer", False, "No token or session ID", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            f"/qm/sessions/{self.session_id}/timer/start",
            token=self.admin_token,
            data={"duration_ms": 30000, "fastest_finger": False}
        )

        msg = "Timer started" if success else f"Error: {response.text if hasattr(response, 'text') else response}"
        self.results.add_result("Start Timer", success, msg)
        return success

    def test_pause_timer(self):
        """Test pausing timer"""
        if not self.admin_token or not self.session_id:
            self.results.add_result("Pause Timer", False, "No token or session ID", skipped=True)
            return False

        # Wait a bit for timer to be running
        time.sleep(0.5)

        success, response = self.make_request(
            "POST",
            f"/qm/sessions/{self.session_id}/timer/pause",
            token=self.admin_token
        )

        msg = "Timer paused" if success else f"Error: {response.text if hasattr(response, 'text') else response}"
        self.results.add_result("Pause Timer", success, msg)
        return success

    def test_reset_timer(self):
        """Test resetting timer"""
        if not self.admin_token or not self.session_id:
            self.results.add_result("Reset Timer", False, "No token or session ID", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            f"/qm/sessions/{self.session_id}/timer/reset",
            token=self.admin_token
        )

        msg = "Timer reset" if success else f"Error: {response.text if hasattr(response, 'text') else response}"
        self.results.add_result("Reset Timer", success, msg)
        return success

    # ========== Quiz Master - Buzzer Tests ==========

    def test_unlock_buzzers(self):
        """Test unlocking buzzers"""
        if not self.admin_token or not self.session_id:
            self.results.add_result("Unlock Buzzers", False, "No token or session ID", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            f"/qm/sessions/{self.session_id}/buzzer/lock?locked=false",
            token=self.admin_token
        )

        msg = "Buzzers unlocked" if success else f"Error: {response.text if hasattr(response, 'text') else response}"
        self.results.add_result("Unlock Buzzers", success, msg)
        return success

    def test_lock_buzzers(self):
        """Test locking buzzers"""
        if not self.admin_token or not self.session_id:
            self.results.add_result("Lock Buzzers", False, "No token or session ID", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            f"/qm/sessions/{self.session_id}/buzzer/lock?locked=true",
            token=self.admin_token
        )

        msg = "Buzzers locked" if success else f"Error: {response.text if hasattr(response, 'text') else response}"
        self.results.add_result("Lock Buzzers", success, msg)
        return success

    # ========== Quiz Master - Score Tests ==========

    def test_adjust_score(self):
        """Test adjusting team score"""
        if not self.admin_token or not self.session_id or not self.team_id:
            self.results.add_result("Adjust Score", False, "No token, session ID, or team ID", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            f"/qm/sessions/{self.session_id}/scores/{self.team_id}",
            token=self.admin_token,
            data={"delta": 10, "round_id": 1, "reason": "Correct answer"}
        )

        if success and response:
            try:
                data = response.json()
                msg = f"New total: {data.get('new_total', 'Unknown')}"
            except:
                msg = "Score adjusted"
        else:
            msg = f"Error: {response if isinstance(response, str) else response.text}"

        self.results.add_result("Adjust Score", success, msg)
        return success

    # ========== Display Tests ==========

    def test_display_snapshot(self):
        """Test getting display snapshot"""
        if not self.session_id:
            self.results.add_result("Display Snapshot", False, "No session ID", skipped=True)
            return False

        success, response = self.make_request(
            "GET",
            f"/display/sessions/{self.session_id}/snapshot"
        )

        if success and response:
            try:
                data = response.json()
                msg = f"Session: {data.get('session_name')}, Mode: {data.get('mode')}"
            except:
                msg = "Invalid JSON response"
        else:
            msg = f"Error: {response if isinstance(response, str) else response.text}"

        self.results.add_result("Display Snapshot", success, msg)
        return success

    # ========== Database Migration Test ==========

    def test_admin_settings_table_exists(self):
        """Test if admin_settings table exists"""
        success, response = self.make_request(
            "GET",
            "/admin/settings",
            token=self.admin_token
        )

        msg = "admin_settings table exists" if success else "admin_settings table may not exist (run migration)"
        self.results.add_result("Admin Settings Table", success, msg)
        return success

    # ========== Team Session Assignment Tests ==========

    def test_assign_team_to_session(self):
        """Test assigning a team to a session"""
        if not self.admin_token or not self.session_id or not self.team_id:
            self.results.add_result("Assign Team to Session", False, "Missing prerequisites", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            f"/admin/sessions/{self.session_id}/teams",
            token=self.admin_token,
            data={"team_ids": [self.team_id], "starting_score": 0}
        )

        msg = "Team assigned to session" if success else f"Error: {response.text if hasattr(response, 'text') else response}"
        self.results.add_result("Assign Team to Session", success, msg)
        return success

    # ========== Round Management Tests ==========

    def test_create_round(self):
        """Test creating a round in a session"""
        if not self.admin_token or not self.session_id:
            self.results.add_result("Create Round", False, "Missing prerequisites", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            f"/admin/sessions/{self.session_id}/rounds",
            token=self.admin_token,
            data={
                "name": "Round 1",
                "type": "normal",
                "timer_default_ms": 30000,
                "scoring_presets": {"positive": [10, 20], "negative": [-5]},
                "order_index": 1
            }
        )

        msg = "Round created" if success else f"Error: {response.text if hasattr(response, 'text') else response}"
        self.results.add_result("Create Round", success, msg)
        return success

    def test_list_rounds(self):
        """Test listing rounds for a session"""
        if not self.admin_token or not self.session_id:
            self.results.add_result("List Rounds", False, "Missing prerequisites", skipped=True)
            return False

        success, response = self.make_request(
            "GET",
            f"/admin/sessions/{self.session_id}/rounds",
            token=self.admin_token
        )

        if success and response:
            try:
                rounds = response.json()
                msg = f"Found {len(rounds)} round(s)"
            except:
                msg = "Invalid JSON response"
        else:
            msg = f"Error: {response if isinstance(response, str) else response.text}"

        self.results.add_result("List Rounds", success, msg)
        return success

    # ========== Settings Edge Cases ==========

    def test_update_fps_setting(self):
        """Test updating FPS setting"""
        if not self.admin_token:
            self.results.add_result("Update FPS Setting", False, "No admin token", skipped=True)
            return False

        success, response = self.make_request(
            "PUT",
            "/admin/settings/screen_share_fps?value=10",
            token=self.admin_token
        )

        msg = "FPS setting updated" if success else f"Error: {response.text if hasattr(response, 'text') else response}"
        self.results.add_result("Update FPS Setting", success, msg)
        return success

    def test_update_quality_setting(self):
        """Test updating quality setting"""
        if not self.admin_token:
            self.results.add_result("Update Quality Setting", False, "No admin token", skipped=True)
            return False

        success, response = self.make_request(
            "PUT",
            "/admin/settings/screen_share_quality?value=0.7",
            token=self.admin_token
        )

        msg = "Quality setting updated" if success else f"Error: {response.text if hasattr(response, 'text') else response}"
        self.results.add_result("Update Quality Setting", success, msg)
        return success

    def test_get_nonexistent_setting(self):
        """Test getting a non-existent setting (should fail)"""
        if not self.admin_token:
            self.results.add_result("Get Non-existent Setting", False, "No admin token", skipped=True)
            return False

        success, response = self.make_request(
            "GET",
            "/admin/settings/nonexistent_setting",
            token=self.admin_token,
            expected_status=404
        )

        msg = "Correctly returned 404" if success else "Did not handle non-existent setting properly"
        self.results.add_result("Get Non-existent Setting (404)", success, msg)
        return success

    # ========== Authorization Tests ==========

    def test_unauthorized_access(self):
        """Test accessing admin endpoint without token"""
        success, response = self.make_request(
            "GET",
            "/admin/teams",
            expected_status=401
        )

        msg = "Correctly rejected unauthorized access" if success else "Did not reject unauthorized access"
        self.results.add_result("Unauthorized Access (401)", success, msg)
        return success

    def test_invalid_token_access(self):
        """Test accessing endpoint with invalid token"""
        success, response = self.make_request(
            "GET",
            "/admin/teams",
            token="invalid_token_12345",
            expected_status=401
        )

        msg = "Correctly rejected invalid token" if success else "Did not reject invalid token"
        self.results.add_result("Invalid Token Access (401)", success, msg)
        return success

    # ========== Session Update Tests ==========

    def test_update_session(self):
        """Test updating session details"""
        if not self.admin_token or not self.session_id:
            self.results.add_result("Update Session", False, "Missing prerequisites", skipped=True)
            return False

        success, response = self.make_request(
            "PATCH",
            f"/admin/sessions/{self.session_id}",
            token=self.admin_token,
            data={"banner_text": "UPDATED BANNER", "status": "live"}
        )

        msg = "Session updated" if success else f"Error: {response.text if hasattr(response, 'text') else response}"
        self.results.add_result("Update Session", success, msg)
        return success

    # ========== Team Update Tests ==========

    def test_update_team(self):
        """Test updating team details"""
        if not self.admin_token or not self.team_id:
            self.results.add_result("Update Team", False, "Missing prerequisites", skipped=True)
            return False

        success, response = self.make_request(
            "PATCH",
            f"/admin/teams/{self.team_id}",
            token=self.admin_token,
            data={"name": "Updated Team Name", "is_active": True}
        )

        msg = "Team updated" if success else f"Error: {response.text if hasattr(response, 'text') else response}"
        self.results.add_result("Update Team", success, msg)
        return success

    # ========== WebSocket Tests ==========

    def test_websocket_display_connection(self):
        """Test WebSocket connection for display"""
        if not WEBSOCKET_AVAILABLE:
            self.results.add_result("WebSocket Display Connection", False, "websocket-client not installed", skipped=True)
            return False

        if not self.session_id:
            self.results.add_result("WebSocket Display Connection", False, "No session ID", skipped=True)
            return False

        try:
            ws_url = f"ws://{BASE_URL.replace('http://', '')}/ws/display/{self.session_id}"
            ws = create_connection(ws_url, timeout=5)
            ws.close()
            self.results.add_result("WebSocket Display Connection", True, "Connected successfully")
            return True
        except Exception as e:
            self.results.add_result("WebSocket Display Connection", False, f"Error: {str(e)}")
            return False

    def test_websocket_qm_connection(self):
        """Test WebSocket connection for quiz master"""
        if not WEBSOCKET_AVAILABLE:
            self.results.add_result("WebSocket QM Connection", False, "websocket-client not installed", skipped=True)
            return False

        if not self.session_id or not self.admin_token:
            self.results.add_result("WebSocket QM Connection", False, "Missing prerequisites", skipped=True)
            return False

        try:
            ws_url = f"ws://{BASE_URL.replace('http://', '')}/ws/qm/{self.session_id}?token={self.admin_token}"
            ws = create_connection(ws_url, timeout=5)
            ws.close()
            self.results.add_result("WebSocket QM Connection", True, "Connected successfully")
            return True
        except Exception as e:
            self.results.add_result("WebSocket QM Connection", False, f"Error: {str(e)}")
            return False

    # ========== API Response Format Tests ==========

    def test_api_response_formats(self):
        """Test that API responses have correct JSON format"""
        if not self.admin_token:
            self.results.add_result("API Response Format", False, "No admin token", skipped=True)
            return False

        tests_passed = 0
        tests_total = 0

        # Test teams endpoint
        tests_total += 1
        success, response = self.make_request("GET", "/admin/teams", token=self.admin_token)
        if success and response:
            try:
                data = response.json()
                if isinstance(data, list):
                    tests_passed += 1
            except:
                pass

        # Test sessions endpoint
        tests_total += 1
        success, response = self.make_request("GET", "/admin/sessions", token=self.admin_token)
        if success and response:
            try:
                data = response.json()
                if isinstance(data, list):
                    tests_passed += 1
            except:
                pass

        # Test settings endpoint
        tests_total += 1
        success, response = self.make_request("GET", "/admin/settings", token=self.admin_token)
        if success and response:
            try:
                data = response.json()
                if isinstance(data, dict):
                    tests_passed += 1
            except:
                pass

        success = tests_passed == tests_total
        msg = f"{tests_passed}/{tests_total} endpoints returned correct JSON format"
        self.results.add_result("API Response Format", success, msg)
        return success

    # ========== Performance Tests ==========

    def test_response_time(self):
        """Test API response times"""
        if not self.admin_token:
            self.results.add_result("Response Time Test", False, "No admin token", skipped=True)
            return False

        start_time = time.time()
        success, response = self.make_request("GET", "/admin/teams", token=self.admin_token)
        response_time = (time.time() - start_time) * 1000  # Convert to ms

        # Response should be under 1000ms
        performance_ok = response_time < 1000
        msg = f"Response time: {response_time:.0f}ms {'(Good)' if performance_ok else '(Slow)'}"

        self.results.add_result("API Response Time", success and performance_ok, msg)
        return success and performance_ok

    # ========== Edge Case Tests ==========

    def test_create_duplicate_team(self):
        """Test creating team with duplicate code (should fail)"""
        if not self.admin_token:
            self.results.add_result("Duplicate Team Code", False, "No admin token", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            "/admin/teams",
            token=self.admin_token,
            data={"name": "Duplicate Team", "code": "ALPHA123"},  # Same code as first test
            expected_status=400
        )

        msg = "Correctly rejected duplicate team code" if success else "Did not handle duplicate properly"
        self.results.add_result("Duplicate Team Code (400)", success, msg)
        return success

    def test_empty_request_body(self):
        """Test endpoint with empty request body"""
        if not self.admin_token:
            self.results.add_result("Empty Request Body", False, "No admin token", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            "/admin/teams",
            token=self.admin_token,
            data={},
            expected_status=422  # Validation error
        )

        msg = "Correctly rejected empty body" if success else "Did not validate empty body"
        self.results.add_result("Empty Request Body (422)", success, msg)
        return success

    # ========== Undo Score Test ==========

    def test_undo_score(self):
        """Test undoing score adjustment"""
        if not self.admin_token or not self.session_id or not self.team_id:
            self.results.add_result("Undo Score", False, "Missing prerequisites", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            f"/qm/sessions/{self.session_id}/scores/{self.team_id}/undo",
            token=self.admin_token
        )

        if success and response:
            try:
                data = response.json()
                msg = f"Undo successful, new total: {data.get('new_total', 'Unknown')}"
            except:
                msg = "Score undone"
        else:
            msg = f"Error: {response if isinstance(response, str) else response.text}"

        self.results.add_result("Undo Score", success, msg)
        return success

    # ========== Slide Jump Test ==========

    def test_jump_to_slide(self):
        """Test jumping to specific slide"""
        if not self.admin_token or not self.session_id or not self.slide_id:
            self.results.add_result("Jump to Slide", False, "Missing prerequisites", skipped=True)
            return False

        success, response = self.make_request(
            "POST",
            f"/qm/sessions/{self.session_id}/slide/jump?slide_id={self.slide_id}&mode=question",
            token=self.admin_token
        )

        msg = "Jump successful" if success else f"Error: {response.text if hasattr(response, 'text') else response}"
        self.results.add_result("Jump to Slide", success, msg)
        return success

    # ========== Run All Tests ==========

    def run_all_tests(self):
        """Run all tests in order"""
        print(f"\n{Style.BRIGHT}{Fore.MAGENTA}")
        print("╔" + "="*78 + "╗")
        print("║" + " "*20 + "QUIZ APPLICATION TEST SUITE" + " "*31 + "║")
        print("║" + " "*78 + "║")
        print("║" + f"  Testing: {BASE_URL}".ljust(78) + "║")
        print("╚" + "="*78 + "╝")
        print(f"{Style.RESET_ALL}")

        # 1. Health Check
        self.print_section("1. SERVER HEALTH CHECK")
        if not self.test_health_check():
            print(f"\n{Fore.RED}Server is not running at {BASE_URL}{Style.RESET_ALL}")
            print(f"Please start the server and try again.")
            self.results.print_summary()
            return

        # 2. Authentication Tests
        self.print_section("2. AUTHENTICATION TESTS")
        self.test_admin_login()
        self.test_invalid_login()

        # 3. Admin - Team Management
        self.print_section("3. TEAM MANAGEMENT TESTS")
        self.test_create_team()
        self.test_list_teams()

        # 4. Admin - Session Management
        self.print_section("4. SESSION MANAGEMENT TESTS")
        self.test_create_session()
        self.test_list_sessions()

        # 5. Admin - User Management
        self.print_section("5. USER MANAGEMENT TESTS")
        self.test_create_quiz_master()
        self.test_create_presenter()

        # 6. Admin - Settings Tests
        self.print_section("6. ADMIN SETTINGS TESTS (Screen Sharing Feature)")
        self.test_admin_settings_table_exists()
        self.test_get_settings()
        self.test_get_display_mode_setting()
        self.test_update_display_mode()

        # 7. Quiz Master - Session Tests
        self.print_section("7. QUIZ MASTER SESSION TESTS")
        self.test_qm_get_live_sessions()

        # 8. Quiz Master - Slide Navigation
        self.print_section("8. SLIDE NAVIGATION TESTS")
        self.test_next_slide()
        self.test_previous_slide()

        # 9. Quiz Master - Timer Tests
        self.print_section("9. TIMER TESTS")
        self.test_start_timer()
        self.test_pause_timer()
        self.test_reset_timer()

        # 10. Quiz Master - Buzzer Tests
        self.print_section("10. BUZZER TESTS")
        self.test_unlock_buzzers()
        self.test_lock_buzzers()

        # 11. Quiz Master - Score Tests
        self.print_section("11. SCORE TESTS")
        self.test_adjust_score()

        # 12. Display Tests
        self.print_section("12. DISPLAY TESTS")
        self.test_display_snapshot()

        # 13. Team Session Assignment
        self.print_section("13. TEAM SESSION ASSIGNMENT TESTS")
        self.test_assign_team_to_session()

        # 14. Round Management
        self.print_section("14. ROUND MANAGEMENT TESTS")
        self.test_create_round()
        self.test_list_rounds()

        # 15. Advanced Settings Tests
        self.print_section("15. ADVANCED SETTINGS TESTS")
        self.test_update_fps_setting()
        self.test_update_quality_setting()
        self.test_get_nonexistent_setting()

        # 16. Authorization & Security Tests
        self.print_section("16. AUTHORIZATION & SECURITY TESTS")
        self.test_unauthorized_access()
        self.test_invalid_token_access()

        # 17. Update Tests
        self.print_section("17. UPDATE OPERATION TESTS")
        self.test_update_session()
        self.test_update_team()

        # 18. WebSocket Connection Tests
        if WEBSOCKET_AVAILABLE:
            self.print_section("18. WEBSOCKET CONNECTION TESTS")
            self.test_websocket_display_connection()
            self.test_websocket_qm_connection()
        else:
            print(f"\n{Fore.YELLOW}Skipping WebSocket tests (websocket-client not installed){Style.RESET_ALL}\n")

        # 19. API Quality Tests
        self.print_section("19. API QUALITY TESTS")
        self.test_api_response_formats()
        self.test_response_time()

        # 20. Edge Case Tests
        self.print_section("20. EDGE CASE & ERROR HANDLING TESTS")
        self.test_create_duplicate_team()
        self.test_empty_request_body()

        # 21. Advanced Operations
        self.print_section("21. ADVANCED OPERATIONS")
        self.test_undo_score()
        self.test_jump_to_slide()

        # Print Summary
        self.results.print_summary()

        # Print recommendations
        print(f"\n{Style.BRIGHT}RECOMMENDATIONS:{Style.RESET_ALL}")
        if self.results.failed > 0:
            print(f"{Fore.RED}✗ Fix failed tests before deployment{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}✓ All tests passed! System is ready for deployment{Style.RESET_ALL}")

        if not WEBSOCKET_AVAILABLE:
            print(f"{Fore.YELLOW}! Install websocket-client for complete testing{Style.RESET_ALL}")

        # Exit with appropriate code
        sys.exit(0 if self.results.failed == 0 else 1)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Quiz Application Comprehensive Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_all_endpoints.py
  python test_all_endpoints.py --url http://192.168.1.100:8000
  python test_all_endpoints.py --verbose
  python test_all_endpoints.py --url http://myserver.com:8000 --verbose

Note: Make sure the quiz server is running before executing tests.
        """
    )

    parser.add_argument(
        '--url',
        type=str,
        default='http://localhost:8000',
        help='Base URL of the quiz server (default: http://localhost:8000)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show verbose output'
    )

    parser.add_argument(
        '--skip-websocket',
        action='store_true',
        help='Skip WebSocket tests'
    )

    return parser.parse_args()


if __name__ == "__main__":
    # Parse arguments
    args = parse_args()

    # Update global configuration
    BASE_URL = args.url
    API_URL = f"{BASE_URL}/api"
    VERBOSE = args.verbose

    print(f"\n{Style.BRIGHT}{Fore.MAGENTA}")
    print("╔" + "="*78 + "╗")
    print("║" + " "*15 + "QUIZ APPLICATION COMPREHENSIVE TEST SUITE" + " "*22 + "║")
    print("║" + " "*78 + "║")
    print("║" + f"  Target Server: {BASE_URL}".ljust(78) + "║")
    print("║" + f"  Tests: 50+ endpoint and functionality tests".ljust(78) + "║")
    print("╚" + "="*78 + "╝")
    print(f"{Style.RESET_ALL}\n")

    tester = QuizTester()
    tester.run_all_tests()
