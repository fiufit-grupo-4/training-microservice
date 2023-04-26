from typing import Optional
from bson import InvalidDocument, ObjectId
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

class Rating(BaseModel):
    score: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str]

########################################################################

class TrainingResponse(BaseModel):
    # TODO: add more fields
    id: ObjectIdPydantic
    title: Optional[str]
    description: Optional[str]

    def get_post_training(self, post_training):
        return PostTraining(self.title, self.description, self.id)

    class Config(BaseConfig):
        json_encoders = {ObjectId: lambda id: str(id)}  # convert ObjectId into str

    @classmethod
    def from_mongo(cls, training: dict):
        """We must convert _id into "id" and"""
        if not training:
            return training
        id = training.pop('_id', None)
        return cls(**dict(training, id=id))

class PostTraining(BaseModel):
    title: str
    description: str
    type: list[TrainingTypes]
    difficulty: list[TrainingTypes]
    media: Optional[list[Media]]
    blocked: Optional[bool]
    rating: Optional[Rating]

class TrainingQueryParamsFilter(BaseModel): #TODO: check param types
    type: str = Query(None, min_length=1, max_length=256)
    difficulty: str = Query(None, min_length=1, max_length=256)
