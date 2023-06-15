import asyncio
import logging
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status
from app.services import ServiceGoals
from app.trainings.models import (
    StateGoal,
    StateTraining,
    UserRoles,
)
from app.trainings.object_id import ObjectIdPydantic
from starlette.responses import JSONResponse

from app.trainings.trainings_crud import get_all_data_of_access_token
import time

logger = logging.getLogger('app')
router_athletes = APIRouter()


def restrict_access_goals_service(request: Request):
    logger.info("TODO! restrict access to endpoint of goals service")
    # logger.info(f"Headers: {request.headers}")
    # host_origin = request.headers.get("origin").split("//")[1]
    # logger.info(f"Host origin: {host_origin}")
    # if host_origin not in ServiceGoals.ALLOWED_HOSTS:
    #     logger.warning(f"Host {host_origin} not allowed to access this service")
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="You are not allowed to access this service",
    #     )


async def create_goal_started(training_id, goal, headers):
    result_goals = await ServiceGoals.post(
        "/goals/",
        json={
            "title": goal["title"],
            "description": goal["description"],
            "metric": goal["metric"],
            "quantity": goal["quantity"],
            "state": StateGoal.INIT,
            "training_id": str(training_id),
        },
        headers={"authorization": headers["authorization"]},
    )

    return {"status_code": result_goals.status_code, "body": result_goals.json()}


async def set_state(id_goal, headers, StateGoal):
    result = None
    if StateGoal == StateGoal.STOP:
        result = await ServiceGoals.patch(
            f"/goals/{id_goal}/stop",
            json={},
            headers={"authorization": headers["authorization"]},
        )
    elif StateGoal == StateGoal.INIT:
        result = await ServiceGoals.patch(
            f"/goals/{id_goal}/start",
            json={},
            headers={"authorization": headers["authorization"]},
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"State {StateGoal} is not valid",
        )

    return {"status_code": result.status_code, "body": result.json()}


@router_athletes.patch('/{training_id}/start', status_code=status.HTTP_200_OK)
async def start_training(
    request: Request,
    training_id: ObjectIdPydantic,
    data_access_token=Depends(get_all_data_of_access_token),
):

    if UserRoles(data_access_token["role"]) != UserRoles.ATLETA:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not an ATHLETE to start a training",
        )
    id_user = data_access_token["id"]
    trainings = request.app.database["trainings"]
    athletes_states = request.app.database["athletes_states"]
    training = trainings.find_one({"_id": training_id})

    if not training:
        logger.info(f"Training {training_id} does not exist")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f"Training {training_id} does not exist",
        )

    result_find = athletes_states.find_one(
        {"user_id": ObjectId(id_user), "training_id": training_id}
    )
    if result_find:
        state_saved = StateTraining(str(result_find["state"]))
        if state_saved == StateTraining.INIT or state_saved == StateTraining.COMPLETE:
            logger.info(
                f"Training {training_id} as {state_saved} state for athlete {id_user}"
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=f"Training {training_id} as {state_saved}"
                + f" state for athlete {id_user}",
            )
        else:
            result_update = athletes_states.update_one(
                {"user_id": ObjectId(id_user), "training_id": training_id},
                {"$set": {"state": StateTraining.INIT}},
            )
            if result_update.matched_count == 1:
                headers = request.headers
                init_responses = []
                for id_goal in result_find["goals"]:
                    goal = asyncio.create_task(
                        set_state(id_goal, headers, StateGoal.INIT)
                    )
                    init_responses.append(goal)

                init_responses = await asyncio.gather(*init_responses)

                if all(
                    goal["status_code"] == status.HTTP_200_OK for goal in init_responses
                ):
                    logger.info(
                        f"Training {training_id} as INIT state for"
                        + f" athlete {id_user} successfully"
                    )
                    return JSONResponse(
                        status_code=status.HTTP_200_OK,
                        content=f"Training {training_id} as INIT"
                        + f" for athlete {id_user} successfully",
                    )
                else:
                    athletes_states.update_one(
                        {"user_id": ObjectId(id_user), "training_id": training_id},
                        {"$set": {"state": state_saved}},
                    )

        logger.info(f"Training {training_id} could not be INIT for athlete {id_user}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"Training {training_id} could not"
            + f" be INIT for athlete {id_user}",
        )
    else:

        try:
            receta_goals = training["goals"]
            headers = request.headers
            goals_responses = []
            for receta in receta_goals:
                goal = asyncio.create_task(
                    create_goal_started(training_id, receta, headers)
                )
                goals_responses.append(goal)

            goals_responses = await asyncio.gather(*goals_responses)

            if all(
                goal["status_code"] == status.HTTP_200_OK for goal in goals_responses
            ):
                athletes_states.insert_one(
                    {
                        "user_id": ObjectId(id_user),
                        "training_id": training_id,
                        "state": StateTraining.INIT,
                        "goals": [
                            ObjectId(goal["body"]["id"]) for goal in goals_responses
                        ],
                    }
                )

                logger.info(
                    f"Training {training_id} as INIT for athlete {id_user} successfully"
                )
                logger.info("Goals created successfully in Goals Service")
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=f"Training {training_id} as INIT for"
                    + f" athlete {id_user} successfully",
                )
            else:
                raise Exception("Error creating goals in Goals Service")
        except Exception as e:
            logger.error(
                f"Goals of Training {training_id}"
                + " could not be created in"
                + " Goals Service."
                + f" Detail error: {e}"
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=f"Goals of Training {training_id} could not"
                + " be created in Goals Service",
            )


