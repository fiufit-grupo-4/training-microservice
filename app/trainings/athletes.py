import logging
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from passlib.context import CryptContext
from starlette import status
from typing import List, Optional
from app.services import ServiceGoals, ServiceUsers
from app.trainings.models import (
    StateTraining,
    TrainingQueryParamsFilter,
    TrainingResponse,
    UserRoles,
)
from app.trainings.object_id import ObjectIdPydantic
from starlette.responses import JSONResponse

from app.trainings.trainings_crud import get_user_id, get_user_role


logger = logging.getLogger('app')
router_athletes = APIRouter()


@router_athletes.patch('/{training_id}/start', status_code=status.HTTP_200_OK)
async def stop_training(
    request: Request,
    training_id: ObjectIdPydantic,
    id_user: ObjectId = Depends(get_user_id),
    role_user = Depends(get_user_role)
):
    if role_user != UserRoles.ATLETA:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not an ATHLETE to start a training",
        )
    trainings = request.app.database["trainings"]
    athletes_states = request.app.database["athletes_states"]
    training = trainings.find_one({"_id": training_id})
    
    if not training:
        logger.info(f"Training {training_id} does not exist")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f"Training {training_id} does not exist"
        )
            
    result_find = athletes_states.find_one({"user_id": ObjectId(id_user), "training_id": training_id})
    if result_find:
        state_saved = StateTraining(str(result_find["state"]))
        if state_saved == StateTraining.INIT or state_saved == StateTraining.COMPLETE:
            logger.info(f"Training {training_id} as {state_saved} state for athlete {id_user}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=f"Training {training_id} as {state_saved} state for athlete {id_user}",
            )
        else:
            result_update = athletes_states.update_one({"user_id": ObjectId(id_user), "training_id": training_id}, {"$set": {"state": StateTraining.INIT}})
            if result_update.matched_count == 1:
                logger.info(f"Training {training_id} as INIT for athlete {id_user} successfully")
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=f"Training {training_id} as INIT for athlete {id_user} successfully",
                )
            else:
                logger.info(f"Training {training_id} could not be STOPPED for athlete {id_user}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content=f"Training {training_id} could not be STOPPED for athlete {id_user}",
                )
    else:
        athletes_states.insert_one({"user_id": ObjectId(id_user), "training_id": training_id, "state": StateTraining.INIT})
        logger.info(f"Training {training_id} as INIT for athlete {id_user} successfully")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=f"Training {training_id} as INIT for athlete {id_user} successfully",
        )


@router_athletes.patch('/{training_id}/stop', status_code=status.HTTP_200_OK)
async def stop_training(
    request: Request,
    training_id: ObjectIdPydantic,
    id_user: ObjectId = Depends(get_user_id),
    role_user = Depends(get_user_role)
):
    if role_user != UserRoles.ATLETA:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not an ATHLETE to start a training",
        )
    trainings = request.app.database["trainings"]
    athletes_states = request.app.database["athletes_states"]
    training = trainings.find_one({"_id": training_id})
    if not training:
        logger.info(f"Training {training_id} does not exist")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f"Training {training_id} does not exist"
        )

    result_find = athletes_states.find_one({"user_id": ObjectId(id_user), "training_id": training_id})
    if not result_find:
        logger.info(f"Training {training_id} does not exist for athlete {id_user}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f"Training {training_id} does not exist for athlete {id_user}",
        )
        
    state_saved = StateTraining(str(result_find["state"]))
    if state_saved == StateTraining.NOT_INIT or state_saved == StateTraining.STOP or state_saved == StateTraining.COMPLETE:
        logger.info(f"Training {training_id} as {state_saved} state for athlete {id_user}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"Training {training_id} as {state_saved} state for athlete {id_user}",
        )
        
    result_update = athletes_states.update_one({"user_id": ObjectId(id_user), "training_id": training_id}, {"$set": {"state": StateTraining.STOP}})
    if result_update.matched_count == 1:
        logger.info(f"Training {training_id} as STOP state for athlete {id_user} successfully")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=f"Training {training_id} as STOP state for athlete {id_user} successfully",
        )
    else:
        logger.info(f"Training {training_id} could not be STOPPED for athlete {id_user}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"Training {training_id} could not be STOPPED for athlete {id_user}",
        )
    

@router_athletes.patch('/{training_id}/complete', status_code=status.HTTP_200_OK)
async def complete_training(
    request: Request,
    training_id: ObjectIdPydantic,
    id_user: ObjectId = Depends(get_user_id),
    role_user = Depends(get_user_role)
):
    if role_user != UserRoles.ATLETA:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not an ATHLETE to start a training",
        )
    trainings = request.app.database["trainings"]
    athletes_states = request.app.database["athletes_states"]
    training = trainings.find_one({"_id": training_id})
    if not training:
        logger.info(f"Training {training_id} does not exist")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f"Training {training_id} does not exist"
        )

    result_find = athletes_states.find_one({"user_id": ObjectId(id_user), "training_id": training_id})
    if not result_find:
        logger.info(f"Training {training_id} does not exist for athlete {id_user}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f"Training {training_id} does not exist for athlete {id_user}",
        )
        
    state_saved = StateTraining(str(result_find["state"]))
    if state_saved == StateTraining.NOT_INIT or state_saved == StateTraining.STOP or state_saved == StateTraining.COMPLETE:
        logger.info(f"Training {training_id} as {state_saved} state for athlete {id_user}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"Training {training_id} as {state_saved} state for athlete {id_user}",
        )
        
    result_update = athletes_states.update_one({"user_id": ObjectId(id_user), "training_id": training_id}, {"$set": {"state": StateTraining.COMPLETE}})
    if result_update.matched_count == 1:
        logger.info(f"Training {training_id} as COMPLETE state for athlete {id_user} successfully")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=f"Training {training_id} as COMPLETE state for athlete {id_user} successfully",
        )
    else:
        logger.info(f"Training {training_id} could not be COMPLETED for athlete {id_user}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"Training {training_id} could not be COMPLETED for athlete {id_user}",
        )