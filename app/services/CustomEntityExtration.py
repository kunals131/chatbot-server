from fuzzywuzzy import fuzz
from fuzzywuzzy import process

class CustomEntity:
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

    def extract(self, text, threshold=90):
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
