from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activities_data(monkeypatch):
    test_data = {
        "Chess Club": {
            "description": "Practice chess",
            "schedule": "Fridays",
            "max_participants": 12,
            "participants": ["student@mergington.edu"],
        },
        "Art Club": {
            "description": "Practice art",
            "schedule": "Wednesdays",
            "max_participants": 15,
            "participants": ["student@mergington.edu"],
        },
    }
    monkeypatch.setattr(app_module, "activities", test_data)
    return test_data


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_get_activities_returns_data_without_caching(client, activities_data):
    # Arrange
    expected_activities = activities_data

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(client, activities_data):
    # Arrange
    activity_name = "Chess Club"
    email = "new-student@mergington.edu"
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities_data[activity_name]["participants"]


def test_signup_returns_404_for_unknown_activity(client, activities_data):
    # Arrange
    email = "new-student@mergington.edu"
    original_data = {name: activity.copy() for name, activity in activities_data.items()}

    # Act
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    assert activities_data == original_data


def test_signup_rejects_duplicate_participant(client, activities_data):
    # Arrange
    activity_name = "Chess Club"
    email = activities_data[activity_name]["participants"][0]
    original_participants = list(activities_data[activity_name]["participants"])
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert activities_data[activity_name]["participants"] == original_participants


def test_unregister_removes_participant_from_only_selected_activity(client, activities_data):
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.delete(
        f"/activities/{activity_path}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities_data[activity_name]["participants"]
    assert email in activities_data["Art Club"]["participants"]


def test_unregister_returns_404_for_unknown_activity(client, activities_data):
    # Arrange
    email = "student@mergington.edu"
    original_data = {name: activity.copy() for name, activity in activities_data.items()}

    # Act
    response = client.delete(
        "/activities/Unknown%20Club/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
    assert activities_data == original_data


def test_unregister_returns_404_for_unregistered_participant(client, activities_data):
    # Arrange
    activity_name = "Chess Club"
    email = "absent-student@mergington.edu"
    original_participants = list(activities_data[activity_name]["participants"])
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.delete(
        f"/activities/{activity_path}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert activities_data[activity_name]["participants"] == original_participants
