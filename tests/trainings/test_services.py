from bson import ObjectId
import mongomock
import pytest
from requests.models import Response
from fastapi.testclient import TestClient
from app.main import app, logger
from app.services import ServiceGoals, ServiceUsers
from app.config.auth_settings import SettingsAuth
from app.trainings.models import StateTraining, UserRoles
from starlette import status

client = TestClient(app)

trainer_id_example_mock = str(ObjectId())

training_example_mock = {
    "id_trainer": trainer_id_example_mock,
    "title": "A",
    "description": "string",
    "type": "Walking",
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
      "metric": "Calories",
      "quantity_steps": 100
    },    {
      "title": "B",
      "description": "B ASD",
      "metric": "steps",
      "quantity_steps": 13
    },
        {
      "title": "C",
      "description": "C ASD",
      "metric": "km",
      "quantity_steps": 32
    }]
}

access_token_trainer_example = SettingsAuth.generate_token_with_role(trainer_id_example_mock, UserRoles.TRAINER)

async def mock_get_user_service_ok(*args, **kwargs):
    response = Response()
    response.status_code = 200
    response.json = lambda: {"id" : trainer_id_example_mock, "name": "Juan", "lastname": "Perez"}
    return response


async def mock_get_user_service_err(*args, **kwargs):
    response = Response()
    response.status_code = 404
    response.json = lambda: {"error" : "error"}
    return response


async def mock_post_goals_service_ok(*args, **kwargs):
    response = Response()
    response.status_code = 200
    response.json = lambda: {"id" : trainer_id_example_mock, "name": "Juan", "lastname": "Perez"}
    return response


async def mock_post_goals_service_err(*args, **kwargs):
    response = Response()
    response.status_code = 404
    response.json = lambda: {"error" : "error"}
    return response


async def mock_patch_goals_service_ok(*args, **kwargs):
    response = Response()
    response.status_code = 200
    response.json = lambda: {"id" : trainer_id_example_mock, "name": "Juan", "lastname": "Perez"}
    return response


async def mock_patch_goals_service_err(*args, **kwargs):
    response = Response()
    response.status_code = 404
    response.json = lambda: {"error" : "error"}
    return response

    
@pytest.mark.asyncio
async def test_services_users_get(monkeypatch):
    monkeypatch.setattr("app.services.httpx.AsyncClient.get", mock_get_user_service_ok)

    response = await ServiceUsers.get("/users/5f9d7a7c6c6d6b4a1f3f1f1f")
    assert response.status_code == 200
    
@pytest.mark.asyncio
async def test_services_users_get_fail(monkeypatch):
    monkeypatch.setattr("app.services.httpx.AsyncClient.get", mock_get_user_service_err)
    
    try:
        response = await ServiceUsers.get("/users/5f9d7a7c6c6d6b4a1f3f1f1f")
    except Exception as e:
        assert e.status_code == 500
    
    
@pytest.mark.asyncio
async def test_goals_service_post(monkeypatch):
    monkeypatch.setattr("app.services.httpx.AsyncClient.post", mock_post_goals_service_ok)

    response = await ServiceGoals.post("/users/5f9d7a7c6c6d6b4a1f3f1f1f", {}, {})
    assert response.status_code == 200
    
@pytest.mark.asyncio
async def test_goals_service_post_fail(monkeypatch):
    monkeypatch.setattr("app.services.httpx.AsyncClient.post", mock_post_goals_service_err)
    
    try:
        response = await ServiceGoals.post("/users/5f9d7a7c6c6d6b4a1f3f1f1f", {}, {})
    except Exception as e:
        assert e.status_code == 500
    
    
@pytest.mark.asyncio
async def test_goals_service_patch(monkeypatch):
    monkeypatch.setattr("app.services.httpx.AsyncClient.patch", mock_patch_goals_service_ok)

    response = await ServiceGoals.patch("/users/5f9d7a7c6c6d6b4a1f3f1f1f", {}, {})
    assert response.status_code == 200
    
@pytest.mark.asyncio
async def test_goals_service_patch_fail(monkeypatch):
    monkeypatch.setattr("app.services.httpx.AsyncClient.patch", mock_patch_goals_service_err)
    
    try:
        response = await ServiceGoals.patch("/users/5f9d7a7c6c6d6b4a1f3f1f1f", {}, {})
    except Exception as e:
        assert e.status_code == 500
    