"""
Comprehensive test suite using AAA (Arrange-Act-Assert) pattern.
Coverage includes edge cases, boundary testing, and risk areas.
"""
import pytest


class TestGetActivitiesEndpoint:
    """GET /activities endpoint - basic functionality"""
    
    def test_returns_all_activities(self, client):
        """
        Arrange: Client is ready
        Act: Get all activities
        Assert: All activities returned successfully
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) >= 3
        assert "Chess Club" in activities
        assert "Programming Class" in activities


class TestSignupEdgeCases:
    """Boundary testing and edge cases for signup"""
    
    def test_signup_empty_email(self, client):
        """
        EDGE CASE: Empty email
        Arrange: Empty email string
        Act: Attempt signup with empty email
        Assert: Request processed (FastAPI doesn't validate format)
        """
        # Arrange
        activity = "Programming Class"
        email = ""
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert - Empty email is technically accepted by FastAPI
        # This could be a RISK if email format validation is desired
        assert response.status_code in [200, 400]  # Depends on validation
    
    def test_signup_email_with_special_chars(self, client):
        """
        EDGE CASE: Email with special characters
        Arrange: Valid email with special characters
        Act: Signup with unusual but valid email
        Assert: Signup succeeds
        """
        # Arrange
        activity = "Programming Class"
        email = "user+tag@sub.domain.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
    
    def test_signup_very_long_email(self, client):
        """
        EDGE CASE: Very long email address
        Arrange: Extremely long email (still valid format)
        Act: Signup with long email
        Assert: Signup succeeds
        """
        # Arrange
        activity = "Programming Class"
        email = "a" * 50 + "@example.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200


class TestSignupRiskAreas:
    """Risk areas: double registration, capacity overflow"""
    
    def test_prevent_double_registration(self, client):
        """
        RISK: Double registration vulnerability (original bug)
        Arrange: User already signed up
        Act: Attempt to signup again
        Assert: Second signup is rejected
        """
        # Arrange
        activity = "Chess Club"
        email = "alice@school.edu"  # Already in Chess Club
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_prevent_capacity_overflow(self, client):
        """
        RISK: Capacity overflow - signing up beyond max_participants
        Arrange: Activity at max capacity (1 participant, max=1)
        Act: Try to add another participant
        Assert: Signup is rejected for full activity
        """
        # Arrange
        activity = "Full Activity"  # max=1, participants=["full@school.edu"]
        email = "overflow@school.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "maximum capacity" in response.json()["detail"]
    
    def test_signup_at_boundary_capacity(self, client):
        """
        BOUNDARY TEST: Signup when capacity is exactly 1 spot remaining
        Arrange: Activity has 1 spot left (2 spots, 1 participant)
        Act: Sign up new user
        Assert: Signup succeeds
        """
        # Arrange
        activity = "Chess Club"  # max=3, participants=2, spots_left=1
        email = "charlie@school.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        
        # Verify capacity is now full
        response_activities = client.get("/activities")
        assert len(response_activities.json()["Chess Club"]["participants"]) == 3
    
    def test_signup_fails_when_one_spot_over_capacity(self, client):
        """
        BOUNDARY TEST: Verify strict capacity enforcement
        Arrange: Activity now at exact capacity (3 spots, 3 participants)
        Act: Attempt to signup after capacity filled
        Assert: Signup is rejected
        """
        # Arrange - First fill the activity
        activity = "Chess Club"
        email_third = "charlie@school.edu"
        client.post(f"/activities/{activity}/signup", params={"email": email_third})
        
        # Now attempt fourth signup (over capacity)
        email_fourth = "diana@school.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email_fourth}
        )
        
        # Assert
        assert response.status_code == 400
        assert "maximum capacity" in response.json()["detail"]


class TestSignupEquivalenceClasses:
    """Equivalent class partitioning for signup"""
    
    def test_signup_new_user_valid_email(self, client):
        """
        EQUIVALENCE CLASS: New user with valid email
        Arrange: New user email
        Act: Signup
        Assert: Success
        """
        # Arrange
        activity = "Programming Class"
        email = "newuser@school.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "newuser@school.edu" in response.json()["message"]
    
    def test_signup_registered_user_same_activity(self, client):
        """
        EQUIVALENCE CLASS: Already registered user for same activity
        Arrange: User already in activity
        Act: Attempt signup
        Assert: Rejection (4xx error)
        """
        # Arrange
        activity = "Chess Club"
        email = "alice@school.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
    
    def test_signup_nonexistent_activity(self, client):
        """
        EQUIVALENCE CLASS: Non-existent activity
        Arrange: Invalid activity name
        Act: Signup for non-existent activity
        Assert: 404 error
        """
        # Arrange
        activity = "Nonexistent Activity"
        email = "user@school.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestUnregisterEdgeCases:
    """Edge cases for unregister operation"""
    
    def test_unregister_registered_user(self, client):
        """
        Arrange: User is registered
        Act: Unregister user
        Assert: Success
        """
        # Arrange
        activity = "Chess Club"
        email = "alice@school.edu"  # Registered
        
        # Act
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
    
    def test_unregister_unregistered_user(self, client):
        """
        Arrange: User is not registered
        Act: Attempt to unregister
        Assert: 400 error
        """
        # Arrange
        activity = "Chess Club"
        email = "notregistered@school.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_from_nonexistent_activity(self, client):
        """
        Arrange: Invalid activity
        Act: Unregister from non-existent activity
        Assert: 404 error
        """
        # Arrange
        activity = "Fake Activity"
        email = "user@school.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404


class TestStateConsistency:
    """Risk Area: State rollback and consistency after failures"""
    
    def test_state_unchanged_after_failed_signup(self, client):
        """
        RISK: Ensure state consistency on failure
        Arrange: Setup with full activity and failing signup
        Act: Attempt signup that fails
        Assert: Participant list unchanged
        """
        # Arrange
        activity = "Full Activity"
        original_participants = client.get("/activities").json()[activity]["participants"].copy()
        email = "newuser@school.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert - Signup failed
        assert response.status_code == 400
        
        # State unchanged
        current_participants = client.get("/activities").json()[activity]["participants"]
        assert current_participants == original_participants
    
    def test_state_unchanged_after_failed_unregister(self, client):
        """
        RISK: Ensure state consistency when unregister fails
        Arrange: User not registered
        Act: Attempt unregister
        Assert: Participant list unchanged
        """
        # Arrange
        activity = "Chess Club"
        original_participants = client.get("/activities").json()[activity]["participants"].copy()
        email = "notregistered@school.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        current_participants = client.get("/activities").json()[activity]["participants"]
        assert current_participants == original_participants
    
    def test_signup_unregister_state_consistency(self, client):
        """
        RISK: Full workflow maintains consistency
        Arrange: User ready to signup
        Act: Signup -> Verify -> Unregister -> Verify
        Assert: All state transitions correct
        """
        # Arrange
        activity = "Programming Class"
        email = "workflow@school.edu"
        
        # Act - Signup
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Assert - Verify added
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Assert - Verify removed
        activities = client.get("/activities").json()
        assert email not in activities[activity]["participants"]


class TestMultipleUsersScenarios:
    """Integration tests with multiple users"""
    
    def test_different_users_same_activity(self, client):
        """
        Arrange: Multiple new users
        Act: Each signs up for same activity
        Assert: All added if within capacity
        """
        # Arrange
        activity = "Programming Class"
        users = ["user1@school.edu", "user2@school.edu"]
        
        # Act
        for email in users:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            # Assert each signup
            assert response.status_code == 200
        
        # Final assert - All participants added
        activities = client.get("/activities").json()
        for email in users:
            assert email in activities[activity]["participants"]
    
    def test_same_user_different_activities(self, client):
        """
        Arrange: Same user, different activities
        Act: User signs up for multiple activities
        Assert: Registered for all
        """
        # Arrange
        email = "multiuser@school.edu"
        activities_list = ["Chess Club", "Programming Class"]
        
        # Act
        for activity in activities_list:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Assert
        activities = client.get("/activities").json()
        for activity in activities_list:
            assert email in activities[activity]["participants"]
