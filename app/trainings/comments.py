import logging
from bson import ObjectId
from fastapi import APIRouter, Depends, Request
from passlib.context import CryptContext
from starlette import status
from app.trainings.models import (
    CommentRequest,
    CommentResponse,
)
from app.trainings.object_id import ObjectIdPydantic
from starlette.responses import JSONResponse

from app.trainings.trainings_crud import get_user_id


logger = logging.getLogger('app')
router_comments = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router_comments.post(
    "/{training_id}/comment",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create my comment for a training",
)
async def add_qualification_comment(
    request: Request,
    request_body: CommentRequest,
    training_id: ObjectIdPydantic,
    id_user: ObjectId = Depends(get_user_id),
):
    trainings = request.app.database["trainings"]
    comment_json = request_body.encode_json_with(id_user)

    result = trainings.update_one(
        {"_id": training_id}, {"$push": {"comments": comment_json}}
    )
    if result.modified_count == 1:
        logger.info(
            f'Comment of user {id_user} created successfully on Training {training_id}'
        )
        return await CommentResponse.from_mongo(comment_json)
    else:
        logger.info(
            f'Comment of user {id_user} could not be created on Training {training_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=f'Comment of user {id_user} could not be'
            + f'created on Training {training_id}',
        )


@router_comments.patch(
    "/{training_id}/comment/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
    summary="Modify my comment for a training",
)
async def modify_comment(
    request: Request,
    request_body: CommentRequest,
    training_id: ObjectIdPydantic,
    comment_id: ObjectIdPydantic,
    id_user: ObjectId = Depends(get_user_id),
):
    trainings = request.app.database["trainings"]
    result = trainings.update_one(
        {
            "_id": training_id,
            "comments": {"$elemMatch": {"id_user": id_user, "id": comment_id}},
        },
        {"$set": {"comments.$.detail": request_body.detail}},
    )
    if result.matched_count == 1:
        logger.info(
            f'Comment of user {id_user} modified successfully on Training {training_id}'
        )
        return await CommentResponse.from_mongo(
            request_body.encode_json_with(id_user, comment_id)
        )
    else:
        logger.info(
            f'Comment of user {id_user} could not be modified on Training {training_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=f'Comment of user {id_user} could not be modified'
            + f' on Training {training_id}',
        )


@router_comments.delete(
    "/{training_id}/comment/{comment_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete my comment for a training",
)
def delete_comment(
    request: Request,
    training_id: ObjectIdPydantic,
    comment_id: ObjectIdPydantic,
    id_user: ObjectId = Depends(get_user_id),
):
    trainings = request.app.database["trainings"]
    result = trainings.update_one(
        {"_id": training_id, "comments.id": comment_id, "comments.id_user": id_user},
        {"$pull": {"comments": {"id": comment_id}}},
    )

    if result.modified_count == 1:
        logger.info(
            f'Comment of user {id_user} deleted successfully on Training {training_id}'
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=f'Comment of user {id_user} deleted'
            + f' successfully on Training {training_id}',
        )
