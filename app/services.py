from fastapi import HTTPException
import requests
import app.main as main
from starlette import status
from os import environ

USER_SERVICE_URL = environ.get('USER_SERVICE_URL', 'http://user-microservice:7500')


class ServiceUsers:
    @staticmethod
    def get(path):
        try:
            result = requests.get(USER_SERVICE_URL + f'{path}')
            return result
        except Exception:
            main.logger.error('User service cannot be accessed')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='User service cannot be accessed',
            )
