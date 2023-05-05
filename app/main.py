import pymongo
from fastapi import FastAPI
import logging
from logging.config import dictConfig
from .log_config import logconfig
from os import environ
from dotenv import load_dotenv
from app.trainings.routes import router
from app.trainings.trainers_routes import trainers_router


load_dotenv()

MONGODB_URI = environ["MONGODB_URI"]

dictConfig(logconfig)
app = FastAPI()
logger = logging.getLogger("app")


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
    # app.database.trainings.delete_many({})


@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()
    logger.info("Shutdown APP")


app.include_router(router, prefix="/trainings")
app.include_router(trainers_router, prefix="/trainers/me/trainings")
