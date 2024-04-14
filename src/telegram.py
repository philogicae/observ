from os import getenv
from time import sleep, time as now
from typing import Tuple
from addict import Dict
from data.db import DB
from dotenv import load_dotenv
from logging import basicConfig, getLogger, INFO
from llm.llm import LLM
from rich.logging import RichHandler
from telebot import TeleBot, types

load_dotenv()

# Logs
basicConfig(
    format="%(message)s", datefmt="[%d-%m %X]", level=INFO, handlers=[RichHandler()]
)
logger = getLogger("rich")

# Responses
starting = "Welcome!\nTo get notifications about Arbitrum on-chain activity, just send me a contract address and describe what you want to monitooor.\nI will check constantly and notify you!"
waiting = "Observ is thinking..."
checking = "Observ is checking..."


class SafeRequest:
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.delay = 0.2
        self.last = 0
        self.logger = logger

    def done(self):
        self.last = now()

    def is_free(self):
        return self.last + self.delay < now()

    def exec(self, method, *args, **kwargs):
        while True:
            if self.is_free():
                try:
                    return method(*args, **kwargs), self.done()
                except:
                    pass
            else:
                sleep(self.delay)

    def send(self, text, chat_id, parse_mode=None) -> types.Message:
        return self.exec(self.bot.send_message, chat_id, text, parse_mode=parse_mode)[0]

    def reply(self, message, text, parse_mode=None) -> types.Message:
        return self.exec(self.bot.reply_to, message, text, parse_mode=parse_mode)[0]

    def edit(self, text, chat_id, message_id, parse_mode=None) -> types.Message:
        return self.exec(
            self.bot.edit_message_text, text, chat_id, message_id, parse_mode=parse_mode
        )[0]

    def delete(self, chat_id, message_id):
        return self.exec(self.bot.delete_message, chat_id, message_id)[0]


class History:
    def __init__(self, bot_user: types.User):
        self.users = Dict({bot_user.id: [bot_user.username, bot_user.first_name]})
        self.chatrooms = Dict()

    def get_user(self, user_id) -> Tuple[str, str]:
        return self.users.get(user_id)

    def insert_user(self, user_id, user, name):
        self.users[user_id] = [user, name]

    def get_chat(self, chat_id):
        return self.chatrooms.get(chat_id, Dict())

    def get_user_chat(self, chat_id, user_id):
        return self.get_chat(chat_id).get(user_id, [])

    def insert_msg(self, chat_id, user_id, message, user=None, name=None):
        if chat_id not in self.chatrooms:
            self.chatrooms[chat_id] = Dict()
        if user_id not in self.chatrooms[chat_id]:
            self.chatrooms[chat_id][user_id] = []
        if user_id not in self.users and user and name:
            self.insert_user(user_id, user, name)
        self.chatrooms[chat_id][user_id].append(message)


class SafeBot:
    sent = lambda _, chat_id, user, name, log: logger.info(
        f"<-[{chat_id}](@{user}) {name}: {log}"
    )
    received = lambda _, chat_id, user, name, log: logger.info(
        f"->[{chat_id}](@{user}) {name}: {log}"
    )
    happened = lambda _, chat_id, user, name, log: logger.info(
        f"-x[{chat_id}](@{user}) {name}: {log}"
    )

    def __init__(self):
        self.bot = TeleBot(
            token=getenv("TELEGRAM_BOT_ID"),
            threaded=False,
            disable_web_page_preview=True,
            skip_pending=True,
        )
        self.safe = SafeRequest(self.bot)
        self.me = self.bot.get_me()
        self.history = History(self.me)
        self.db = DB()
        self.llm = LLM()

        @self.bot.message_handler(commands=["start"])
        def handle_start(message: types.Message):
            chat_id = message.chat.id
            sender = message.from_user
            text = message.text
            self.msg_in(chat_id, sender, text)
            self.msg_out(chat_id, starting)

        @self.bot.message_handler(content_types=["text"])
        def handle_message(message: types.Message):
            chat_id = message.chat.id
            sender = message.from_user
            text = message.text
            self.msg_in(chat_id, sender, text)
            msg = self.msg_out(chat_id, waiting)
            resp = self.llm.call("I am an AI, and I am ready to respond.", text)
            self.msg_out(chat_id, resp, msg.id)

    def start(self):
        try:
            logger.info("Observ: Started.")
            self.bot.infinity_polling(
                skip_pending=True, timeout=300, long_polling_timeout=300
            )
        except KeyboardInterrupt:
            logger.info("Killed by KeyboardInterrupt")
        except Exception as e:
            logger.error(f"Error: {e}")

    def infinity_polling(self, **kwargs):
        self.bot.infinity_polling(**kwargs)

    def msg_in(self, chat_id, sender, text):
        self.received(chat_id, sender.username, sender.first_name, text)
        self.db.commit("insert_message", chat_id, sender.id, text)
        self.history.insert_msg(chat_id, sender.id, text, sender, sender.first_name)

    def msg_out(self, chat_id, text, msg_id=None):
        if not msg_id:
            msg = self.safe.send(text, chat_id)
        else:
            msg = self.safe.edit(text, chat_id, msg_id)
        self.sent(chat_id, *self.history.get_user(self.me.id), text)
        self.db.commit("insert_message", chat_id, self.me.id, text)
        self.history.insert_msg(chat_id, self.me.id, text)
        return msg


bot = SafeBot()

if __name__ == "__main__":
    bot.start()
