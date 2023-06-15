import httpx
from fastapi import HTTPException, status
from os import environ
import app.main as main


USER_SERVICE_URL = environ.get('USER_SERVICE_URL', 'http://user-microservice:7500')
GOALS_SERVICE_URL = environ.get('GOALS_SERVICE_URL', 'http://goals-microservice:7502')


class ServiceUsers:
    @staticmethod
    async def get(path):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{USER_SERVICE_URL}{path}")
                return response
        except Exception:
            main.logger.error('User service cannot be accessed')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='User service cannot be accessed',
            )


class ServiceGoals:
    @staticmethod
    async def post(path, json, headers):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{GOALS_SERVICE_URL}{path}",
                    json=json,
                    headers=headers,
                )
                return response
        except Exception:
            main.logger.error('Goals service cannot be accessed')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Goals service cannot be accessed',
            )

    @staticmethod
    async def patch(path, json, headers):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{GOALS_SERVICE_URL}{path}",
                    json=json,
                    headers=headers,
                )
                return response
        except Exception:
            main.logger.error('Goals service cannot be accessed')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Goals service cannot be accessed',
            )


# TRAINING_SERVICE_URL = environ.get(
#     'TRAINING_SERVICE_URL', 'http://training-microservice:7501'
# )
# TRAINING_HOST = TRAINING_SERVICE_URL.split('/')[2]
# ALLOWED_HOSTS = [
#     'localhost:3000',
#     'localhost:7500',
#     'localhost:7501',
#     'localhost:7502',
#     ServiceGoals.HOST,
#     TRAINING_HOST,
# ]
