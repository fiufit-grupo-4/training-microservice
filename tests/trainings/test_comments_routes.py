from bson import ObjectId
import mongomock
import pytest
from requests.models import Response
from fastapi.testclient import TestClient
from app.main import app, logger
from app.settings.auth_settings import Settings

client = TestClient(app)

trainer_id_example_mock = str(ObjectId())

training_example_mock = {
    "id_trainer": trainer_id_example_mock,
    "title": "A",
    "description": "string",
    "type": "Caminata",
    "difficulty": 1,
    "media": [
        {"media_type": "image", "url": "chauuu.png"},
        {"media_type": "video", "url": "hola.mp4"},
    ],
    "blocked": False,
    "scores": [],
    "comments": []
}

access_token_trainer_example = Settings.generate_token(trainer_id_example_mock)

def mock_get(*args, **kwargs):
    response = Response()
    response.status_code = 200
    response.json = lambda: {"id" : trainer_id_example_mock, "name": "Juan", "lastname": "Perez"}
    return response

@pytest.fixture()
def mongo_mock(monkeypatch):
    mongo_client = mongomock.MongoClient()
    db = mongo_client.get_database("training_microservice")
    col = db.get_collection("trainings")
    col.insert_one(training_example_mock)

    app.database = db
    app.logger = logger
    monkeypatch.setattr(app, "database", db)
    monkeypatch.setattr("app.trainings.user_small.ServiceUsers.get", mock_get)


def test_post_comment_success(mongo_mock):
    training = client.get("/trainings", json={"title": "A"}).json()[0]
    assert not training["comments"]
    
    training_id = training["id"]
    response = client.post(
        f"/trainings/{training_id}/comment",
        json={"detail": "AsdAsd"},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 201
    assert response.json().get("detail") == "AsdAsd"

    training = client.get("/trainings", json={"title": "A"}).json()[0]
    assert training["comments"][0].get("detail") == "AsdAsd"
    
# user puede comentar muchas veces un mismo training, no es unico!
def test_post_comment_multiple_times_success(mongo_mock):
    training = client.get("/trainings", json={"title": "A"}).json()[0]
    assert not training["comments"]
    
    training_id = training["id"]
    response = client.post(
        f"/trainings/{training_id}/comment",
        json={"detail": "AsdAsd1"},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 201
    assert response.json().get("detail") == "AsdAsd1"

    response = client.post(
        f"/trainings/{training_id}/comment",
        json={"detail": "AsdAsd2"},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 201
    assert response.json().get("detail") == "AsdAsd2"

    training = client.get("/trainings", json={"title": "A"}).json()[0]
    assert training["comments"][0].get("detail") == "AsdAsd1"
    assert training["comments"][1].get("detail") == "AsdAsd2"
    
def test_post_comment_invalids(mongo_mock):
    training = client.get("/trainings", json={"title": "A"}).json()[0]
    assert not training["comments"]
    
    training_id = training["id"]
    response = client.post(
        f"/trainings/{training_id}/comment",
        json={"detail": ""},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 422

    response = client.post(
        f"/trainings/{training_id}/comment",
        json={"detail": "a" * 501},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 422

    training = client.get("/trainings", json={"title": "A"}).json()[0]
    assert not training["comments"]
    

    
def test_modify_comment_success(mongo_mock):
    training = client.get("/trainings", json={"title": "A"}).json()[0]
    assert not training["comments"]
    
    training_id = training["id"]
    response = client.post(
        f"/trainings/{training_id}/comment",
        json={"detail": "AsdAsd"},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 201
    res = response.json()
    res.pop("id")
    assert res == {"detail": "AsdAsd", "id_user": trainer_id_example_mock}
    
    training = client.get("/trainings", json={"title": "A"}).json()[0]

    comment_id = training["comments"][0]["id"]

    response = client.patch(
        f"/trainings/{training_id}/comment/{comment_id}",
        json={"detail": "AsdAsd patched"},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 200


    training = client.get("/trainings", json={"title": "A"}).json()[0]
    assert training["comments"][0].get("detail") == "AsdAsd patched"
    
    
def test_modify_comment_invalids(mongo_mock):
    training = client.get("/trainings", json={"title": "A"}).json()[0]
    assert not training["comments"]
    
    training_id = training["id"]
    response = client.post(
        f"/trainings/{training_id}/comment",
        json={"detail": "AsdAsd"},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 201
    res = response.json()
    res.pop("id")
    assert res == {"detail": "AsdAsd", "id_user": trainer_id_example_mock}

    training = client.get("/trainings", json={"title": "A"}).json()[0]
    comment_id = training["comments"][0]["id"]

    response = client.patch(
        f"/trainings/{training_id}/comment/{comment_id}",
        json={"detail": ""},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 422

    response = client.patch(
        f"/trainings/{training_id}/comment/{comment_id}",
        json={"detail": "a" * 501},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 422

    training = client.get("/trainings", json={"title": "A"}).json()[0]
    assert training["comments"][0].get("detail") == "AsdAsd"
    

def test_delete_comment_success(mongo_mock):
    training = client.get("/trainings", json={"title": "A"}).json()[0]
    assert not training["comments"]
    
    training_id = training["id"]
    response = client.post(
        f"/trainings/{training_id}/comment",
        json={"detail": "AsdAsd"},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 201

    training = client.get("/trainings", json={"title": "A"}).json()[0]
    comment_id = training["comments"][0]["id"]

    response = client.delete(
        f"/trainings/{training_id}/comment/{comment_id}",
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    assert response.status_code == 200

    training = client.get("/trainings", json={"title": "A"}).json()[0]
    assert not training["comments"]