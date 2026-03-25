import pytest
from copy import deepcopy
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


# Base configuration for test activities
BASE_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 3,
        "participants": ["alice@school.edu", "bob@school.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 2,
        "participants": []
    },
    "Full Activity": {
        "description": "Activity at max capacity",
        "schedule": "Mondays, 3:00 PM - 4:00 PM",
        "max_participants": 1,
        "participants": ["full@school.edu"]
    }
}


@pytest.fixture
def test_activities():
    """
    Creates a fresh copy of test activities for each test.
    Isolates tests from each other's state changes.
    """
    return deepcopy(BASE_ACTIVITIES)


@pytest.fixture
def client(test_activities):
    """
    Creates a test client with isolated activity data.
    Uses AAA pattern: each test gets clean state (Arrange).
    """
    app = FastAPI()
    
    @app.get("/activities")
    def get_activities():
        return test_activities
    
    @app.post("/activities/{activity_name}/signup")
    def signup_for_activity(activity_name: str, email: str):
        # Validate activity exists
        if activity_name not in test_activities:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        activity = test_activities[activity_name]
        
        # Validate student is not already signed up
        if email in activity["participants"]:
            raise HTTPException(status_code=400, detail="Student is already signed up for this activity")
        
        # Check capacity (RISK: capacity overflow)
        if len(activity["participants"]) >= activity["max_participants"]:
            raise HTTPException(status_code=400, detail="Activity is at maximum capacity")
        
        activity["participants"].append(email)
        return {"message": f"Signed up {email} for {activity_name}"}
    
    @app.delete("/activities/{activity_name}/signup")
    def unregister_from_activity(activity_name: str, email: str):
        if activity_name not in test_activities:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        activity = test_activities[activity_name]
        
        if email in activity["participants"]:
            activity["participants"].remove(email)
            return {"message": f"Unregistered {email} from {activity_name}"}
        else:
            raise HTTPException(status_code=400, detail="Student is not registered for this activity")
    
    return TestClient(app)
