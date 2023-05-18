from typing import Optional
from bson import ObjectId
from fastapi import Query
from pydantic import BaseConfig, BaseModel, Field
from enum import Enum
from app.services import ServiceUsers
from app.trainings.object_id import ObjectIdPydantic
from app.trainings.user_small import UserResponseSmall

########################################################################


class TrainingTypes(str, Enum):
    caminata = "Caminata"
    running = "Running"


class MediaType(str, Enum):
    image = "image"
    video = "video"


class Media(BaseModel):
    media_type: MediaType = Field(None, example="image")
    url: str = Field(None, example="https://www.example.com/image.png")


########################################################################


class Score(BaseModel):
    id_user: ObjectIdPydantic
    qualification: int = Field(None, ge=1, le=5)


class ScoreRequest(BaseModel):
    qualification: int = Field(None, ge=1, le=5)

    def encode_json_with(self, id_user: ObjectId):
        """Encode the json to be inserted in MongoDB"""

        return {"id_user": id_user, "qualification": self.qualification}


class ScoreResponse(BaseModel):
    user: UserResponseSmall
    qualification: int = Field(None, ge=1, le=5)

    class Config(BaseConfig):
        json_encoders = {
            ObjectId: lambda id_user: str(id_user)
        }  # convert ObjectId into str

    @classmethod
    def from_mongo(cls, training: dict):
        """We must convert ObjectId(id_user) into ObjectIdPydantic(id_user)"""
        if not training:
            return training

        user = ServiceUsers.get(f'/users/{training["id_user"]}')

        if user.status_code == 200:
            user = user.json()

        else:
            return None

        training.pop("id_user")
        training["user"] = UserResponseSmall.from_mongo(user)
        return cls(**dict(training))


########################################################################


class Comment(BaseModel):
    id: ObjectIdPydantic = None
    id_user: ObjectIdPydantic
    detail: str = Field(None, min_length=1, max_length=256)


class CommentRequest(BaseModel):
    detail: str = Field(None, min_length=1, max_length=256)

    # random id
    def encode_json_with(self, id_user: ObjectId, id: ObjectId = None):
        """Encode the json to be inserted in MongoDB, with new ObjectId internally"""

        if id is None:
            id = ObjectId()
        return {"id": id, "id_user": id_user, "detail": self.detail}


class CommentResponse(BaseModel):
    id: ObjectIdPydantic
    user: UserResponseSmall
    detail: str = Field(None, min_length=1, max_length=256)

    class Config(BaseConfig):
        json_encoders = {ObjectId: lambda id: str(id)}  # convert ObjectId into str

    @classmethod
    def from_mongo(cls, training: dict):
        """We must convert ObjectId(id) into ObjectIdPydantic(id)"""
        if not training:
            return training

        user = ServiceUsers.get(f'/users/{training["id_user"]}')

        if user.status_code == 200:
            user = user.json()

        else:
            return None

        training.pop("id_user")
        training["user"] = UserResponseSmall.from_mongo(user)
        return cls(**dict(training))


########################################################################


class TrainingRequestPost(BaseModel):
    title: str
    description: str
    type: TrainingTypes
    difficulty: int = Field(None, ge=1, le=5)
    media: Optional[list[Media]]

    def encode_json_with(self, id_trainer: ObjectIdPydantic):
        """Encode the json to be inserted in MongoDB"""

        json = TrainingDatabase(
            id_trainer=id_trainer,
            title=self.title,
            description=self.description,
            type=self.type,
            difficulty=self.difficulty,
            media=self.media or [],
        ).dict()

        # the "TrainingDatabase" model has an "id" field that
        # is not needed to be created in MongoDB
        json.pop("id")
        return json


# Model of "Training" in MongoDB
class TrainingDatabase(BaseModel):
    id: ObjectIdPydantic = None
    id_trainer: ObjectIdPydantic
    title: str
    description: str
    type: TrainingTypes
    difficulty: int = Field(None, ge=1, le=5)
    media: list[Media] = []
    comments: list[Comment] = []
    scores: list[Score] = []
    blocked: bool = False


class TrainingResponse(BaseModel):
    id: ObjectIdPydantic = None
    trainer: UserResponseSmall
    title: str
    description: str
    type: TrainingTypes
    difficulty: int = Field(None, ge=1, le=5)
    media: list[Media] = []
    comments: list[CommentResponse] = []
    scores: list[ScoreResponse] = []
    blocked: bool = False

    class Config(BaseConfig):
        json_encoders = {ObjectId: lambda id: str(id)}  # convert ObjectId into str

    @classmethod
    def from_mongo(cls, training: dict):
        """We must convert _id into "id" and"""
        if not training:
            return training
        id_training = training.pop('_id', None)

        id_trainer = training.pop('id_trainer', None)
        result = UserResponseSmall.from_service(id_trainer, id_training)

        if not result:
            return None

        # idem with Comment y Score
        if training.get('comments'):
            comments = [
                CommentResponse.from_mongo(comment) for comment in training['comments']
            ]
            training['comments'] = comments

        if training.get('scores'):
            scores = [ScoreResponse.from_mongo(score) for score in training['scores']]
            training['scores'] = scores

        training['trainer'] = result.dict()

        return cls(**dict(training, id=id_training))


class UpdateTrainingRequest(BaseModel):
    title: Optional[str]
    description: Optional[str]
    type: Optional[TrainingTypes]
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    media: Optional[list[Media]]


class ScoreInt(int):
    score: int

    def __iter__(self):
        yield from {'scores.qualification': self.score}.items()


class TrainingQueryParamsFilter(BaseModel):  # TODO: check param types
    title: str = Query(None, min_length=1, max_length=256)
    description: str = Query(None, min_length=1, max_length=256)
    type: TrainingTypes = Query(None, min_length=1, max_length=256)
    difficulty: int = Query(None, ge=1, le=5)
    id_trainer: ObjectIdPydantic = Query(None)
    score: ScoreInt = Query(None, ge=1, le=5)

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        if data.get('score'):
            data['scores.qualification'] = data.pop('score')
        return data
