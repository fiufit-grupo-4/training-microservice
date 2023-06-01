# import app.main as main
# from app.services import ServiceUsers
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
