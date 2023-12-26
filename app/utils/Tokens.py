from datetime import datetime, timedelta
import jwt

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120


class ManageTokens():
    @staticmethod
    def create_access_token(data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token:str, exception):
        try:
            # Decode the token payload
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return payload["sub"]
        except jwt.ExpiredSignatureError:
            # Token has expired
            raise exception
        except jwt.InvalidTokenError:
            # Token is invalid
            raise exception
