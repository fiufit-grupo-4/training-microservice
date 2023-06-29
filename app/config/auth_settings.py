import jwt
from passlib.context import CryptContext
from pydantic import BaseSettings
from datetime import datetime
from app.config.config import Settings
from app.trainings.models import UserRoles

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
app_settings = Settings()


class SettingsAuth(BaseSettings):
    def generate_token_with_role(id: str, role: UserRoles) -> str:
        utcnow = datetime.utcnow()
        expires = utcnow + app_settings.EXPIRES
        token_data = {"id": id, "exp": expires, "iat": utcnow, "role": role}
        token = jwt.encode(
            token_data,
            key=app_settings.JWT_SECRET,
            algorithm=app_settings.JWT_ALGORITHM,
        )
        return token

    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)
