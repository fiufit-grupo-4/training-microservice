from bson import ObjectId
import mongomock
import pytest
from fastapi.testclient import TestClient
from app.main import app, logger

from app.trainings.object_id import ObjectIdPydantic
from app.trainings.routes import router


client = TestClient(app)

trainer_id_example_mock = str(ObjectId())

training_example_mock = {
    "id_trainer": trainer_id_example_mock,
    "title": "A",
    "description": "string",
    "type": "Caminata",
    "difficulty": "Fácil",
    "media": [
        {"media_type": "image", "url": "chau.png"},
        {"media_type": "video", "url": "hola.mp4"},
    ],
    "blocked": None,
    "rating": None,
}


@pytest.fixture()
def mongo_mock(monkeypatch):
    mongo_client = mongomock.MongoClient()
    db = mongo_client.get_database("training_microservice")
    col = db.get_collection("trainings")
    col.insert_one(training_example_mock)

    app.database = db
    app.logger = logger
    monkeypatch.setattr(app, "database", db)


def test_get_trainings(mongo_mock):
    response = client.get("/trainings")
    assert response.status_code == 200

    response_body = response.json()

    assert all(item in response_body[0] for item in {
            'blocked': None,
            'description': 'string',
            'difficulty': 'Fácil',
            'media': [{'media_type': 'image', 'url': 'chau.png'},
                      {'media_type': 'video', 'url': 'hola.mp4'}],
            'rating': None,
            'title': 'A',
            'type': 'Caminata'
        }
    )
