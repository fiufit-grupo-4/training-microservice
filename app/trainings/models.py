import asyncio
from typing import Optional, Union
from bson import ObjectId
from fastapi import HTTPException, Query
from pydantic import BaseConfig, BaseModel, Field
from enum import Enum
from app.services import ServiceUsers
from app.trainings.object_id import ObjectIdPydantic
from app.trainings.user_small import UserResponseSmall
import app.main as main

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
    user: Union[UserResponseSmall, dict]
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

        id_user = training.pop("id_user")
        training["user"] = {"id": id_user}
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
    user: Union[UserResponseSmall, dict]
    detail: str = Field(None, min_length=1, max_length=256)

    class Config(BaseConfig):
        json_encoders = {ObjectId: lambda id: str(id)}  # convert ObjectId into str

    @classmethod
    def from_mongo(cls, training: dict):
        """We must convert ObjectId(id) into ObjectIdPydantic(id)"""
        if not training:
            return training

        id_user = training.pop("id_user")
        training["user"] = {"id": id_user}
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
    trainer: Union[UserResponseSmall, dict]
    title: str
    description: str
    type: TrainingTypes
    difficulty: int = Field(None, ge=1, le=5)
    media: list[Media] = []
    comments: list[Union[CommentResponse, dict]] = []
    scores: list[Union[ScoreResponse, dict]] = []
    blocked: bool = False

    class Config(BaseConfig):
        json_encoders = {ObjectId: lambda id: str(id)}  # convert ObjectId into str

    @staticmethod
    async def map_users(trainings_list):
        """Map "users IDs" to the "users data" of each training in the list.
        By example id_trainer, id_users of comments and id_users of scores."""

        users_tasks = TrainingResponse.prepare_user_tasks(trainings_list)

        main.app.logger.info(
            f'Waiting for {len(users_tasks)} \"GET /users/{{id_users}}\" requests'
        )

        # Wait in parallel for all the requests to finish!
        user_responses = await asyncio.gather(*users_tasks.values())

        users = TrainingResponse.reorganize_users(users_tasks, user_responses)

        TrainingResponse.convert_all_types_ids(trainings_list, users)

    @staticmethod
    def convert_all_types_ids(trainings_list, users):
        """With the users data, map all the ids users of each training in the list."""

        training_to_delete = []

        for training in trainings_list:
            trainings = main.app.database["trainings"]

            if users[str(training.trainer["id"])]:
                training.trainer = UserResponseSmall.from_mongo(
                    users[str(training.trainer["id"])].copy()
                )

                TrainingResponse.map_ids_users_of_comments(users, training, trainings)

                TrainingResponse.map_ids_users_of_scores(users, training, trainings)
            else:
                training_to_delete.append(training)

        for training in training_to_delete:
            main.app.logger.warning(
                f'DELETING TRAINING ID {training.id} BECAUSE TRAINER DOES NOT EXIST'
            )
            trainings.delete_one({"_id": training.id})
            trainings_list.remove(training)

    @staticmethod
    def map_ids_users_of_scores(users, training, trainings):
        new_elements = []
        for score in training.scores:
            if users[str(score.user["id"])]:
                score.user = UserResponseSmall.from_mongo(
                    users[str(score.user["id"])].copy()
                )
                new_elements.append(score)

            else:
                main.app.logger.warning(
                    f'DELETING SCORE OF USER ID {score.user["id"]} FROM'
                    + f'TRAINING ID {training.id} BECAUSE USER DOES NOT EXIST'
                )
                trainings.update_one(
                    {"_id": training.id},
                    {"$pull": {"scores": {"id_user": score.user["id"]}}},
                )

        training.scores = new_elements

    @staticmethod
    def map_ids_users_of_comments(users, training, trainings):
        new_elements = []

        for comment in training.comments:
            if users[str(comment.user["id"])]:
                comment.user = UserResponseSmall.from_mongo(
                    users[str(comment.user["id"])].copy()
                )
                new_elements.append(comment)

            else:
                main.app.logger.warning(
                    f'DELETING COMMENT ID {comment.id} FROM TRAINING'
                    + f'ID {training.id} BECAUSE USER DOES NOT EXIST'
                )
                trainings.update_one(
                    {"_id": training.id},
                    {"$pull": {"comments": {"id_user": comment.user["id"]}}},
                )

        training.comments = new_elements.copy()

    @staticmethod
    def reorganize_users(users_tasks, responses):
        """Reorganize the users in a dict with the id as key, and the user (obtained in
        the request) as value. If the user does not exist, the value assigned is None"""

        users = {}
        for id_user, user in zip(users_tasks.keys(), responses):
            if user.status_code == 200:
                users[id_user] = user.json()
            elif user.status_code == 404:
                main.app.logger.warning(f'User with id {id_user} not found')
                users[id_user] = None
            else:
                main.app.logger.error(
                    f'Error getting user: {user.status_code} {user.json()}'
                )
                raise HTTPException(
                    status_code=user.status_code,
                    detail='Error getting user for any training',
                )

        main.app.logger.info(
            f'Finished for {len(users_tasks)} \"GET /users/{{id_users}}\" requests'
        )

        return users

    @staticmethod
    def prepare_user_tasks(trainings_list):
        """Prepare the tasks (small threads) to get all uniques users of each training
        in the list (trainer, commenting users and scoring users).
        The tasks are stored in a dictionary where the key is the id of the user.
        All the tasks are created at the same time, but they are not executed until
        the "await" is called. Thanks to this, the requests are executed in parallel,
        and the time to get all the users is reduced."""

        users_tasks = {}
        for user in trainings_list:
            if str(user.trainer["id"]) not in users_tasks:
                users_tasks[str(user.trainer["id"])] = asyncio.create_task(
                    ServiceUsers.get(
                        f'/users/{user.trainer["id"]}' + '?map_trainings=false'
                    )
                )

            for comment in user.comments:
                if str(comment.user["id"]) not in users_tasks:
                    users_tasks[str(comment.user["id"])] = asyncio.create_task(
                        ServiceUsers.get(
                            f'/users/{comment.user["id"]}' + '?map_trainings=false'
                        )
                    )

            for score in user.scores:
                if str(score.user["id"]) not in users_tasks:
                    users_tasks[str(score.user["id"])] = asyncio.create_task(
                        ServiceUsers.get(
                            f'/users/{score.user["id"]}' + '?map_trainings=false'
                        )
                    )

        return users_tasks

    @classmethod
    def from_mongo(cls, training: dict):
        """We must convert _id into "id" and"""
        if not training:
            return training
        id_training = training.pop('_id', None)

        id_trainer = training.pop('id_trainer', None)

        if training.get('comments'):
            comments = [
                CommentResponse.from_mongo(comment) for comment in training['comments']
            ]
            training['comments'] = comments

        if training.get('scores'):
            scores = [ScoreResponse.from_mongo(score) for score in training['scores']]
            training['scores'] = scores

        training['trainer'] = {"id": str(id_trainer)}

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
