from sentence_transformers import SentenceTransformer
from app.config.sql_connection import get_connection
import pinecone
import pandas as pd
from app.utils.Constants import PINECONE_CREDENTIALS


model_path = 'models/all-mpnet-base-v2'  

class QueryModes:
    PERCISE = '0'
    BALANCED = '1'
    BASIC = '2'

pinecone.init(api_key=PINECONE_CREDENTIALS.API_KEY, environment=PINECONE_CREDENTIALS.ENV)


class EngineersQuery():
    def __init__(self): 
        self.sqlConn = None

    def get_vector_embeddings(self,text:str):
        model = SentenceTransformer('sentence-transformers/multi-qa-MiniLM-L6-cos-v1')
        return model.encode(text).tolist()
    

    
    def get_metadata_filters_from_entities(self,entities, queryMode=QueryModes.PERCISE):
        metaDataFilter = {}
        skills = entities['skills'] if entities['skills'] else []
        print(skills)
        metaDataFilter['$or'] = []
        if entities['availability']:
            if entities['availability'] == 'full-time':
                metaDataFilter['fullTimeAvailability'] = True
            elif entities['availability'] == 'part-time':
                metaDataFilter['partTimeAvailability'] = True
        if 'budget' in entities and entities['budget']:
            #if we have availability and budget then if availability is full time then add a filter with $lt fullTimeSalary and if it's part-time then add a filter with $lt partTimeSalary otherwise add a or condition if partTimeSalary or fullTimeSalary is less than budget
            if entities['availability']:
                if entities['availability'] == 'full-time':
                    metaDataFilter['fullTimeSalary'] = {'$lt': entities['budget']['amount']}
                elif entities['availability'] == 'part-time':
                    metaDataFilter['partTimeSalary'] = {'$lt': entities['budget']['amount']}
            else:
                metaDataFilter['$or'] = [
                    {'fullTimeSalary': {'$lt': entities['budget']['amount']}},
                    {'partTimeSalary': {'$lt': entities['budget']['amount']}}
                ]
        if len(skills)>0:
            if queryMode == QueryModes.PERCISE:
                metaDataFilter['$and'] = []
                for skill in skills:
                    metaDataFilter['$and'].append({'Skills': {'$eq': skill}})
            elif queryMode == QueryModes.BALANCED:
                metaDataFilter['$or'].append({'Skills': {'$in': skills}})
        
        return metaDataFilter
    
    def get_engineer_details(self,results):
        try:
            self.sqlConn = get_connection()
            matches = results['matches']
            resumeIds = [match['id'] for match in matches]
            resume_ids_str = ','.join("'" + str(id) + "'" for id in resumeIds)
            print(resume_ids_str)
            query = """
                SELECT r.resumeId, r.userId, pi.name, pi.email, pi.phone, u.fullTimeStatus, u.workAvailability, u.fullTimeSalaryCurrency, 
                u.fullTimeSalary, u.partTimeSalaryCurrency, u.partTimeSalary, u.fullTimeAvailability, 
                u.partTimeAvailability, u.preferredRole,
                GROUP_CONCAT(DISTINCT we.company) AS WorkExperience,
                GROUP_CONCAT(DISTINCT ed.degree) AS Education,
                pi.location
                FROM UserResume r
                LEFT JOIN PersonalInformation pi ON r.resumeId = pi.resumeId
                LEFT JOIN MercorUsers u ON r.userId = u.userId
                LEFT JOIN WorkExperience we ON r.resumeId = we.resumeId
                LEFT JOIN Education ed ON r.resumeId = ed.resumeId
                WHERE r.resumeId IN ({})
                GROUP BY r.resumeId, pi.location, pi.name, pi.email, pi.phone
            """.format(resume_ids_str)
            cursor = self.sqlConn.cursor()
            cursor.execute(query)
            records = cursor.fetchall()
            cursor.close()
            results = []
            for row in records:
                column_names = [description[0] for description in cursor.description]
                row_dict = dict(zip(column_names, row))
                results.append(row_dict)
            return results
        except Exception as e:
            print(e)
            return []

    def processEngineerResults(self,matches):
        updated_data = []
        for obj in matches:
            updated_obj = {
                "id": obj["id"],
                "score": obj["score"],
                "skills": ', '.join(obj["metadata"]["Skills"]) if obj["metadata"].get("Skills") else "",
            }
            updated_data.append(updated_obj)
        response ={}
        response['matches'] = updated_data
        return response


    
    def get_engineers_precise(self,query:str, entities):
        metaDataFilter = self.get_metadata_filters_from_entities(entities)
        vector = self.get_vector_embeddings(query)
        pineconeIndex = pinecone.Index(PINECONE_CREDENTIALS.INDEX)
        queryMatches = pineconeIndex.query(vector=vector,top_k=6, filter=metaDataFilter, include_metadata=True)
        self.get_engineer_details(queryMatches.to_dict())
        return queryMatches.to_dict()
    def get_engineers_balanced(self,query:str, entities):
        metaDataFilter = self.get_metadata_filters_from_entities(entities, queryMode=QueryModes.BALANCED)
        vector = self.get_vector_embeddings(query)
        pineconeIndex = pinecone.Index(PINECONE_CREDENTIALS.INDEX)
        queryMatches = pineconeIndex.query(vector=vector,top_k=6, filter=metaDataFilter, include_metadata=True)
        matches = [{key: obj[key] for key in ['id','score']} for obj in queryMatches['matches']]
        resumeIds = [match['id'] for match in matches]
        return queryMatches.to_dict()
    def get_engineers_basic(self,query:str):
        vector = self.get_vector_embeddings(query)
        pineconeIndex = pinecone.Index(PINECONE_CREDENTIALS.INDEX)
        queryMatches = pineconeIndex.query(vector=vector,top_k=6, include_metadata=True)
        return queryMatches.to_dict()
    
  
    def get_engineers(self,query:str,entities:dict={}, mode:str=QueryModes.PERCISE):
        if mode == QueryModes.PERCISE:
            return self.get_engineers_precise(query, entities)
        elif mode == QueryModes.BALANCED:
            return self.get_engineers_balanced(query, entities)
        elif mode == QueryModes.BASIC:
            print("Processing basic query")
            return self.get_engineers_basic(query)
        else:
            return self.get_engineers_precise(query, entities)
    

            

    def __del__(self):
        if self.sqlConn:
            self.sqlConn.close()
    
    
    
        

