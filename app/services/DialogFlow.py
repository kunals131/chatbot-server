import os
from google.cloud import dialogflow_v2 as dialogflow
from pydantic import BaseModel
import re
from app.utils.Constants import Constants, DIALOGFLOW_CONFIG
from app.utils.Helpers import Helpers

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
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = DIALOGFLOW_CONFIG.CREDENTIALS_PATH
        self.project_id = DIALOGFLOW_CONFIG.PROJECT_ID
        self.language_code = DIALOGFLOW_CONFIG.LANGUAGE_CODE
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
    
    def getBotResponse(self,session_id,text):
        session = self.client.session_path(self.project_id, session_id)
        text_input = dialogflow.TextInput(text=text, language_code=self.language_code)
        query_input = dialogflow.QueryInput(text=text_input)
        response = self.client.detect_intent(request={"session": session, "query_input": query_input})
        return response
    
    def parseUnitAmountObject(self,entities):
        current_budget = dict(entities['unit-currency']) if 'unit-currency' in entities else None
        current_budget =  current_budget['amount'] if current_budget and 'amount' in current_budget else None
        return current_budget
    
    def parseBudgetIfAvailable(self,entities,session_id, text):
        is_yearly = entities['salaryduration'] == Constants.SALARY_DURATION_YEARLY if 'salary-duration' in entities else False
        current_budget = self.parseUnitAmountObject(entities)
        is_unlimited_budget = entities['budget'] == Constants.UNLIMITED_BUDGET_TEXT if 'budget' in entities else False
        if is_unlimited_budget and not current_budget:
            current_budget = Constants.UNLIMITED_BUDGET_VALUE
            if current_budget and is_yearly:
                current_budget = current_budget/12
            budget_input_response = self.getBotResponse(session_id, f"My budget is ${current_budget}")
            return budget_input_response
        
        elif not current_budget:
            extracted_amount = self.parseForAmount(text)
            if extracted_amount and is_yearly:
                extracted_amount = extracted_amount/12
            if extracted_amount:
                budget_input_response = self.getBotResponse(session_id, f"My budget is ${extracted_amount}")
                entities = dict(budget_input_response.query_result.parameters)
                return budget_input_response

    def interact(self,session_id, text)->ChatBotResponse:
        response = self.getBotResponse(session_id, text)
        entities = dict(response.query_result.parameters)
        if response.query_result.intent.display_name == Constants.HIRE_ENGINEER_INTENT:
            parsed_entity_response = self.parseBudgetIfAvailable(entities,session_id,text)
            if parsed_entity_response:
                parsedBudgetEntities = dict(parsed_entity_response.query_result.parameters)
                prev_query_amount = self.parseUnitAmountObject(entities)
                current_query_amount = self.parseUnitAmountObject(parsedBudgetEntities)
                if prev_query_amount != current_query_amount:
                    entities = parsedBudgetEntities
                    response = parsed_entity_response

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