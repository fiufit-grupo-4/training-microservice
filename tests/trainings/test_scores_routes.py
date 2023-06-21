from dotenv import load_dotenv
load_dotenv()
from bson import ObjectId
from requests.models import Response
import mongomock
import pytest
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


def test_post_scores(mongo_mock):
    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert not training["scores"]
    
    training_id = training["id"]
    response = client.post(
        f"/trainings/{training_id}/score",
        json={"qualification": 5},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 201
    assert response.json().get("qualification") == 5

    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert training["scores"][0]["qualification"] == 5

def test_post_scores_invalid(mongo_mock):
    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert not training["scores"]
    
    training_id = training["id"]
    response = client.post(
        f"/trainings/{training_id}/score",
        json={"qualification": 6},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 422

    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert not training["scores"]
    
def test_post_scores_invalid_negative(mongo_mock):
    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert not training["scores"]
    
    training_id = training["id"]
    response = client.post(
        f"/trainings/{training_id}/score",
        json={"qualification": -1},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 422

    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert not training["scores"]
    
def test_post_scores_invalid_zero(mongo_mock):
    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert not training["scores"]
    
    training_id = training["id"]
    response = client.post(
        f"/trainings/{training_id}/score",
        json={"qualification": 0},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 422

    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert not training["scores"]
    
def test_post_score_its_unique_by_user(mongo_mock):
    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert not training["scores"]
    
    training_id = training["id"]
    response = client.post(
        f"/trainings/{training_id}/score",
        json={"qualification": 5},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 201
    assert response.json().get("qualification") == 5

    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert training["scores"][0]["qualification"] == 5

    response = client.post(
        f"/trainings/{training_id}/score",
        json={"qualification": 3},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 409

    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert training["scores"][0]["qualification"] == 5
    
def test_patch_score_success(mongo_mock):
    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert not training["scores"]
    
    training_id = training["id"]
    response = client.post(
        f"/trainings/{training_id}/score",
        json={"qualification": 5},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 201
    assert response.json().get("qualification") == 5

    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert training["scores"][0].get("qualification") == 5

    response = client.patch(
        f"/trainings/{training_id}/score",
        json={"qualification": 3},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 200

    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert training["scores"][0].get("qualification") == 3
    
def test_patch_score_invalids(mongo_mock):
    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert not training["scores"]
    
    training_id = training["id"]
    response = client.post(
        f"/trainings/{training_id}/score",
        json={"qualification": 5},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 201
    assert response.json().get("qualification") == 5

    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert training["scores"][0]["qualification"] == 5

    score_id = training["scores"][0]

    response = client.patch(
        f"/trainings/{training_id}/score",
        json={"qualification": 6},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 422

    response = client.patch(
        f"/trainings/{training_id}/score",
        json={"qualification": -1},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 422

    response = client.patch(
        f"/trainings/{training_id}/score",
        json={"qualification": 0},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 422

    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert training["scores"][0].get("qualification") == 5
    
def test_delete_score_success(mongo_mock):
    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert not training["scores"]
    
    training_id = training["id"]
    response = client.post(
        f"/trainings/{training_id}/score",
        json={"qualification": 5},
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 201
    assert response.json().get("qualification") == 5

    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    logger.warning(training)
    assert training["scores"][0]["qualification"] == 5

    response = client.delete(
        f"/trainings/{training_id}/score",
        headers={"Authorization": f"Bearer {access_token_trainer_example}"},
    )
    
    assert response.status_code == 200

    training = client.get("/trainings?map_users=false&map_states=false", json={"title": "A"}).json()[0]
    assert not training["scores"]