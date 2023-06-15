from bson import ObjectId
import mongomock
import pytest
from requests.models import Response
from fastapi.testclient import TestClient
from app.main import app, logger
from app.settings.auth_settings import Settings
from app.trainings.models import StateTraining, UserRoles
from starlette import status

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

access_token_trainer_example = Settings.generate_token_with_role(trainer_id_example_mock, UserRoles.TRAINER)

async def mock_get(*args, **kwargs):
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
    monkeypatch.setattr("app.trainings.models.ServiceUsers.get", mock_get)


def test_get_trainings_as_trainer_return_state_as_you_are_not_athlete(mongo_mock):
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["state"] == StateTraining.YOU_ARE_NOT_ATHLETE.value
    
def test_get_trainings_without_headers_with_map_states_return_state_as_you_are_not_athlete(mongo_mock):
    response = client.get("/trainings?map_states=false")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["state"] == StateTraining.YOU_ARE_NOT_ATHLETE.value

def test_get_trainings_without_headers_without_map_states_return_error(mongo_mock):
    response = client.get("/trainings")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
def test_get_trainings_as_athlete_return_state_as_not_init(mongo_mock):
    access_token_athlete_example = Settings.generate_token_with_role(str(ObjectId()), UserRoles.ATLETA)
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["state"] == StateTraining.NOT_INIT.value
    
def test_get_trainings_as_admin_return_state_as_not_init(mongo_mock):
    access_token_athlete_example = Settings.generate_token_with_role(str(ObjectId()), UserRoles.ADMIN)
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["state"] == StateTraining.YOU_ARE_NOT_ATHLETE.value