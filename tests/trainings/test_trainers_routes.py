from black import nullcontext
from bson import ObjectId
import mongomock
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.main import logger

from app.settings.auth_settings import Settings
from app.trainings.object_id import ObjectIdPydantic


client = TestClient(app)

trainer_id_example_mock = str(ObjectId())

training_example_mock = {
    "id_trainer": trainer_id_example_mock,
    "title": "A",
    "description": "string",
    "type": "Caminata",
    "difficulty": "Fácil",
    "media": [
        {"media_type": "image", "url": "chauuu.png"},
        {"media_type": "video", "url": "hola.mp4"},
    ],
    "blocked": None,
    "rating": None,
}


access_token_trainer_example = Settings.generate_token(trainer_id_example_mock)

# Mock MongoDB
@pytest.fixture()
def mongo_mock(monkeypatch):
    mongo_client = mongomock.MongoClient()
    db = mongo_client.get_database("training_microservice")
    col = db.get_collection("users")

    col.insert_one(training_example_mock)

    app.database = db
    app.logger = logger
    monkeypatch.setattr(app, "database", db)


def test_post_trainig(mongo_mock):
    data = {
        "title": "B",
        "description": "BABA",
        "type": "Caminata",
        "difficulty": "Fácil",
    }

    response = client.post(
        "trainers/me/trainings/",
        json=data,
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    response_body = response.json()
    response_body.pop("id")  # no me interesa el id del training en el test

    assert response.status_code == 201
    assert response_body == {
        "id_trainer": trainer_id_example_mock,
        "title": "B",
        "description": "BABA",
        "type": "Caminata",
        "difficulty": "Fácil",
        "media": None,
        "blocked": None,
        "rating": None,
    }
