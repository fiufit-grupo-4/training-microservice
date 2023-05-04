from typing import List
from bson import ObjectId
import jwt
from app.settings.auth_baerer import JWTBearer
from fastapi import APIRouter, Query, Request
from app.settings.auth_settings import JWT_SECRET
from app.trainings.models import (
    TrainingQueryParamsFilter,
    TrainingRequestPost,
    TrainingResponse,
)

from fastapi import Depends, HTTPException, status
from starlette.responses import JSONResponse

trainers_router = APIRouter()


def get_user_id(token: str = Depends(JWTBearer())) -> ObjectId:
    """Get trainer id from the token"""

    print(token)
    try:
        token_data_trainer = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return ObjectId(token_data_trainer["id"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token invalid!"
        )


@trainers_router.post(
    "/",
    response_model=TrainingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create training",
)
def add_training(
    request: Request,
    request_body: TrainingRequestPost,
    id_trainer: ObjectId = Depends(get_user_id),
):
    trainings = request.app.database["trainings"]

    training_json = request_body.encode_json_with(id_trainer)
    training_id = trainings.insert_one(training_json).inserted_id

    training_mongo = trainings.find_one({"_id": training_id})

    request.app.logger.info(f'New training {training_id} created.')

    return TrainingResponse.from_mongo(training_mongo)


@trainers_router.get(
    "/",
    response_model=List[TrainingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get trainings created by me",
)
def get_training_created(
    request: Request,
    queries: TrainingQueryParamsFilter = Depends(),
    id_trainer: ObjectId = Depends(get_user_id),
    limit: int = Query(128, ge=1, le=1024),
):
    trainings = request.app.database["trainings"]

    query = queries.dict(exclude_none=True)
    query["id_trainer"] = id_trainer

    trainings_list = []
    for training in trainings.find(query).limit(limit):
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
        + f'{query}'
    )
    return trainings_list

