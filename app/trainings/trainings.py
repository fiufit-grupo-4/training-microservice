import logging
from bson import ObjectId
from fastapi import APIRouter, Depends, Query, Request
from passlib.context import CryptContext
from starlette import status
from typing import List, Optional
from app.trainings.models import (
    StateTraining,
    TrainingQueryParamsFilter,
    TrainingResponse,
    UserRoles,
)
from app.trainings.object_id import ObjectIdPydantic
from starlette.responses import JSONResponse

from app.trainings.trainings_crud import get_all_data_of_access_token


logger = logging.getLogger('app')
router_trainings = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def update_states_to_visualizate(training, athletes_states, request: Request):
    token = request.headers["authorization"].split(" ")[1]
    data = get_all_data_of_access_token(token)

    if UserRoles(data["role"]) != UserRoles.ATLETA:
        training["state"] = StateTraining.YOU_ARE_NOT_ATHLETE
    else:
        result = athletes_states.find_one(
            {"user_id": ObjectId(data["id"]), "training_id": training["_id"]}
        )
        if not result:
            training["state"] = StateTraining.NOT_INIT
        else:
            training["state"] = result["state"]


@router_trainings.get(
    '/',
    response_model=List[TrainingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all trainings. Include query params to filter",
)
async def get_trainings(
    request: Request,
    queries: TrainingQueryParamsFilter = Depends(),
    limit: int = Query(128, ge=1, le=1024),
    map_users: Optional[bool] = True,
    map_states: Optional[bool] = True,
):
    trainings = request.app.database["trainings"]

    trainings_list = []
    for training in trainings.find(queries.dict(exclude_none=True)).limit(limit):
        if map_states:
            update_states_to_visualizate(
                training, request.app.database["athletes_states"], request
            )
        if res := TrainingResponse.from_mongo(training):
            trainings_list.append(res)

    if map_users:
        await TrainingResponse.map_users(trainings_list)

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


@router_trainings.patch('/{training_id}/block', status_code=status.HTTP_200_OK)
def block_status(training_id: ObjectIdPydantic, request: Request):
    trainings = request.app.database["trainings"]
    training = trainings.find_one({"_id": training_id})

    if not training:
        request.app.logger.info(f'Training {training_id} not found to block')
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f'Training {training_id} not found',
        )

    if training["blocked"]:
        request.app.logger.info(f'Training {training_id} was already blocked!')
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"Training {training_id} is already blocked",
        )

    update_result = trainings.update_one(
        {"_id": training_id}, {"$set": {"blocked": True}}
    )

    if update_result.modified_count > 0:
        request.app.logger.info(f'Training {training_id} was successfully blocked')
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=f'Training {training_id} successfully blocked',
        )

    request.app.logger.info(f'Training {training_id} was not blocked')
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=f'Training {training_id} not blocked',
    )


@router_trainings.patch('/{training_id}/unblock', status_code=status.HTTP_200_OK)
def unblock_status(training_id: ObjectIdPydantic, request: Request):
    trainings = request.app.database["trainings"]
    training = trainings.find_one({"_id": training_id})

    if not training:
        request.app.logger.info(f'Training {training_id} not found to block')
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f'Training {training_id} not found',
        )

    if not training["blocked"]:
        request.app.logger.info(f'Training {training_id} was not blocked!')
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"Training {training_id} is not blocked",
        )

    update_result = trainings.update_one(
        {"_id": training_id}, {"$set": {"blocked": False}}
    )

    if update_result.modified_count > 0:
        request.app.logger.info(f'Training {training_id} was successfully unblocked')
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=f'Training {training_id} successfully unblocked',
        )
    request.app.logger.info(f'Training {training_id} was not unblocked')
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=f'Training {training_id} not unblocked',
    )


@router_trainings.get(
    "/{training_id}",
    response_model=TrainingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific training by training_id",
)
async def get_training_by_id(
    request: Request,
    training_id: ObjectIdPydantic,
    map_users: Optional[bool] = True,
    map_states: Optional[bool] = True,
):
    trainings = request.app.database["trainings"]

    training = trainings.find_one({"_id": training_id})

    if training is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f'Training {training_id} not found to get',
        )

    if map_states:
        update_states_to_visualizate(
            training, request.app.database["athletes_states"], request
        )
    if res := TrainingResponse.from_mongo(training):
        if map_users:
            await res.map_users([res])
        return res
    else:
        request.app.logger.error(f"Failed to search training {training_id}'")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f'Failed to search training {training_id}',
        )
