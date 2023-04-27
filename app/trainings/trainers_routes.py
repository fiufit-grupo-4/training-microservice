import jwt
from http.client import HTTPException
from app.settings.auth_baerer import JWTBearer
from app.trainings.object_id import ObjectIdPydantic
from fastapi import APIRouter, Depends, Request
from starlette import status
from app.settings.auth_settings import JWT_SECRET
from app.trainings.models import TrainingRequestPost, TrainingResponse
from fastapi import Depends, HTTPException, status

trainers_router = APIRouter()


def get_trainer_id(token: str = Depends(JWTBearer())):
    """Get trainer id from the token"""

    try:
        token_data_trainer = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return token_data_trainer["id"]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token invalid!"
        )


@trainers_router.post(
    "/", response_model=TrainingResponse, status_code=status.HTTP_201_CREATED
)
def add_training(
    request: Request,
    request_body: TrainingRequestPost,
    id_trainer: ObjectIdPydantic = Depends(get_trainer_id),
):
    trainings = request.app.database["trainings"]

    training_json = request_body.encode_json_with(id_trainer)
    training_id = trainings.insert_one(training_json).inserted_id

    training_mongo = trainings.find_one({"_id": training_id})
    return TrainingResponse.from_mongo(training_mongo)
