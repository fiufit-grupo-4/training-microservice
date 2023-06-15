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
    "comments": [],
    "goals" : [    {
      "title": "A",
      "description": "A asd",
      "metric": "kcal",
      "quantity": 100
    },    {
      "title": "B",
      "description": "B ASD",
      "metric": "steps",
      "quantity": 13
    },
        {
      "title": "C",
      "description": "C ASD",
      "metric": "km",
      "quantity": 32
    }]
}

access_token_trainer_example = Settings.generate_token_with_role(trainer_id_example_mock, UserRoles.TRAINER)

async def mock_get(*args, **kwargs):
    response = Response()
    response.status_code = 200
    response.json = lambda: {"id" : trainer_id_example_mock, "name": "Juan", "lastname": "Perez"}
    return response


async def mock_post_goals(*args, **kwargs):
    response = Response()
    response.status_code = 200
    response.json = lambda: {
        "id": "648b817cff2cea65900751ee",
        "user_id": "5f9d7a7c6c6d6b4a1f3f1f1f",
        "title": "string",
        "description": "string",
        "metric": "string",
        "limit_time": "2023-06-15T21:24:11.479000+00:00",
        "state": 1,
        "list_multimedia": [],
        "quantity": 0,
        "progress": 0
        }
    return {"status_code": response.status_code, "body": response.json()}


async def mock_set_state(*args, **kwargs):
    response = Response()
    response.status_code = 200
    response.json = lambda: {
        "ok": "ok"
        }
    return {"status_code": response.status_code, "body": response.json()}

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
    monkeypatch.setattr("app.trainings.athletes.create_goal_started", mock_post_goals)
    monkeypatch.setattr("app.trainings.athletes.set_state", mock_set_state)


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
    
def test_get_trainings_as_athlete_registered_return_state_as_init(mongo_mock):
    athletes_states = app.database.get_collection("athletes_states")
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    id_training = response.json()[0]["id"]
    user_id = ObjectId("60b9b0a9d6b9a9b3f0a1a1a1")
    access_token_athlete_example = Settings.generate_token_with_role(str(user_id), UserRoles.ATLETA)
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.NOT_INIT.value
    
    athletes_states.insert_one({"user_id": user_id,
                            "training_id": ObjectId(id_training), 
                            "state": StateTraining.INIT.value,
                            "goals": [ObjectId("60b9b0a9d6b9a9b3f0a1a1a3"), 
                                        ObjectId("60b9b0a9d6b9a9b3f0a1a1a4")]})
    
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.INIT.value
    
    athletes_states.update_one({"user_id": user_id}, {"$set": {"state": StateTraining.STOP.value}})
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.STOP.value

    athletes_states.update_one({"user_id": user_id}, {"$set": {"state": StateTraining.COMPLETE.value}})
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.COMPLETE.value

