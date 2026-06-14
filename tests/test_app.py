"""
Backend tests for the Mergington High School activities API.
Tests all CRUD operations and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test."""
    # Store initial state
    initial_state = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
    }
    
    # Clear activities dict and repopulate with initial state
    activities.clear()
    activities.update(initial_state)
    
    yield
    
    # Cleanup after test
    activities.clear()
    activities.update(initial_state)


class TestRoot:
    """Tests for the root endpoint."""
    
    def test_root_redirect(self, client):
        """Test that GET / redirects to /static/index.html."""
        # Arrange: No setup needed for this endpoint
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_all_activities(self, client):
        """Test retrieving all activities."""
        # Arrange: Activities are pre-populated by the reset_activities fixture
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_activities_have_correct_structure(self, client):
        """Test that activities have all required fields."""
        # Arrange: Fetch activities from API
        
        # Act
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        # Assert: Check all required fields exist
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
    
    def test_activities_contain_initial_participants(self, client):
        """Test that activities contain the initial participants."""
        # Arrange: Get activities list
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert: Verify initial participants are present
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_successful_signup(self, client):
        """Test successful signup for an activity."""
        # Arrange
        email = "newstudent@mergington.edu"
        activity_name = "Chess%20Club"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in data["message"]
        assert email in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup adds the participant to the activity."""
        # Arrange
        email = "newstudent@mergington.edu"
        
        # Act: Sign up the student
        client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        
        # Assert: Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
    
    def test_duplicate_signup_rejected(self, client):
        """Test that duplicate signup returns 400 error."""
        # Arrange
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test that signup to non-existent activity returns 404."""
        # Arrange
        email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/NonExistent%20Activity/signup?email={email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "not found" in data["detail"].lower()
    
    def test_signup_multiple_different_activities(self, client):
        """Test that a student can signup for multiple activities."""
        # Arrange
        email = "student@mergington.edu"
        
        # Act: Sign up for Chess Club
        response1 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Act: Sign up for Programming Class
        response2 = client.post(
            f"/activities/Programming%20Class/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Assert: Verify both signups succeeded
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Programming Class"]["participants"]


class TestRemoveParticipant:
    """Tests for the DELETE /activities/{activity_name}/participants endpoint."""
    
    def test_successful_participant_removal(self, client):
        """Test successful removal of a participant."""
        # Arrange
        email = "michael@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/Chess%20Club/participants?email={email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Removed" in data["message"]
    
    def test_removal_updates_participants_list(self, client):
        """Test that removal updates the participants list."""
        # Arrange
        email = "michael@mergington.edu"
        
        # Act: Remove the participant
        client.delete(
            f"/activities/Chess%20Club/participants?email={email}"
        )
        
        # Assert: Verify removal from participants list
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
    
    def test_remove_nonexistent_participant(self, client):
        """Test that removing non-existent participant returns 404."""
        # Arrange
        email = "nonexistent@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/Chess%20Club/participants?email={email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "not found" in data["detail"].lower()
    
    def test_remove_from_nonexistent_activity(self, client):
        """Test that removing from non-existent activity returns 404."""
        # Arrange
        email = "test@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/NonExistent%20Activity/participants?email={email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 404
        assert "not found" in data["detail"].lower()
    
    def test_remove_and_resign_up(self, client):
        """Test that a removed participant can sign up again."""
        # Arrange
        email = "michael@mergington.edu"
        
        # Act: Remove participant
        client.delete(
            f"/activities/Chess%20Club/participants?email={email}"
        )
        
        # Assert: Verify removal
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
        
        # Act: Sign up again
        signup_response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Assert: Verify re-signup
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Chess Club"]["participants"]


class TestActivityCapacity:
    """Tests for respecting max_participants capacity."""
    
    def test_get_activity_spots_left(self, client):
        """Test that activities report correct available spots."""
        # Arrange: Get activities with initial state
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert: Chess Club has max 12, currently has 2 participants
        chess_club = data["Chess Club"]
        expected_spots = 12 - len(chess_club["participants"])
        assert expected_spots == 10
    
    def test_spots_decrease_after_signup(self, client):
        """Test that available spots decrease after signup."""
        # Arrange: Get initial spot count for Programming Class
        response1 = client.get("/activities")
        prog_class_initial = response1.json()["Programming Class"]
        initial_count = len(prog_class_initial["participants"])
        
        # Act: Sign up a new participant
        client.post(
            "/activities/Programming%20Class/signup?email=newperson@mergington.edu"
        )
        
        # Assert: Verify spot count decreased
        response2 = client.get("/activities")
        prog_class_updated = response2.json()["Programming Class"]
        updated_count = len(prog_class_updated["participants"])
        
        assert updated_count == initial_count + 1
        assert updated_count == 3  # 2 initial + 1 new
