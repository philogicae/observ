import sys
from threading import Thread

from bot import SafeBot
from data import DB
from watcher import EventListener, start_event_listener

if __name__ == "__main__":
    if len(sys.argv) == 1:
        Thread(target=start_event_listener, daemon=True).start()
        SafeBot().start()
    elif sys.argv[1] == "bot":
        SafeBot().start()
    elif sys.argv[1] == "events":
        EventListener().start()
    elif sys.argv[1] == "reset":
        db = DB()
        db.reset()
