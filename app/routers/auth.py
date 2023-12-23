from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from config.mongo_connection import get_db_instance
from pymongo.database import Database
from app.utils.Hash import Hash
from app.services.oauth import get_current_user
from app.utils.Tokens import ManageTokens
from app.utils.Validators import AuthTokenData
router = APIRouter()

class LoginPayload(BaseModel):
    username: str
    password: str

class RegisterPayload(BaseModel):
    username: str
    password: str
    confirm_password: str



@router.post("/login")
def login_user(body:LoginPayload, db:Database = Depends(get_db_instance)):
    users_collection= db["users"]
    username= body.username.lower()
    password = body.password
    user = users_collection.find_one({"username":username})
    print(user)
    token_data:AuthTokenData = {
        "username": username,
        "id": str(user["_id"])
    }
    if user:
        if Hash.verify(user["password"],password):
                access_token = ManageTokens.create_access_token(data={"sub": token_data})
                return {"token": access_token}
        else:
            raise HTTPException(status_code=401, detail="Login credentails are invalid.")
    else:
        raise HTTPException(status_code=401, detail="Login credentails are invalid.")


@router.post("/register")
def register_user(body:RegisterPayload, db:Database = Depends(get_db_instance)):
    users_collection= db["users"]
    username= body.username.lower()
    password = body.password
    confirm_password = body.confirm_password
    user = users_collection.find_one({"username":username})
    if user:
        raise HTTPException(status_code=401, detail="User already exists.")
    else:
        if password != confirm_password:
            raise HTTPException(status_code=401, detail="Passwords do not match.")
        else:
            password = Hash.bcrypt(password)
            users_collection.insert_one({"username":username,"password":password})
            return {"success": True, "message": "User has been registered successfully!"}

@router.get("/verify-auth")
def verify_auth(token_data: AuthTokenData = Depends(get_current_user)):
    return {"success": True, "message": "User is authenticated!", "data": token_data}