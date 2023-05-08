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
    UpdateTrainingRequest,
)

from fastapi import Depends, HTTPException, status
from starlette.responses import JSONResponse

from app.trainings.object_id import ObjectIdPydantic

router_trainers = APIRouter()


def get_user_id(token: str = Depends(JWTBearer())) -> ObjectId:
    """Get user id from the token"""

    try:
        token_data_trainer = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return ObjectId(token_data_trainer["id"])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token invalid!"
        )


@router_trainers.post(
    "/",
    response_model=TrainingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create training by me",
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


@router_trainers.get(
    "/",
    response_model=List[TrainingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all trainings created by me. Include query params to filter",
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


@router_trainers.patch('/{training_id}', status_code=status.HTTP_200_OK)
async def update_training(
    request: Request,
    training_id: ObjectIdPydantic,
    update_training_request: UpdateTrainingRequest,
    id_trainer: ObjectId = Depends(get_user_id),
):
    fields_to_change = update_training_request.dict(exclude_none=True)
    if not fields_to_change or len(fields_to_change) == 0:
        request.app.logger.info('No values especified in body to update')
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content='No values especified to update',
        )
    trainings = request.app.database["trainings"]
    training = trainings.find_one({"_id": training_id, "id_trainer": id_trainer})

    if not training:
        request.app.logger.info(f'Training {training_id} not found to update')
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f'Training {training_id} not found',
        )
    update_result = trainings.update_one(
        {"_id": training_id}, {"$set": fields_to_change}
    )
    if update_result.modified_count > 0:
        request.app.logger.info(
            f'Updating training {training_id} values {list(fields_to_change.keys())}'
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=f'Training {training_id} updated successfully',
        )
    request.app.logger.info(f'Training {training_id} was not updated')
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=f'Training {training_id} not updated',
    )


@router_trainers.delete("/{training_id}", status_code=status.HTTP_200_OK)
def delete_training(
    request: Request,
    training_id: ObjectIdPydantic,
    id_trainer: ObjectId = Depends(get_user_id),
):
    trainings = request.app.database["trainings"]
    result = trainings.delete_one({"_id": training_id})
    if result.deleted_count == 1:
        request.app.logger.info(f'Deleting training {training_id}')
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=f'Training {training_id} deleted successfully',
        )
    request.app.logger.info(f'Training {training_id} not found to delete')
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=f'Training {training_id} not found to delete',
    )
