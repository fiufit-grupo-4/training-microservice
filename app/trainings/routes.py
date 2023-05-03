import logging
from fastapi import APIRouter, Depends, Query, Request
from passlib.context import CryptContext
from starlette import status
from typing import List
from app.trainings.models import TrainingQueryParamsFilter, TrainingResponse
from app.trainings.object_id import ObjectIdPydantic
from starlette.responses import JSONResponse


logger = logging.getLogger('app')
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get('/', response_model=List[TrainingResponse], status_code=status.HTTP_200_OK)
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
            content=f'Trainings not found with' +
            'query params: {queries.dict(exclude_none=True)}',
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
    summary="Get a training by id",
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
