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
    "blocked": False,
    "scores": [],
    "comments": []
}


access_token_trainer_example = Settings.generate_token(trainer_id_example_mock)


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


def test_post_training(mongo_mock):
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
    # we don't want to check the training id at the test
    response_body.pop("id")

    assert response.status_code == 201
    assert response_body == {
        "id_trainer": trainer_id_example_mock,
        "title": "B",
        "description": "BABA",
        "type": "Caminata",
        "difficulty": "Fácil",
        "media": [],
        "blocked": False,
        "scores": [],
        "comments": []
    }

#@patch('app.trainings.crud.get_database')
def test_delete_training(mongo_mock):

    # Success
    training_id = training_id_example_mock
    app.logger.warning(training_id)
    a = client.get("/trainings")
    app.logger.warning(a.json())
    # Call the API to delete the training
    response = client.delete(f'/trainers/me/trainings/{training_id}', headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    response_body = response.json()
    # Check the response
    assert response.status_code == 200
    assert response_body == f'Training {training_id} deleted successfully'


    # Failure
    training_id = str(ObjectId())
    app.logger.warning(training_id)
    response = client.delete(f'/trainers/me/trainings/{training_id}', headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    response_body = response.json()
    assert response.status_code == 404
    assert response_body == f"Training {training_id} not found to delete"