@router_athletes.patch('/{training_id}/stop', status_code=status.HTTP_200_OK)
async def stop_training(
    request: Request,
    training_id: ObjectIdPydantic,
    data_access_token=Depends(get_all_data_of_access_token),
):
    if UserRoles(data_access_token["role"]) != UserRoles.ATLETA:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not an ATHLETE to start a training",
        )
    id_user = data_access_token["id"]

    trainings = request.app.database["trainings"]
    athletes_states = request.app.database["athletes_states"]
    training = trainings.find_one({"_id": training_id})
    if not training:
        logger.info(f"Training {training_id} does not exist")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f"Training {training_id} does not exist",
        )

    result_find = athletes_states.find_one(
        {"user_id": ObjectId(id_user), "training_id": training_id}
    )
    if not result_find:
        logger.info(f"Training {training_id} does not exist for athlete {id_user}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f"Training {training_id} does not exist for athlete {id_user}",
        )

    state_saved = StateTraining(str(result_find["state"]))
    if (
        state_saved == StateTraining.NOT_INIT
        or state_saved == StateTraining.STOP
        or state_saved == StateTraining.COMPLETE
    ):
        logger.info(
            f"Training {training_id} as {state_saved} state for athlete {id_user}"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"Training {training_id} as {state_saved}"
            + f" state for athlete {id_user}",
        )

    old_state = result_find["state"]
    result_update = athletes_states.update_one(
        {"user_id": ObjectId(id_user), "training_id": training_id},
        {"$set": {"state": StateTraining.STOP}},
    )
    if result_update.matched_count == 1:
        headers = request.headers
        stop_responses = []
        for id_goal in result_find["goals"]:
            goal = asyncio.create_task(set_state(id_goal, headers, StateGoal.STOP))
            stop_responses.append(goal)

        stop_responses = await asyncio.gather(*stop_responses)

        if all(goal["status_code"] == status.HTTP_200_OK for goal in stop_responses):
            logger.info(
                f"Training {training_id} as STOP state for"
                + f" athlete {id_user} successfully"
            )
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=f"Training {training_id} as STOP"
                + f" state for athlete {id_user} successfully",
            )
        else:
            athletes_states.update_one(
                {"user_id": ObjectId(id_user), "training_id": training_id},
                {"$set": {"state": old_state}},
            )

    logger.info(f"Training {training_id} could not be STOPPED for athlete {id_user}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=f"Training {training_id} could not"
        + f" be STOPPED for athlete {id_user}",
    )


@router_athletes.patch(
    '/{training_id}/complete',
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(restrict_access_goals_service)],
)
async def complete_training(
    request: Request,
    training_id: ObjectIdPydantic,
    data_access_token=Depends(get_all_data_of_access_token),
):
    if UserRoles(data_access_token["role"]) != UserRoles.ATLETA:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not an ATHLETE to start a training",
        )
    id_user = data_access_token["id"]
    trainings = request.app.database["trainings"]
    athletes_states = request.app.database["athletes_states"]
    training = trainings.find_one({"_id": training_id})
    if not training:
        logger.info(f"Training {training_id} does not exist")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f"Training {training_id} does not exist",
        )

    result_find = athletes_states.find_one(
        {"user_id": ObjectId(id_user), "training_id": training_id}
    )
    if not result_find:
        logger.info(f"Training {training_id} does not exist for athlete {id_user}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=f"Training {training_id} does not exist for athlete {id_user}",
        )

    state_saved = StateTraining(str(result_find["state"]))
    if (
        state_saved == StateTraining.NOT_INIT
        or state_saved == StateTraining.STOP
        or state_saved == StateTraining.COMPLETE
    ):
        logger.info(
            f"Training {training_id} as {state_saved}" + f" state for athlete {id_user}"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"Training {training_id} as {state_saved}"
            + f" state for athlete {id_user}",
        )

    result_update = athletes_states.update_one(
        {"user_id": ObjectId(id_user), "training_id": training_id},
        {"$set": {"state": StateTraining.COMPLETE}},
    )
    if result_update.matched_count == 1:
        logger.info(
            f"Training {training_id} as COMPLETE state"
            + f" for athlete {id_user} successfully"
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=f"Training {training_id} as COMPLETE"
            + f" state for athlete {id_user} successfully",
        )
    else:
        logger.info(
            f"Training {training_id} could not be COMPLETED" + f" for athlete {id_user}"
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=f"Training {training_id} could not be"
            + f" COMPLETED for athlete {id_user}",
        )
