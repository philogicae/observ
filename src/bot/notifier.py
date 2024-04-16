from addict import Dict

from llm import LLM, Prompts


class Notifier:
    def __init__(self):
        try:
            from bot.telegram import SafeBot
        except Exception as e:
            print(e)
        self.bot = SafeBot()
        self.llm = LLM()
        self.condition_prompt = Prompts.condition

    def handler(self, to_check):
        to_process, refs, i = [], {}, 0
        for request_id, data, txHash, event in to_check:
            refs[i] = [data.chat_id, data.user_id]
            needed_data = Dict(
                log_id=i,
                request_id=request_id,
                intention=data.intention,
                event_name=data.event_name,
                condition=data.condition,
                tx_hash=txHash,
                event_logs=dict(event.args),
            )
            if "decimals" in data:
                needed_data.decimals = data.decimals
            to_process.append(needed_data)
            i += 1
        if to_process:
            results = self.llm.call_for_json(self.condition_prompt, str(to_process))
            if results:
                to_notify = {}
                for i in results.found:
                    try:
                        data = to_process[i]
                        condition = (
                            ("\n- Condition: " + str(data.condition))
                            if data.decimals
                            else ""
                        )
                        decimals = (
                            ("\n- Decimals: " + str(data.decimals))
                            if data.decimals
                            else ""
                        )
                        base = f"⚠️ Alert-{data.request_id}: {data.intention}{condition}{decimals}\n- Event: {data.event_name}\n- Tx: {data.tx_hash.hex()}\nLogs:"
                        log = f"\n{data.event_logs}"
                        if base not in to_notify:
                            to_notify[base] = [i, log]
                        else:
                            to_notify[base][1] += log
                    except Exception as e:
                        from bot.telegram import Log

                        Log.error(str(e))
                for base, (i, log) in to_notify.items():
                    self.bot.notify(*refs[i], base + log)
