from datetime import datetime
from addict import Dict
from rich import print


class Notifier:
    def __init__(self, bot, llm, condition_prompt):
        self.bot = bot
        self.llm = llm
        self.condition_prompt = condition_prompt

    def handler(self, to_check):
        to_process, refs, i = [], {}, 0
        for request_id, data, event in to_check:
            print(
                f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - {request_id}: {dict(event.args)}'
            )
            refs[i] = [data.chat_id, data.user_id]
            needed_data = Dict(
                log_id=i,
                request_id=request_id,
                intention=data.intention,
                event_name=data.event_name,
                condition=data.condition,
                event_logs=dict(event.args),
            )
            if "decimals" in data:
                needed_data.decimals = data.decimals
            to_process.append(needed_data)
            i += 1
        results = self.llm.call_for_json(self.condition_prompt, str(to_process))
        if results:
            for r in results.found:
                try:
                    i = int(r)
                    data = to_process[i]
                    self.bot.notify(
                        *refs[i],
                        f"Alert for request_id {data.request_id}:\n- Intention: {data.intention}\n- Condition: {data.condition}\n- Event: {data.event_name}\n- Logs: {data.event_logs}{'\n- Decimals: '+str(data.decimals) if data.decimals else ''}",
                    )
                except Exception as e:
                    print(e)
