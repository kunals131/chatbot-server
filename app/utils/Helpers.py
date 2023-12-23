import json
from bson import json_util

class Helpers():
    @staticmethod
    def parse_json(data):
        return json.loads(json_util.dumps(data))

    @staticmethod
    def is_valid_dict(dictionary):
        for value in dictionary.values():
            if value is not None and value != '' and value != {} and len(value)>0 and value != [] and value != 'null':
                return True
        return False