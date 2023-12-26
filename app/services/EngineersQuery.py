from sentence_transformers import SentenceTransformer
# from config.sql_connection import get_connection
import pinecone
model_path = 'models/all-mpnet-base-v2'  

class QueryModes:
    PERCISE = '0'
    BALANCED = '1'
    BASIC = '2'

pinecone.init(api_key="11b20ba4-2b37-42a2-8255-b90e095279d1", environment="gcp-starter")


class EngineersQuery():
    def __init__(self): 
        pass

    def get_vector_embeddings(self,text:str):
        model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
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
    
    def get_engineers_precise(self,query:str, entities):
        metaDataFilter = self.get_metadata_filters_from_entities(entities)
        vector = self.get_vector_embeddings(query)
        pineconeIndex = pinecone.Index("engineers")
        queryMatches = pineconeIndex.query(vector=vector,top_k=10, filter=metaDataFilter, include_metadata=True)
        matches = [{key: obj[key] for key in ['id','score']} for obj in queryMatches['matches']]
        resumeIds = [match['id'] for match in matches]
        return queryMatches.to_dict()

    def get_engineers_balanced(self,query:str, entities):
        metaDataFilter = self.get_metadata_filters_from_entities(entities, queryMode=QueryModes.BALANCED)
        vector = self.get_vector_embeddings(query)
        pineconeIndex = pinecone.Index("engineers")
        queryMatches = pineconeIndex.query(vector=vector,top_k=10, filter=metaDataFilter, include_metadata=True)
        matches = [{key: obj[key] for key in ['id','score']} for obj in queryMatches['matches']]
        resumeIds = [match['id'] for match in matches]
        return queryMatches.to_dict()

    def get_engineers_basic(self,query:str):
        vector = self.get_vector_embeddings(query)
        pineconeIndex = pinecone.Index("engineers")
        queryMatches = pineconeIndex.query(vector=vector,top_k=10, include_metadata=True)
        matches = [{key: obj[key] for key in ['id','score']} for obj in queryMatches['matches']]
        resumeIds = [match['id'] for match in matches]
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
        pass
        # Close the connection when the object is destroyed
        # if 'SQLConnection' in self and self.SQLconnection:
        #     self.SQLconnection.close()
    
    
    
        

