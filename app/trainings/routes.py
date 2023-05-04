import logging
from bson import ObjectId
from fastapi import APIRouter, Depends, Query, Request
from passlib.context import CryptContext
from starlette import status
from typing import List
from app.trainings.models import Qualification, QualificationRequestPost, TrainingQueryParamsFilter, TrainingResponse
from app.trainings.object_id import ObjectIdPydantic
from starlette.responses import JSONResponse

from app.trainings.trainers_routes import get_user_id


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


@router.post(
    "/{training_id}/qualification/me",
   
    status_code=status.HTTP_201_CREATED,
    summary="Create me qualitifation for an training",
)
def add_qualification(
    request: Request,
    request_body: QualificationRequestPost,
    training_id: ObjectIdPydantic,
    id_user: ObjectId = Depends(get_user_id),
):
    trainings = request.app.database["trainings"]
    request.app.logger.info(f'id_user {id_user}')
    training_mongo = trainings.find_one({"_id": training_id})
    request.app.logger.info(f'a training!! {training_mongo}')
    
    current_qualification = trainings.find_one({"_id": training_id, "qualification": {"$elemMatch": {"id_user": id_user}}}, {"_id":0, "qualification.$": 1})
    request.app.logger.info(f'current_qualification {current_qualification}')
    if current_qualification is None:
        calification_json = request_body.encode_json_with(id_user, exclude_none=False)
        # if null array
        if training_mongo["qualification"] is None:
            print("entro")
            training_mongo["qualification"] = [calification_json]
            trainings.update_one({"_id": training_id}, {"$set": {"qualification": training_mongo["qualification"]}})
        else:
            result_update = trainings.update_one({"_id": training_id, "qualification.id_user": {"$ne": id_user}}, {"$push": {"qualification": calification_json}})
    else:
        request.app.logger.info(f'YA EXISTE UNA CALIFICACION PARA ESTE USUARIO EN ESTE ENTRENAMIENTO')
    
    return {}



@router.patch(
    "/{training_id}/qualification/me",
   
    status_code=status.HTTP_201_CREATED,
    summary="Modify me qualitifation for an training",
)
def add_qualification(
    request: Request,
    request_body: QualificationRequestPost,
    training_id: ObjectIdPydantic,
    id_user: ObjectId = Depends(get_user_id),
):
    trainings = request.app.database["trainings"]
    request.app.logger.info(f'id_user {id_user}')
    training_mongo = trainings.find_one({"_id": training_id})
    request.app.logger.info(f'a training!! {training_mongo}')
    
    current_qualification = trainings.find_one({"_id": training_id, "qualification": {"$elemMatch": {"id_user": id_user}}}, {"_id":0, "qualification.$": 1})
    request.app.logger.info(f'current_qualification {current_qualification}')
    if current_qualification is None:
        request.app.logger.info(f'NO EXISTE UNA CALIFICACION PARA ESTE USUARIO EN ESTE ENTRENAMIENTO')
    else:
        new_calification_json = request_body.encode_json_with(id_user, exclude_none=True)
        request.app.logger.info(f'new_calification_json: {new_calification_json}')
        current_qualification = current_qualification['qualification'][0]
        request.app.logger.info(f'current_qualification: {current_qualification}')
        ## update qualification
        current_qualification.update(new_calification_json)
        
        result_update = trainings.update_one(
                {'_id': training_id, 'qualification': {'$elemMatch': {'id_user': id_user}}},
                {'$set': {'qualification.$': current_qualification}}
            )
        request.app.logger.info(f'result_update: {result_update}')
    
    return {}

    

@router.delete(
    "/{training_id}/qualification/me",
    status_code=status.HTTP_201_CREATED,
    summary="Delete me qualitifation for an training",
)
def delete_qualification(
    request: Request,
    training_id: ObjectIdPydantic,
    id_user: ObjectId = Depends(get_user_id),
):
    trainings = request.app.database["trainings"]
    result = trainings.update_one({"_id": training_id}, {"$pull": {"qualification": {"id_user": id_user}}})

    if result.modified_count == 1:
        logger.info(f'Calification of {id_user} deleted successfully on Training {training_id}')
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=f'Calification of {id_user} deleted successfully on Training {training_id}',
        )
    else:
        logger.info(f'Calificacion of User {id_user} not found on Training {training_id}')
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f'Calificacion of User {id_user} not found on Training {training_id}',
        )
