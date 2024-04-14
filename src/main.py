import sys
from datetime import datetime
from bot.notifier import Notifier
from data import DB
from bot import SafeBot
from llm import LLM, PROMPTS
from watcher import EventListener

if __name__ == "__main__":
    bot = SafeBot()
    llm = LLM()
    notifier = Notifier(bot, llm, PROMPTS.condition)
    db = DB()
    args = sys.argv
    if args[1] == "bot":
        bot.start()
    elif args[1] == "events":
        event_listener = EventListener(db, notifier.handler)
        event_listener.listen()
    elif args[1] == "reset":
        db.reset()
