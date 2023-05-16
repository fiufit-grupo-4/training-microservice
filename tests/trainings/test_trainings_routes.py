from bson import ObjectId
import mongomock
import pytest
from fastapi.testclient import TestClient
from app.main import app, logger
from app.settings.auth_settings import Settings

from app.trainings.object_id import ObjectIdPydantic
from app.trainings.trainings import router_trainings


client = TestClient(app)

trainer_id_example_mock = ObjectId()

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
    "comments": [],
    "place": "CABA"
}

access_token_trainer_example = Settings.generate_token(str(trainer_id_example_mock))

@pytest.fixture()
def mongo_mock(monkeypatch):
    mongo_client = mongomock.MongoClient()
    db = mongo_client.get_database("training_microservice")
    col = db.get_collection("trainings")
    result = col.insert_one(training_example_mock)

    global training_id_example_mock
    training_id_example_mock = result.inserted_id

    app.database = db
    app.logger = logger
    monkeypatch.setattr(app, "database", db)


def test_get_trainings(mongo_mock):
    response = client.get("/trainings")
    assert response.status_code == 200

    response_body = response.json()

    assert all(item in response_body[0] for item in {
        'blocked': False,
        'description': 'string',
        'difficulty': 1,
        'media': [{'media_type': 'image', 'url': 'chau.png'},
                  {'media_type': 'video', 'url': 'hola.mp4'}],
        'scores': [],
        'comments': [],
        'title': 'A',
        'type': 'Caminata',
        "place": "CABA"
    }
    )

def test_block_status(mongo_mock):
    # Success
    response = client.patch(
        f"/trainings/{training_id_example_mock}/block",
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )

    assert response.status_code == 200
    assert response.json() == f"Training {training_id_example_mock} successfully blocked"

    trainings = app.database["trainings"]
    blocked_training = trainings.find_one({"_id": training_id_example_mock, "blocked": True})


    # Failure
    response = client.patch(
        f"/trainings/{training_id_example_mock}/block"
    )

    assert response.status_code == 400
    assert response.json() == f"Training {training_id_example_mock} is already blocked"

    training_id = str(ObjectId())
    response = client.patch(
        f"/trainings/{training_id}/block"
    )

    assert response.status_code == 404
    assert response.json() == f"Training {training_id} not found"


def test_unblock_status(mongo_mock):
    # Failure: unblock not blocked training
    response = client.patch(
        f"/trainings/{training_id_example_mock}/unblock"
    )

    assert response.status_code == 400
    assert response.json() == f"Training {training_id_example_mock} is not blocked"

    trainings = app.database["trainings"]
    blocked_training = trainings.find_one({"_id": training_id_example_mock, "blocked": False})

    # Success: unblock blocked training
    trainings.update_one({"_id": training_id_example_mock}, {"$set": {"blocked": True}})

    response = client.patch(
        f"/trainings/{training_id_example_mock}/unblock"
    )

    assert response.status_code == 200
    assert response.json() == f"Training {training_id_example_mock} successfully unblocked"

