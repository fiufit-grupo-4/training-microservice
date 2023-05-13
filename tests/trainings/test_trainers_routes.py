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
    "comments": []
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


def test_post_training(mongo_mock):
    data = {
        "title": "B",
        "description": "BABA",
        "type": "Caminata",
        "difficulty": 1,
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
        "id_trainer": str(trainer_id_example_mock),
        "title": "B",
        "description": "BABA",
        "type": "Caminata",
        "difficulty": 1,
        "media": [],
        "blocked": False,
        "scores": [],
        "comments": []
    }


def test_update_training(mongo_mock):
    
    # Success
    update_data = {"title": "Test training name", "description": "Test description"}
    response = client.patch(f'/trainers/me/trainings/{training_id_example_mock}',
                            json=update_data,
                            headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    assert response.status_code == 200
    response_body = response.json()
    assert response_body == f'Training {training_id_example_mock} updated successfully'

    trainings = app.database.get_collection("trainings")

    training = trainings.find_one({"_id": training_id_example_mock})

    assert training['title'] == 'Test training name'
    assert training["description"] == "Test description"

    # Failure
    training_id = str(ObjectId())

    update_data = {"name": "Test training name", "description": "Test description"}
    response = client.patch(
        f"/trainers/me/trainings/{training_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {access_token_trainer_example}"}
    )
    response_body = response.json()
    assert response.status_code == 404
    assert response_body == f'Training {training_id} not found'


def test_delete_training(mongo_mock):
    # Success

    response = client.delete(f'/trainers/me/trainings/{training_id_example_mock}', headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    response_body = response.json()

    assert response.status_code == 200
    assert response_body == f'Training {training_id_example_mock} deleted successfully'

    trainings = app.database["trainings"]
    deleted_training = trainings.find_one({"_id": training_id_example_mock})
    assert deleted_training is None

    # Failure
    training_id = str(ObjectId())

    response = client.delete(f'/trainers/me/trainings/{training_id}', headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    response_body = response.json()

    assert response.status_code == 404
    assert response_body == f"Training {training_id} not found to delete"


def test_block_status(mongo_mock):
    # Success
    response = client.patch(
        f"/trainers/me/trainings/{training_id_example_mock}/block",
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )

    assert response.status_code == 200
    assert response.json() == f"Training {training_id_example_mock} successfully blocked"

    trainings = app.database["trainings"]
    blocked_training = trainings.find_one({"_id": training_id_example_mock, "blocked": True})


    # Failure
    response = client.patch(
        f"/trainers/me/trainings/{training_id_example_mock}/block",
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )

    assert response.status_code == 400
    assert response.json() == f"Training {training_id_example_mock} is already blocked"

    training_id = str(ObjectId())
    response = client.patch(
        f"/trainers/me/trainings/{training_id}/block",
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )

    assert response.status_code == 404
    assert response.json() == f"Training {training_id} not found"


def test_unblock_status(mongo_mock):
    # Failure: unblock not blocked training
    response = client.patch(
        f"/trainers/me/trainings/{training_id_example_mock}/unblock",
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )

    assert response.status_code == 400
    assert response.json() == f"Training {training_id_example_mock} is not blocked"

    trainings = app.database["trainings"]
    blocked_training = trainings.find_one({"_id": training_id_example_mock, "blocked": False})

    # Success: unblock blocked training
    trainings.update_one({"_id": training_id_example_mock}, {"$set": {"blocked": True}})
    response = client.patch(
        f"/trainers/me/trainings/{training_id_example_mock}/unblock",
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )

    assert response.status_code == 200
    assert response.json() == f"Training {training_id_example_mock} successfully unblocked"

