import app.main as main
from app.services import ServiceUsers
from bson import ObjectId
from pydantic import BaseConfig, BaseModel
from app.trainings.object_id import ObjectIdPydantic


class UserResponseSmall(BaseModel):
    id: ObjectIdPydantic
    name: str
    lastname: str

    class Config(BaseConfig):
        json_encoders = {ObjectId: lambda id: str(id)}  # convert ObjectId into str

    @classmethod
    def from_mongo(cls, user: dict):
        if not user:
            return user

        id_user = user.pop('id', None)

        return cls(**dict(id=id_user, **user))

    @classmethod
    def from_service(cls, id_user, id_training):
        user = ServiceUsers.get(f'/users/{id_user}')

        if user.status_code == 200:
            user = user.json()
            return UserResponseSmall.from_mongo(user)
        elif user.status_code == 404:
            trainings = main.app.database["trainings"]
            trainings.delete_one({"_id": ObjectId(id_training)})
            return None
        else:
            return None