def test_start_training_without_role_athlete_return_error(mongo_mock):
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    id_training = response.json()[0]["id"]
    
    response = client.patch(f"/athletes/me/trainings/{id_training}/start", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "You are not an ATHLETE to start a training"
    
def test_start_training_not_init_with_role_athlete_return_training_init_for_this_athlete(mongo_mock):
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    id_training = response.json()[0]["id"]
    
    user_id = ObjectId("60b9b0a9d6b9a9b3f0a1a1a1")
    access_token_athlete_example = Settings.generate_token_with_role(str(user_id), UserRoles.ATLETA)
    response = client.patch(f"/athletes/me/trainings/{id_training}/start", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_200_OK
    
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.INIT.value
    
    
def test_start_training_init_for_any_athlete_return_not_init_for_another_athlete(mongo_mock):
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    id_training = response.json()[0]["id"]
    
    user_id = ObjectId("60b9b0a9d6b9a9b3f0a1a1a1")
    access_token_athlete_example = Settings.generate_token_with_role(str(user_id), UserRoles.ATLETA)
    response = client.patch(f"/athletes/me/trainings/{id_training}/start", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_200_OK
    
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.INIT.value
    
    user_id_2 = ObjectId("60b9b0a9d6b9a9b3f0a1a1a2")
    access_token_athlete_example_2 = Settings.generate_token_with_role(str(user_id_2), UserRoles.ATLETA)
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example_2}"})
    assert response.json()[0]["state"] == StateTraining.NOT_INIT.value
    
def test_start_training_init_as_athlete_return_error(mongo_mock):
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    id_training = response.json()[0]["id"]
    user_id = ObjectId("60b9b0a9d6b9a9b3f0a1a1a1")
    access_token_athlete_example = Settings.generate_token_with_role(str(user_id), UserRoles.ATLETA)
    
    response = client.patch(f"/athletes/me/trainings/{id_training}/start", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_200_OK
    
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.INIT.value
    
    response = client.patch(f"/athletes/me/trainings/{id_training}/start", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_start_training_complete_as_athlete_return_error(mongo_mock):
    athletes_states = app.database.get_collection("athletes_states")
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    id_training = response.json()[0]["id"]
    user_id = ObjectId("60b9b0a9d6b9a9b3f0a1a1a1")
    access_token_athlete_example = Settings.generate_token_with_role(str(user_id), UserRoles.ATLETA)
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.NOT_INIT.value
    
    athletes_states.insert_one({"user_id": user_id,
                            "training_id": ObjectId(id_training), 
                            "state": StateTraining.COMPLETE.value,
                            "goals": [ObjectId("60b9b0a9d6b9a9b3f0a1a1a3"), 
                                        ObjectId("60b9b0a9d6b9a9b3f0a1a1a4")]})
    
    response = client.patch(f"/athletes/me/trainings/{id_training}/start", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.COMPLETE.value
    

def test_start_training_stopped_as_athlete_then_start_again(mongo_mock):
    athletes_states = app.database.get_collection("athletes_states")
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    id_training = response.json()[0]["id"]
    user_id = ObjectId("60b9b0a9d6b9a9b3f0a1a1a1")
    access_token_athlete_example = Settings.generate_token_with_role(str(user_id), UserRoles.ATLETA)
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.NOT_INIT.value
    
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.NOT_INIT.value
    
    athletes_states.insert_one({"user_id": user_id,
                            "training_id": ObjectId(id_training), 
                            "state": StateTraining.STOP.value,
                            "goals": [ObjectId("60b9b0a9d6b9a9b3f0a1a1a3"), 
                                        ObjectId("60b9b0a9d6b9a9b3f0a1a1a4")]})
    
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.STOP.value
    
    response = client.patch(f"/athletes/me/trainings/{id_training}/start", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_200_OK

    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.INIT.value
    

def test_start_training_inexistent_as_athlete_return_error(mongo_mock):
    user_id = ObjectId("60b9b0a9d6b9a9b3f0a1a1a1")
    access_token_athlete_example = Settings.generate_token_with_role(str(user_id), UserRoles.ATLETA)
    response = client.patch(f"/athletes/me/trainings/60b9b0a9d6b9a9b3f0a1a1a1/start", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_stop_training_inexistent_as_athlete_return_error(mongo_mock):
    user_id = ObjectId("60b9b0a9d6b9a9b3f0a1a1a1")
    access_token_athlete_example = Settings.generate_token_with_role(str(user_id), UserRoles.ATLETA)
    response = client.patch(f"/athletes/me/trainings/60b9b0a9d6b9a9b3f0a1a1a1/stop", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_stop_training_without_role_athlete_return_error(mongo_mock):
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    id_training = response.json()[0]["id"]
    
    response = client.patch(f"/athletes/me/trainings/{id_training}/stop", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "You are not an ATHLETE to start a training"
    
def test_stop_training_not_init_with_role_athlete_return_error(mongo_mock):
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    id_training = response.json()[0]["id"]
    
    user_id = ObjectId("60b9b0a9d6b9a9b3f0a1a1a1")
    access_token_athlete_example = Settings.generate_token_with_role(str(user_id), UserRoles.ATLETA)
    response = client.patch(f"/athletes/me/trainings/{id_training}/stop", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    
def test_stop_training_not_init_or_complete_or_stop_return_error(mongo_mock):
    athletes_states = app.database.get_collection("athletes_states")
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    id_training = response.json()[0]["id"]
    user_id = ObjectId("60b9b0a9d6b9a9b3f0a1a1a1")
    access_token_athlete_example = Settings.generate_token_with_role(str(user_id), UserRoles.ATLETA)
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.NOT_INIT.value
    
    athletes_states.insert_one({"user_id": user_id,
                            "training_id": ObjectId(id_training), 
                            "state": StateTraining.NOT_INIT.value,
                            "goals": [ObjectId("60b9b0a9d6b9a9b3f0a1a1a3"), 
                                        ObjectId("60b9b0a9d6b9a9b3f0a1a1a4")]})
    
    response = client.patch(f"/athletes/me/trainings/{id_training}/stop", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    athletes_states.update_one({"user_id": user_id}, {"$set": {"state": StateTraining.NOT_INIT.value}})
    response = client.patch(f"/athletes/me/trainings/{id_training}/stop", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    athletes_states.update_one({"user_id": user_id}, {"$set": {"state": StateTraining.STOP.value}})
    response = client.patch(f"/athletes/me/trainings/{id_training}/stop", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    athletes_states.update_one({"user_id": user_id}, {"$set": {"state": StateTraining.COMPLETE.value}})
    response = client.patch(f"/athletes/me/trainings/{id_training}/stop", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    

def test_stop_training_init_with_role_athlete_return_training_stopped_for_this_athlete(mongo_mock):
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    id_training = response.json()[0]["id"]

    user_id = ObjectId("60b9b0a9d6b9a9b3f0a1a1a1")
    access_token_athlete_example = Settings.generate_token_with_role(str(user_id), UserRoles.ATLETA)
    response = client.patch(f"/athletes/me/trainings/{id_training}/start", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_200_OK
    
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.INIT.value
    
    response = client.patch(f"/athletes/me/trainings/{id_training}/stop", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_200_OK
    
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.STOP.value

def test_complete_training_inexistent_as_athlete_return_error(mongo_mock):
    user_id = ObjectId("60b9b0a9d6b9a9b3f0a1a1a1")
    access_token_athlete_example = Settings.generate_token_with_role(str(user_id), UserRoles.ATLETA)
    response = client.patch(f"/athletes/me/trainings/60b9b0a9d6b9a9b3f0a1a1a1/complete", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_complete_training_inexistent_as_athlete_return_error(mongo_mock):
    user_id = ObjectId("60b9b0a9d6b9a9b3f0a1a1a1")
    access_token_athlete_example = Settings.generate_token_with_role(str(user_id), UserRoles.ATLETA)
    response = client.patch(f"/athletes/me/trainings/60b9b0a9d6b9a9b3f0a1a1a1/complete", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_complete_training_without_role_athlete_return_error(mongo_mock):
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    id_training = response.json()[0]["id"]
    
    response = client.patch(f"/athletes/me/trainings/{id_training}/complete", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "You are not an ATHLETE to start a training"


def test_complete_training_not_init_or_complete_or_stop_return_error(mongo_mock):
    athletes_states = app.database.get_collection("athletes_states")
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    id_training = response.json()[0]["id"]
    user_id = ObjectId("60b9b0a9d6b9a9b3f0a1a1a1")
    access_token_athlete_example = Settings.generate_token_with_role(str(user_id), UserRoles.ATLETA)
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.NOT_INIT.value
    
    athletes_states.insert_one({"user_id": user_id,
                            "training_id": ObjectId(id_training), 
                            "state": StateTraining.NOT_INIT.value,
                            "goals": [ObjectId("60b9b0a9d6b9a9b3f0a1a1a3"), 
                                        ObjectId("60b9b0a9d6b9a9b3f0a1a1a4")]})
    
    response = client.patch(f"/athletes/me/trainings/{id_training}/complete", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    athletes_states.update_one({"user_id": user_id}, {"$set": {"state": StateTraining.NOT_INIT.value}})
    response = client.patch(f"/athletes/me/trainings/{id_training}/complete", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    athletes_states.update_one({"user_id": user_id}, {"$set": {"state": StateTraining.STOP.value}})
    response = client.patch(f"/athletes/me/trainings/{id_training}/complete", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    athletes_states.update_one({"user_id": user_id}, {"$set": {"state": StateTraining.COMPLETE.value}})
    response = client.patch(f"/athletes/me/trainings/{id_training}/complete", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    

def test_complete_training_init_with_role_athlete_return_training_completed_for_this_athlete(mongo_mock):
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_trainer_example}"})
    id_training = response.json()[0]["id"]

    user_id = ObjectId("60b9b0a9d6b9a9b3f0a1a1a1")
    access_token_athlete_example = Settings.generate_token_with_role(str(user_id), UserRoles.ATLETA)
    response = client.patch(f"/athletes/me/trainings/{id_training}/start", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_200_OK
    
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.INIT.value
    
    response = client.patch(f"/athletes/me/trainings/{id_training}/complete", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.status_code == status.HTTP_200_OK
    
    response = client.get("/trainings", headers={"Authorization": f"Bearer {access_token_athlete_example}"})
    assert response.json()[0]["state"] == StateTraining.COMPLETE.value