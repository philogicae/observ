from datetime import datetime
from addict import Dict
from llm import PROMPTS
from rich import print


class Notifier:
    def __init__(self, bot, llm, condition_prompt):
        self.bot = bot
        self.llm = llm
        self.condition_prompt = condition_prompt

    def handler(self, to_check):
        to_process = []
        for request_id, data, event in to_check:
            print(
                f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - {request_id}: {dict(event.args)}'
            )
            needed_data = Dict(
                intention=data.intention,
                event_name=data.event_name,
                condition=data.condition,
                event_logs=dict(event.args),
            )
            if "decimals" in data:
                needed_data.decimals = data.decimals
            to_process.append(needed_data)
        result = self.llm.call_for_json(self.condition_prompt, str(to_process))
        print(result)

    def notify(self):
        pass
