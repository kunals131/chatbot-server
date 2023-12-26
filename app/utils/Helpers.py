import json
from bson import json_util
from datetime import datetime
import random
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
    @staticmethod
    def get_current_time_string():
        now = datetime.now()

        hour = now.hour % 12  # Convert to 12-hour format
        minute = now.minute
        am_pm = "AM" if hour < 12 else "PM"  # Add AM/PM indicator

        # Format hour and minute with leading zeros if needed
        hour = f"{hour:02d}"
        minute = f"{minute:02d}"

        date = now.strftime("%d %b %Y")  # Format date as "20 Dec 2019"

        return f"{hour}:{minute}{am_pm} {date}"
    
    def getRandomAdditionalMsgForSuggestion(isEmpty=True):
        additionalEmptyMsg = [
            "No engineers found so far! ",
            "No engineers found! ",
            "No engineers found yet! ",
            "Nada nothing yet! "
        ]
        additionalMsg = [
            "Here are some engineers you might be interested in: ",
            "Here are some engineers you might like: ",
            "Here are some engineers you might want to check out: ",
            "Here are some engineers you might want to look at: ",
            "I found a few! ",
        ]
        if isEmpty:
            return additionalEmptyMsg[random.randint(0,len(additionalEmptyMsg)-1)]
        else:
            return additionalMsg[random.randint(0,len(additionalMsg)-1)]
