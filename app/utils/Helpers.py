import json
from bson import json_util

class Helpers():
    @staticmethod
    def parse_json(data):
        return json.loads(json_util.dumps(data))
