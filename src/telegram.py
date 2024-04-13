from os import getenv
from time import sleep, time as now
from dotenv import load_dotenv
from logging import basicConfig, getLogger, INFO
from rich.logging import RichHandler
from telebot import TeleBot, types

# .env
load_dotenv()
TOKEN = getenv("TELEGRAM_BOT_ID")

# Logs
basicConfig(
    format="%(message)s", datefmt="[%d-%m %X]", level=INFO, handlers=[RichHandler()]
)
logger = getLogger("rich")
sent = lambda chat_id, user, name, log: logger.info(
    f"<-[{chat_id}](@{user}) {name}: {log}"
)
received = lambda chat_id, user, name, log: logger.info(
    f"->[{chat_id}](@{user}) {name}: {log}"
)
happened = lambda chat_id, user, name, log: logger.info(
    f"-x[{chat_id}](@{user}) {name}: {log}"
)

# Responses
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

    def send(self, text, chat_id, parse_mode=None):
        return self.exec(self.bot.send_message, chat_id, text, parse_mode=parse_mode)[0]

    def reply(self, message, text, parse_mode=None):
        return self.exec(self.bot.reply_to, message, text, parse_mode=parse_mode)[0]

    def edit(self, text, chat_id, message_id, parse_mode=None):
        return self.exec(
            self.bot.edit_message_text, text, chat_id, message_id, parse_mode=parse_mode
        )[0]

    def delete(self, chat_id, message_id):
        return self.exec(self.bot.delete_message, chat_id, message_id)[0]


# History
chatrooms = dict()


def get_history(chat_id):
    return chatrooms.get(chat_id, dict())


def get_user_history(chat_id, user_id):
    return get_history(chat_id).get(user_id, [])


def insert_msg_history(chat_id, user_id, message):
    if chat_id not in chatrooms:
        chatrooms[chat_id] = dict()
    if user_id not in chatrooms[chat_id]:
        chatrooms[chat_id][user_id] = []
    chatrooms[chat_id][user_id].append(message)


bot = TeleBot(
    TOKEN,
    threaded=False,
    disable_web_page_preview=True,
    skip_pending=True,
)
safe = SafeRequest(bot)


@bot.message_handler(content_types=["text"])
def handle_message(message: types.Message):
    chat_id = message.chat.id
    sender = message.from_user
    _input = message.text
    insert_msg_history(chat_id, sender.id, _input)
    safe.send(waiting, chat_id)
    sent(chat_id, sender.username, sender.first_name, waiting)


try:
    logger.info("Starting...")
    bot.infinity_polling(skip_pending=True, timeout=300, long_polling_timeout=300)
except KeyboardInterrupt:
    logger.info("Killed by KeyboardInterrupt")
except Exception as e:
    logger.error(f"Error: {e}")
