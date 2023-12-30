from fuzzywuzzy import process
from flair.nn import Classifier
from flair.data import Sentence

class QueryAmplifier:
    def __init__(self):
        pass

    ENTITIES = [
        "big tech",
        "small tech",
        "non tech",
        "medium tech",
        "medium non tech",
        "small non tech"
    ]

    def extract_custom_entities(self, text, threshold=90):
        query = text.lower()
        tokens = query.split(" ")
        entities = []
        for token in tokens:
            if len(token) < 3:
                continue
            isMatched = process.extractOne(token, self.ENTITIES, score_cutoff=threshold)
            if isMatched:
                #Check if entity already contain this match
                if isMatched[0] not in entities:
                    entities.append(isMatched[0])
        return entities
    
    def extract_common_entities(self,text):
        tagger = Classifier.load('ner')
        sentence = Sentence(text.upper())
        tagger.predict(sentence)
        entities = []
        for entity in sentence.get_spans('ner'):
            entities.append(entity.text)
        return entities
    
    def get_keywords(self,query):
        #extract both common and custom entities from query and return the mergeed array
        common_entities = self.extract_common_entities(query)
        custom_entities = self.extract_custom_entities(query)
        entities = common_entities + custom_entities
        return entities

    def amplify_query(self,query,keywords,amp_constant=4):
        for entity in keywords:
            query = query+(" "+entity.upper()+" ")*amp_constant
        return query
    
