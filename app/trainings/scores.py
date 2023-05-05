import logging
from bson import ObjectId
from fastapi import APIRouter, Depends, Request
from passlib.context import CryptContext
from starlette import status
from app.trainings.models import (
    ScoreRequest,
    ScoreResponse,
)
from app.trainings.object_id import ObjectIdPydantic
from starlette.responses import JSONResponse

from app.trainings.trainings_crud import get_user_id


logger = logging.getLogger('app')
router_scores = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router_scores.post(
    "/{training_id}/score",
    response_model=ScoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create my unique score qualitifation for training",
)
def add_score(
    request: Request,
    request_body: ScoreRequest,
    training_id: ObjectIdPydantic,
    id_user: ObjectId = Depends(get_user_id),
):
    trainings = request.app.database["trainings"]
    current_score = trainings.find_one(
        {"_id": training_id, "scores": {"$elemMatch": {"id_user": id_user}}},
        {"_id": 0, "scores.$": 1},
    )

    if current_score is None:
        score_json = request_body.encode_json_with(id_user)
        result = trainings.update_one(
            {"_id": training_id, "scores.id_user": {"$ne": id_user}},
            {"$push": {"scores": score_json}},
        )
        if result.modified_count == 1:
            request.app.logger.info(
                f'Score calification for user {id_user} created' +
                f'successfully on Training {training_id}'
            )
            return ScoreResponse.from_mongo(score_json)
        else:
            request.app.logger.info(
                f'Score calification for user {id_user} could not be' +
                f'created on Training {training_id}'
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=f'Score calification for user {id_user} ' +
                f'could not be created on Training {training_id}',
            )
    else:
        logger.info(
            f'Score calification for user {id_user} \
            already exist on Training {training_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=f'Score calification for {id_user} already' +
                f' exist on Training {training_id}',
        )


@router_scores.patch(
    "/{training_id}/score",
    status_code=status.HTTP_200_OK,
    summary="Modify my unique score qualitifation for an training",
)
def modify_score(
    request: Request,
    request_body: ScoreRequest,
    training_id: ObjectIdPydantic,
    id_user: ObjectId = Depends(get_user_id),
):
    trainings = request.app.database["trainings"]
    current_score = trainings.find_one(
        {"_id": training_id, "scores": {"$elemMatch": {"id_user": id_user}}},
        {"_id": 0, "scores.$": 1},
    )

    if current_score is None:
        logger.info(
            f'Score calification for {id_user} does not exist ' +
                f'on Training {training_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f'Score calification for {id_user} does not' +
                f' exist on Training {training_id}',
        )
    else:
        request_body = request_body.encode_json_with(id_user)
        result = trainings.update_one(
            {"_id": training_id, "scores.id_user": {"$eq": id_user}},
            {"$set": {"scores.$": request_body}},
        )
        if result.modified_count == 1:
            logger.info(
                f'Score calification for {id_user} updated' +
                f' successfully on Training {training_id}'
            )
            return ScoreResponse.from_mongo(request_body)
        else:
            logger.info(
                f'Score calification for {id_user} could not' +
                f' be updated on Training {training_id}'
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=f'Score calification for {id_user} could not' +
                f' be updated on Training {training_id}',
            )


@router_scores.delete(
    "/{training_id}/score",
    status_code=status.HTTP_200_OK,
    summary="Delete my unique score qualitifation for an training",
)
def delete_score(
    request: Request,
    training_id: ObjectIdPydantic,
    id_user: ObjectId = Depends(get_user_id),
):
    trainings = request.app.database["trainings"]
    result = trainings.update_one(
        {"_id": training_id}, {"$pull": {"scores": {"id_user": id_user}}}
    )

    if result.modified_count == 1:
        logger.info(
            f'Score calification of {id_user} deleted' +
                f' successfully on Training {training_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=f'Score calification of {id_user} deleted' +
                f' successfully on Training {training_id}',
        )
    else:
        logger.info(
            f'Score calification of User {id_user} not' +
                f' found on Training {training_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f'Score calification of User {id_user} not' +
                f' found on Training {training_id}',
        )
