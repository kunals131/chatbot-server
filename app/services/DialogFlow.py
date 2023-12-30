import os
from google.cloud import dialogflow_v2 as dialogflow
from pydantic import BaseModel
import re

class ChatBotEntities(BaseModel):
    session_id: str
    availability: str
    skills: list
    budget: dict

class ChatBotResponse(BaseModel):
    response: str
    intent: str
    entities: ChatBotEntities

class ChatBot():
    def __init__(self):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'app/config/credentials.json'
        self.project_id = 'hip-heading-408717'
        self.language_code = 'en'
        self.client = dialogflow.SessionsClient()

    def parseForAmount(self,text:str):
        pattern = r'\b(?:\$|USD)?\s?(\d{1,3}(?:,\d{3})*|\d+\.?\d?)\s?(k|K)?\b'
        
        matches = re.findall(pattern, text)
        magnitude = {'k': 1000, 'K': 1000}
        
        amounts = []
        for match in matches:
            amount_str, magnitude_str = match
            amount_str = amount_str.replace(',', '')

            if magnitude_str:
                amount = float(amount_str) * magnitude[magnitude_str]
            else:
                amount = float(amount_str)
            
            amounts.append(amount)
        
        return amounts[0] if len(amounts)>0 else None
        
        
    def updateEntityReq(self,session_id,text):
        print(text)
        session = self.client.session_path(self.project_id, session_id)
        text_input = dialogflow.TextInput(text=text, language_code=self.language_code)
        query_input = dialogflow.QueryInput(text=text_input)
        response = self.client.detect_intent(request={"session": session, "query_input": query_input})
        return response.query_result.parameters

    def interact(self,session_id, text)->ChatBotResponse:
        session = self.client.session_path(self.project_id, session_id)
        text_input = dialogflow.TextInput(text=text, language_code=self.language_code)
        query_input = dialogflow.QueryInput(text=text_input)
        response = self.client.detect_intent(request={"session": session, "query_input": query_input})
        extracted_budget = self.parseForAmount(text)
        print(extracted_budget)
        if extracted_budget:
            response.query_result.parameters = self.updateEntityReq(session_id=session_id, text=f"My budget is ${extracted_budget}")
        entities = dict(response.query_result.parameters)
        
        params = dict()
        params['availability'] = entities['availability'] if 'availability' in entities else None
        params['skills'] = list(entities['skill']) if len(list(entities['skill']) if 'skill' in entities else [])>0 else []
        params['budget'] = dict(entities['unit-currency']) if 'unit-currency' in entities else {}
        print(params,entities)
        return {
            'response': response.query_result.fulfillment_text,
            'intent': response.query_result.intent.display_name,
            'entities': params 
        }
    
