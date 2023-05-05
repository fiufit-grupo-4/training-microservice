import logging
from bson import ObjectId
from fastapi import APIRouter, Depends, Query, Request
from passlib.context import CryptContext
from starlette import status
from typing import List
from app.trainings.models import (
    CommentRequest,
    CommentResponse,
    ScoreRequest,
    ScoreResponse,
    TrainingQueryParamsFilter,
    TrainingResponse,
)
from app.trainings.object_id import ObjectIdPydantic
from starlette.responses import JSONResponse

from app.trainings.trainers_routes import get_user_id


logger = logging.getLogger('app')
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get(
    '/',
    response_model=List[TrainingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all trainings. Include query params to filter",
    tags=["General routes - Training microservice"],
)
async def get_trainings(
    request: Request,
    queries: TrainingQueryParamsFilter = Depends(),
    limit: int = Query(128, ge=1, le=1024),
):
    trainings = request.app.database["trainings"]

    trainings_list = []
    for training in trainings.find(queries.dict(exclude_none=True)).limit(limit):
        trainings_list.append(TrainingResponse.from_mongo(training))

    if len(trainings_list) == 0:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content='Trainings not found with'
            + f'query params: {queries.dict(exclude_none=True)}',
        )

    request.app.logger.info(
        f'Return list of {len(trainings_list)} trainings,'
        + ' with query params:'
        + f'{queries.dict(exclude_none=True)}'
    )
    return trainings_list


@router.get(
    "/{training_id}",
    response_model=TrainingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific training by training_id",
    tags=["General routes - Training microservice"],
)
def get_training_by_id(
    request: Request,
    training_id: ObjectIdPydantic,
):
    trainings = request.app.database["trainings"]

    training = trainings.find_one({"_id": training_id})

    if training is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f'Training {training_id} not found to get',
        )

    return TrainingResponse.from_mongo(training)


@router.post(
    "/{training_id}/score",
    response_model=ScoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create my unique score qualitifation for training",
    tags=["Scores - Training microservice"],
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
                f'Score calification for {id_user} created successfully on Training {training_id}'
            )
            return ScoreResponse.from_mongo(score_json)
        else:
            request.app.logger.info(
                f'Score calification for {id_user} could not be created on Training {training_id}'
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=f'Score calification for {id_user} could not be created on Training {training_id}',
            )
    else:
        logger.info(
            f'Score calification for {id_user} already exist on Training {training_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=f'Score calification for {id_user} already exist on Training {training_id}',
        )


@router.patch(
    "/{training_id}/score",
    status_code=status.HTTP_200_OK,
    summary="Modify my unique score qualitifation for an training",
    tags=["Scores - Training microservice"],
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
            f'Score calification for {id_user} does not exist on Training {training_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f'Score calification for {id_user} does not exist on Training {training_id}',
        )
    else:
        request_body = request_body.encode_json_with(id_user)
        result = trainings.update_one(
            {"_id": training_id, "scores.id_user": {"$eq": id_user}},
            {"$set": {"scores.$": request_body}},
        )
        if result.modified_count == 1:
            logger.info(
                f'Score calification for {id_user} updated successfully on Training {training_id}'
            )
            return ScoreResponse.from_mongo(request_body)
        else:
            logger.info(
                f'Score calification for {id_user} could not be updated on Training {training_id}'
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=f'Score calification for {id_user} could not be updated on Training {training_id}',
            )


@router.delete(
    "/{training_id}/score",
    status_code=status.HTTP_200_OK,
    summary="Delete my unique score qualitifation for an training",
    tags=["Scores - Training microservice"],
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
            f'Score calification of {id_user} deleted successfully on Training {training_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=f'Score calification of {id_user} deleted successfully on Training {training_id}',
        )
    else:
        logger.info(
            f'Score calification of User {id_user} not found on Training {training_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f'Score calification of User {id_user} not found on Training {training_id}',
        )


@router.post(
    "/{training_id}/comment",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create my comment for a training",
    tags=["Comments - Training microservice"],
)
def add_qualification_comment(
    request: Request,
    request_body: CommentRequest,
    training_id: ObjectIdPydantic,
    id_user: ObjectId = Depends(get_user_id),
):
    trainings = request.app.database["trainings"]
    comment_json = request_body.encode_json_with(id_user)

    result = trainings.update_one(
        {"_id": training_id}, {"$push": {"comments": comment_json}}
    )
    if result.modified_count == 1:
        logger.info(
            f'Comment of {id_user} created successfully on Training {training_id}'
        )
        return CommentResponse.from_mongo(comment_json)
    else:
        logger.info(
            f'Comment of {id_user} could not be created on Training {training_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=f'Comment of {id_user} could not be created on Training {training_id}',
        )


@router.patch(
    "/{training_id}/comment/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
    summary="Modify my comment for a training",
    tags=["Comments - Training microservice"],
)
def modify_comment(
    request: Request,
    request_body: CommentRequest,
    training_id: ObjectIdPydantic,
    comment_id: ObjectIdPydantic,
    id_user: ObjectId = Depends(get_user_id),
):
    trainings = request.app.database["trainings"]
    result = trainings.update_one(
        {
            "_id": training_id,
            "comments": {"$elemMatch": {"id_user": id_user, "id": comment_id}},
        },
        {"$set": {"comments.$.detail": request_body.detail}},
    )
    if result.matched_count == 1:
        logger.info(
            f'Comment of {id_user} modified successfully on Training {training_id}'
        )
        return CommentResponse.from_mongo(
            request_body.encode_json_with(id_user, comment_id)
        )
    else:
        logger.info(
            f'Comment of {id_user} could not be modified on Training {training_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=f'Comment of {id_user} could not be modified on Training {training_id}',
        )


@router.delete(
    "/{training_id}/comment/{comment_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete my comment for a training",
    tags=["Comments - Training microservice"],
)
def delete_comment(
    request: Request,
    training_id: ObjectIdPydantic,
    comment_id: ObjectIdPydantic,
    id_user: ObjectId = Depends(get_user_id),
):
    trainings = request.app.database["trainings"]
    result = trainings.update_one(
        {"_id": training_id, "comments.id": comment_id, "comments.id_user": id_user},
        {"$pull": {"comments": {"id": comment_id}}},
    )

    if result.modified_count == 1:
        logger.info(
            f'Comment of {id_user} deleted successfully on Training {training_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=f'Comment of {id_user} deleted successfully on Training {training_id}',
        )
