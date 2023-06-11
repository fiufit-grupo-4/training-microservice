import asyncio
import pymongo
from fastapi import FastAPI, Request
import logging
from logging.config import dictConfig
from .log_config import logconfig
from os import environ
from dotenv import load_dotenv
from app.publisher.publisher_queue import runPublisherManager
from app.publisher.publisher_queue_middleware import PublisherQueueEventMiddleware
from app.trainings.trainings import router_trainings
from app.trainings.trainings_crud import router_trainers
from app.trainings.scores import router_scores
from app.trainings.comments import router_comments


load_dotenv()

MONGODB_URI = environ["MONGODB_URI"]

dictConfig(logconfig)
app = FastAPI()
logger = logging.getLogger("app")

app.add_middleware(PublisherQueueEventMiddleware)


@app.on_event("startup")
async def startup_db_client():
    try:
        app.mongodb_client = pymongo.MongoClient(MONGODB_URI)
        logger.info("Connected successfully MongoDB")

    except Exception as e:
        logger.error(e)
        logger.error("Could not connect to MongoDB")

    app.logger = logger

    app.database = app.mongodb_client["training_microservice"]
    app.task_publisher_manager = asyncio.create_task(runPublisherManager())
    # app.database.trainings.delete_many({})


@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()
    app.task_publisher_manager.cancel()
    logger.info("Shutdown app")


app.include_router(
    router_trainings,
    prefix="/trainings",
    tags=["General routes - Training microservice"],
)
app.include_router(
    router_trainers,
    prefix="/trainers/me/trainings",
    tags=["CRUD for Trainers - Training microservice"],
)
app.include_router(
    router_scores, prefix="/trainings", tags=["Scores - Training microservice"]
)
app.include_router(
    router_comments, prefix="/trainings", tags=["Comments - Training microservice"]
)
