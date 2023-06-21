from dotenv import load_dotenv
load_dotenv()
from bson import ObjectId
from requests.models import Response
import pytest

from app.services import ServiceUsers
from app.trainings.user_small import UserResponseSmall

trainer_id_example_mock = str(ObjectId())

async def mock_get(*args, **kwargs):
    if args[0] == "/users/123":
        response = Response()
        response.status_code = 200
        response.json = lambda: {"id" : trainer_id_example_mock, "name": "Juan", "lastname": "Perez"}
        return response
    
    response = Response()
    response.status_code = 500
    response.json = lambda: {"error": "Internal Server Error"}
    return response

@pytest.fixture()
def service_mock(monkeypatch):
    monkeypatch.setattr("app.services.ServiceUsers.get", mock_get)
    monkeypatch.setattr("app.trainings.models.ServiceUsers.get", mock_get)

@pytest.mark.asyncio
async def test_get_user(service_mock):
    assert (await ServiceUsers.get("/users/123")).json() == {"id" : trainer_id_example_mock, "name": "Juan", "lastname": "Perez"}

# @pytest.mark.asyncio 
# async def test_from_mongo(service_mock):
#     assert await UserResponseSmall.from_service("2323", "1231") == None