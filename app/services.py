import httpx
from fastapi import HTTPException, status
from app.config.config import Settings
import app.main as main

app_settings = Settings()


class ServiceUsers:
    @staticmethod
    async def get(path):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{app_settings.USER_SERVICE_URL}{path}")
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
                    f"{app_settings.GOALS_SERVICE_URL}{path}",
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
                    f"{app_settings.GOALS_SERVICE_URL}{path}",
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
