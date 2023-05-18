from bson import ObjectId
from fastapi import Response
from app.trainings.user_small import UserResponseSmall

def mock_get_other(*args, **kwargs):
    response = Response()
    response.status_code = 500
    response.json = lambda: {"error": "Internal Server Error"}
    return response

def mock_get_200(*args, **kwargs):
    # args[0] tiene "/users/id"
    id = args[0].split("/")[-1]
    response = Response()
    response.status_code = 200
    response.json = lambda: {"id" : id, "name": "Juan", "lastname": "Perez"}
    return response

def mock_get_404(*args, **kwargs):
    response = Response()
    response.status_code = 404
    response.json = lambda: {"error": "Not Found"}
    return response


def test_none_user_small():
    assert UserResponseSmall.from_mongo({}) == {}

def test_404_user_small(monkeypatch):
    monkeypatch.setattr("app.services.ServiceUsers.get", mock_get_404)
    res = UserResponseSmall.from_service(str(ObjectId()), str(ObjectId()))
    assert res == None

def test_200_user_small(monkeypatch):
    monkeypatch.setattr("app.services.ServiceUsers.get", mock_get_200)
    id = str(ObjectId())
    res = UserResponseSmall.from_service(id, id)
    res = res.dict()
    res.pop("id", None)
    assert res == {"name": "Juan", "lastname": "Perez"}

def test_other_code_status_user_small(monkeypatch):
    monkeypatch.setattr("app.services.ServiceUsers.get", mock_get_other)
    res = UserResponseSmall.from_service("123", "1231") 
    assert res == None
