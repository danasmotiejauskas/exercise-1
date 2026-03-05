from copy import deepcopy
import pytest

from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)

# keep a pristine copy of the in-memory database so tests can restore it
initial_activities = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """ARRANGE: restore the global activities dict before each test"""
    activities.clear()
    activities.update(deepcopy(initial_activities))


# --- tests follow AAA pattern ---

def test_root_redirect():
    # ACT
    response = client.get("/", follow_redirects=False)

    # ASSERT
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    # ACT
    response = client.get("/activities")

    # ASSERT
    assert response.status_code == 200
    assert response.json() == initial_activities


def test_signup_success():
    # ARRANGE
    activity = "Chess Club"
    email = "newstudent@mergington.edu"

    # ACT
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})

    # ASSERT
    assert resp.status_code == 200
    assert resp.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in activities[activity]["participants"]


def test_signup_nonexistent_activity():
    # ARRANGE
    activity = "Nonexistent"
    email = "ignore@mergington.edu"

    # ACT
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})

    # ASSERT
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"


def test_signup_already_signed():
    # ARRANGE
    activity = "Chess Club"
    email = initial_activities[activity]["participants"][0]

    # ACT
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})

    # ASSERT
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Student already signed up for this activity"


def test_unregister_success():
    # ARRANGE
    activity = "Chess Club"
    email = initial_activities[activity]["participants"][0]

    # ACT
    resp = client.delete(f"/activities/{activity}/signup", params={"email": email})

    # ASSERT
    assert resp.status_code == 200
    assert resp.json() == {"message": f"Unregistered {email} from {activity}"}
    assert email not in activities[activity]["participants"]


def test_unregister_nonexistent_activity():
    # ARRANGE
    activity = "Nonexistent"
    email = "whatever@mergington.edu"

    # ACT
    resp = client.delete(f"/activities/{activity}/signup", params={"email": email})

    # ASSERT
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"


def test_unregister_not_signed():
    # ARRANGE
    activity = "Chess Club"
    email = "nobody@mergington.edu"

    # ACT
    resp = client.delete(f"/activities/{activity}/signup", params={"email": email})

    # ASSERT
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Student not signed up for this activity"
