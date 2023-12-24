import json
from bson import json_util
from datetime import datetime
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