import httpx
from fastapi import HTTPException, status
from os import environ
import app.main as main

USER_SERVICE_URL = environ.get('USER_SERVICE_URL', 'http://user-microservice:7500')


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
