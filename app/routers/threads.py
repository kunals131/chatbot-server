from fastapi import APIRouter, Depends, HTTPException, WebSocket
from app.services.oauth import get_current_user
from app.utils.Validators import AuthTokenData
from app.config.mongo_connection import get_db_instance
from pymongo.database import Database
from app.services.DialogFlow import ChatBot
from typing import Optional
from pydantic import BaseModel
from app.services.EngineersQuery import EngineersQuery, QueryModes
from app.utils.Helpers import Helpers
from bson import ObjectId  
import uuid
from datetime import datetime

router = APIRouter()
bot = ChatBot()
engineersDb = EngineersQuery()

class CreateThreadPayload(BaseModel):
    message:str
    sessionId: Optional[str]
    queryMode: Optional[str]

class UpdateThreadPayload(BaseModel):
    title:str

@router.get("/")
def get_threads(auth: AuthTokenData = Depends(get_current_user), db:Database = Depends(get_db_instance)):
    threads_collection = db["threads"]
    # print(auth)
    threads = list(threads_collection.find({"userId": auth['id']}).sort("updatedAt", -1))
    # print(threads)
    return {"threads": Helpers.parse_json(threads)}


@router.post("/message")
def send_message(payload:CreateThreadPayload, auth: AuthTokenData = Depends(get_current_user), db:Database = Depends(get_db_instance)):
    threads_collection = db["threads"]
    session_id = payload.sessionId
    isNewThread = False
    currentThread = {}
    if session_id and session_id != "":
        currentThread = threads_collection.find_one({"sessionId": payload.sessionId, "userId": auth['id']})
        if not currentThread:
            raise HTTPException(status_code=401, detail="Invalid session Id.")
    else:
        session_id = str(uuid.uuid4())
        isNewThread = True
        createdThread = threads_collection.insert_one({"userId": auth['id'], "sessionId": session_id, "messages": [], "title": "New Thread 1","updatedAt": datetime.utcnow().isoformat(), "createdAt": datetime.utcnow().isoformat()})
        currentThread['_id'] = createdThread.inserted_id

 
    messages_collection = db["messages"]
    botResponse = bot.interact(session_id=session_id, text=payload.message)
    botResponse['engineers'] = []
    additionalMsg = ""

    if Helpers.is_valid_dict(botResponse['entities']):
        botResponse['engineers'] = engineersDb.get_engineers(payload.message,botResponse['entities'], mode=payload.queryMode if payload.queryMode else QueryModes.PERCISE)
        if len(botResponse['engineers'].get('matches')) == 0:
            additionalMsg = Helpers.getRandomAdditionalMsgForEmptySuggestion()
        else:
            additionalMsg = Helpers.getRandomAdditionalMsgForSuggestion(isEmpty=False)


    message = {
        "userId": auth['id'],
        "message": payload.message,
        "response": additionalMsg + botResponse['response'],
        "intent": botResponse['intent'],
        "entities": botResponse['entities'],
        "sessionId": session_id,
        "suggestedResults": Helpers.parse_json(botResponse['engineers']),
        "threadId": str(currentThread["_id"]),
        "createdAt": datetime.utcnow().isoformat()
    }
    message = messages_collection.insert_one(message)
    threads_collection.update_one(
        {"_id": currentThread["_id"]},
        {"$push": {"messages": message.inserted_id}, "$set": {"updatedAt": datetime.utcnow().isoformat(), "lastMessage": payload.message}}
    )
    createdMessage = messages_collection.find_one({"_id": message.inserted_id})

    if isNewThread:
        currentThread = threads_collection.find_one({"_id": currentThread["_id"]})
    else:
        currentThread["lastMessage"] = payload.message
        currentThread["updatedAt"] = datetime.utcnow().isoformat()

    return {"success": True, "message": "Thread has been created successfully!","message": Helpers.parse_json(createdMessage), "isNewThread": isNewThread, "thread": Helpers.parse_json(currentThread)}

@router.get("/{thread_id}")
def get_thread(thread_id:str,auth: AuthTokenData = Depends(get_current_user), db:Database = Depends(get_db_instance)):
    message_collection = db["messages"]
    threads_collection = db["threads"]
    print(thread_id)
    thread = threads_collection.find_one({"_id": ObjectId(thread_id), "userId": auth['id']}, {'messages': 0})
    messages = message_collection.find({"threadId": thread_id, "userId": auth['id']})
    return {"messages": Helpers.parse_json(messages), "thread": Helpers.parse_json(thread)}


@router.delete("/all")
def delete_all_threads(auth: AuthTokenData = Depends(get_current_user), db:Database = Depends(get_db_instance)):
    threads_collection = db["threads"]
    messages_collection = db["messages"]
    messages_collection.delete_many({"userId": auth['id']})
    threads_collection.delete_many({"userId": auth['id']})
    return {"success": True, "message": "All threads have been deleted successfully!"}

@router.delete("/{thread_id}")
def delete_thread(thread_id:str,auth: AuthTokenData = Depends(get_current_user), db:Database = Depends(get_db_instance)):
    threads_collection = db["threads"]
    thread = threads_collection.find_one({"_id": thread_id})
    if thread["userId"] != auth['id']:
        raise HTTPException(status_code=401, detail="You are not authorized to delete this thread.")
    threads_collection.delete_one({"_id": thread_id})
    return {"success": True, "message": "Thread has been deleted successfully!"}



@router.put("/{thread_id}")
def update_thread(thread_id:str, payload:UpdateThreadPayload , auth: AuthTokenData = Depends(get_current_user), db:Database = Depends(get_db_instance)):
    threads_collection = db["threads"]
    print(thread_id)
    thread = threads_collection.find_one({"_id": ObjectId(thread_id)})
    # print(thread, auth['id'])
    if thread != None and str(thread["userId"]) != auth['id']:
        raise HTTPException(status_code=401, detail="You are not authorized to update this thread.")
        
    threads_collection.update_one({"_id": ObjectId(thread_id)}, {"$set": {"title": payload.title}})
    return {"success": True, "message": "Thread has been updated successfully!"}