import json
from typing import Optional
from bson import ObjectId
from fastapi import Query
from pydantic import BaseConfig, BaseModel, Field
from enum import Enum
from app.trainings.object_id import ObjectIdPydantic

########################################################################


class TrainingTypes(str, Enum):
    caminata = "Caminata"
    running = "Running"


class Difficulty(str, Enum):
    facil = "Fácil"
    intermedia = "Intermedia"
    dificil = "Difícil"


class MediaType(str, Enum):
    image = "image"
    video = "video"


class Media(BaseModel):
    media_type: MediaType
    url: str


class Qualification(BaseModel):
    id_user: ObjectIdPydantic
    score: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str]

class QualificationRequestPost(BaseModel):
    score: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str]

    def encode_json_with(self, id_user: ObjectId, exclude_none):
        """Encode the json to be inserted in MongoDB"""

        json = Qualification(
            id_user=ObjectIdPydantic(id_user),
            score=self.score,
            comment=self.comment,
        ).dict(exclude_none=exclude_none)

        return json
    

########################################################################

class TrainingRequestPost(BaseModel):
    title: str
    description: str
    type: TrainingTypes
    difficulty: Difficulty
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
    difficulty: Difficulty
    media: list[Media] = []
    qualification: list[Qualification] = []
    blocked: bool = False


class TrainingResponse(TrainingDatabase):
    class Config(BaseConfig):
        json_encoders = {ObjectId: lambda id: str(id)}  # convert ObjectId into str

    @classmethod
    def from_mongo(cls, training: dict):
        """We must convert _id into "id" and"""
        if not training:
            return training
        id = training.pop('_id', None)
        
        return cls(**dict(training, id=id))


class TrainingQueryParamsFilter(BaseModel):  # TODO: check param types
    type: TrainingTypes = Query(None, min_length=1, max_length=256)
    difficulty: Difficulty = Query(None, min_length=1, max_length=256)
    id_trainer: ObjectIdPydantic = Query(None)
