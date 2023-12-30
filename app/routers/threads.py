from fastapi import APIRouter, Depends, HTTPException
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
    try:
        threads_collection = db["threads"]
        # print(auth)
        threads = list(threads_collection.find({"userId": auth['id']}).sort("updatedAt", -1))
        # print(threads)
        return {"threads": Helpers.parse_json(threads)}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something went wrong!")


@router.post("/message")
def send_message(payload:CreateThreadPayload, auth: AuthTokenData = Depends(get_current_user), db:Database = Depends(get_db_instance)):
    try:
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

        print('Mark - 0')
 
        messages_collection = db["messages"]
        botResponse = bot.interact(session_id=session_id, text=payload.message)
        botResponse['engineers'] = []
        print('Mark - 1')

        if Helpers.is_valid_dict(botResponse['entities']) or botResponse['intent'] == 'Hire Engineer':
            botResponse['engineers'] = engineersDb.get_engineers(payload.message,botResponse['entities'], mode=payload.queryMode if payload.queryMode else QueryModes.PERCISE)
        print('Mark - 2')


        message = {
            "userId": auth['id'],
            "message": payload.message,
            "response": botResponse['response'],
            "intent": botResponse['intent'],
            "entities": botResponse['entities'],
            "sessionId": session_id,
            "suggestedResults": Helpers.parse_json(botResponse['engineers']),
            "threadId": str(currentThread["_id"]),
            "createdAt": datetime.utcnow().isoformat()
        }
        print('Mark - 3')
        print(message)

        message = messages_collection.insert_one(Helpers.parse_json(message))

        print('Mark - 4')

        threads_collection.update_one(
            {"_id": currentThread["_id"]},
            {"$push": {"messages": message.inserted_id}, "$set": {"updatedAt": datetime.utcnow().isoformat(), "lastMessage": payload.message}}
        )
        print('Mark - 5')

        createdMessage = messages_collection.find_one({"_id": message.inserted_id})
        print(createdMessage)
        print('Mark - 6')
        
        if createdMessage["suggestedResults"]:
            createdMessage["populatedResults"] = engineersDb.get_engineer_details(createdMessage["suggestedResults"])
        print('Mark - 7')

        if isNewThread:
            currentThread = threads_collection.find_one({"_id": currentThread["_id"]})
        else:
            currentThread["lastMessage"] = payload.message
            currentThread["updatedAt"] = datetime.utcnow().isoformat()
        print('Mark - 8')


        return {"success": True, "message": "Thread has been created successfully!","message": Helpers.parse_json(createdMessage), "isNewThread": isNewThread, "thread": Helpers.parse_json(currentThread)}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something went wrong!")

@router.get("/{thread_id}")
def get_thread(thread_id:str,auth: AuthTokenData = Depends(get_current_user), db:Database = Depends(get_db_instance)):
    try:
        message_collection = db["messages"]
        threads_collection = db["threads"]
        print(thread_id)
        thread = threads_collection.find_one({"_id": ObjectId(thread_id), "userId": auth['id']}, {'messages': 0})
        messages = message_collection.find({"threadId": thread_id, "userId": auth['id']})
        messages = list(messages)
        if len(messages)>0 and messages[len(messages)-1]["suggestedResults"]:
            messages[len(messages)-1]["populatedResults"] = engineersDb.get_engineer_details(messages[len(messages)-1]["suggestedResults"])
        return {"messages": Helpers.parse_json(messages), "thread": Helpers.parse_json(thread)}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something went wrong!")

@router.get("/message/{message_id}")
def get_message_details(message_id:str,auth: AuthTokenData = Depends(get_current_user), db:Database = Depends(get_db_instance)):
    try:
        message_collection = db["messages"]
        message = message_collection.find_one({"_id": ObjectId(message_id), "userId": auth['id']})
        message["populatedResults"] = engineersDb.get_engineer_details(message["suggestedResults"])
        return {"message": Helpers.parse_json(message)}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something went wrong!")


@router.delete("/all")
def delete_all_threads(auth: AuthTokenData = Depends(get_current_user), db:Database = Depends(get_db_instance)):
    try:
        threads_collection = db["threads"]
        messages_collection = db["messages"]
        messages_collection.delete_many({"userId": auth['id']})
        threads_collection.delete_many({"userId": auth['id']})
        return {"success": True, "message": "All threads have been deleted successfully!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something went wrong!")

@router.delete("/{thread_id}")
def delete_thread(thread_id:str,auth: AuthTokenData = Depends(get_current_user), db:Database = Depends(get_db_instance)):
    try:
        threads_collection = db["threads"]
        thread = threads_collection.find_one({"_id": ObjectId(thread_id)})
        if thread["userId"] != auth['id']:
            raise HTTPException(status_code=401, detail="You are not authorized to delete this thread.")
        messages_collection = db["messages"]
        messages_collection.delete_many({"threadId": thread_id})
        threads_collection.delete_one({"_id": ObjectId(thread_id)})
        return {"success": True, "message": "Thread has been deleted successfully!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something went wrong!")



@router.put("/{thread_id}")
def update_thread(thread_id:str, payload:UpdateThreadPayload , auth: AuthTokenData = Depends(get_current_user), db:Database = Depends(get_db_instance)):
    try:
        threads_collection = db["threads"]
        thread = threads_collection.find_one({"_id": ObjectId(thread_id)})
        # print(thread, auth['id'])
        if thread != None and str(thread["userId"]) != auth['id']:
            raise HTTPException(status_code=401, detail="You are not authorized to update this thread.")
        if thread == None:
            raise HTTPException(status_code=401, detail="Thread not found.")
            
        threads_collection.update_one({"_id": ObjectId(thread_id)}, {"$set": {"title": payload.title}})
        return {"success": True, "message": "Thread has been updated successfully!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Something went wrong!")