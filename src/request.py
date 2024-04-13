import datetime

class Request:
    def __init__(self, id, chat_id, user_id, data, type, condition, active):
        self.id = id
        self.chat_id = chat_id
        self.user_id = user_id
        self.data = data
        self.type = type
        self.condition = condition
        self.active = active
        self.time = datetime.now()
