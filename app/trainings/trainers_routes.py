import logging
import jwt
from bson import ObjectId
from fastapi import APIRouter, Depends, Query, Request
from fastapi.encoders import jsonable_encoder
from passlib.context import CryptContext
from starlette import status
from starlette.responses import JSONResponse
from typing import List
from app.settings.auth_settings import JWT_SECRET, JWT_ALGORITHM
from app.trainings.models import PostTraining, TrainingResponse


logger = logging.getLogger('app')
trainers_router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@trainers_router.post("/", response_model=TrainingResponse, status_code=status.HTTP_201_CREATED)
def add_training(request: Request, add_training_request: PostTraining):

    token = request.headers.get("Authorization")

    if token:
        token = token.split(" ")[1]
        request.app.logger.info(f"Token found: {token}")
    else:
        request.app.logger.info(f"No token found!")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content="No token found!",
        )

    try:
        token_data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception as e:
        request.app.logger.info(f"Invalid decode for token: {token}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, #TODO: choose status code
            content=e, # TODO: write an error message
        )

    trainings = request.app.database["trainings"]
    training_json = jsonable_encoder(add_training_request)
    training_json["trainer_id"] = token_data["id"]
    training_id = trainings.insert_one(training_json).inserted_id

    request.app.logger.info(
        f"Training {TrainingResponse(id=str(training_id))} successfully created"
    )
    return TrainingResponse(id=str(training_id))