import logging
from fastapi import APIRouter, Depends, Query, Request
from passlib.context import CryptContext
from starlette import status
from typing import List
from app.trainings.models import TrainingQueryParamsFilter, TrainingResponse


logger = logging.getLogger('app')
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get('/', response_model=List[TrainingResponse], status_code=status.HTTP_200_OK)
async def get_users(
    request: Request,
    queries: TrainingQueryParamsFilter = Depends(),
    limit: int = Query(128, ge=1, le=1024),
):
    trainings = request.app.database["trainings"]

    trainings_list = []
    for training in trainings.find(queries.dict(exclude_none=True)).limit(limit):
        request.app.logger.error(training)
        trainings_list.append(TrainingResponse.from_mongo(training))

    request.app.logger.info(
        f'Return list of {len(trainings_list)} trainings,'
        + ' with query params: {queries.dict(exclude_none=True)}'
    )
    return trainings_list
