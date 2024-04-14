from os import getenv
from time import sleep, time as now
from typing import Tuple

from web3 import Web3
from addict import Dict
from api import BlockExplorer
from data.db import DB
from dotenv import load_dotenv
from logging import basicConfig, getLogger, INFO
from llm import LLM, PROMPTS
from rich.logging import RichHandler
from telebot import TeleBot, types
from watcher import RPC

load_dotenv()

# Logs
basicConfig(
    format="%(message)s", datefmt="[%d-%m %X]", level=INFO, handlers=[RichHandler()]
)
logger = getLogger("rich")
shorten = lambda text: text[0:100] + ("..." if len(text) > 100 else "")
sent = lambda chat_id, user, name, log: logger.info(
    f"<-[{chat_id}](@{user}) {name}: {shorten(log)}"
)
received = lambda chat_id, user, name, log: logger.info(
    f"->[{chat_id}](@{user}) {name}: {shorten(log)}"
)
happened = lambda chat_id, user, name, log: logger.info(
    f"-x[{chat_id}](@{user}) {name}: {shorten(log)}"
)

# Responses
starting = "Welcome!\nTo get notifications about Arbitrum on-chain activity, just send me a contract address and describe what you want to monitooor.\nI will check constantly and notify you!\nStart by sending:\n#tellmewhen ..."
waiting = "Observ is thinking..."
checking = "Observ is checking..."
proxying = "Observ is checking the proxied contract..."
missing = "Please provide a contract address by sending:\n#address 0x..."
done = "Successfully added to your list of monitored events!"


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
        self.buffer = Dict()

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
        agent = "user: " if user else "assistant: "
        self.chatrooms[chat_id][user_id].append(agent + message)


class SafeBot:
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
            self.msg_out(chat_id, sender, starting)

        @self.bot.message_handler(content_types=["text"])
        def handle_message(message: types.Message):
            chat_id = message.chat.id
            sender = message.from_user
            text = message.text
            self.msg_in(chat_id, sender, text)
            msg = self.msg_out(chat_id, sender, waiting)
            if not text.startswith("#"):
                resp = self.llm.call(PROMPTS.default, text)
            else:
                user, name = self.history.get_user(self.me.id)
                if text.startswith("#tellmewhen ") and len(text) > 12:
                    parsed = self.llm.call_for_json(PROMPTS.analyse, text)
                    if parsed.address:
                        try:
                            parsed.address = Web3.to_checksum_address(parsed.address)
                        except Exception as e:
                            happened(chat_id, user, name, str(e))
                            parsed.address = None
                    if not parsed.address:
                        happened(
                            chat_id, user, name, "Missing or invalid contract address"
                        )
                        resp = missing
                    else:
                        happened(chat_id, user, name, str(parsed))
                        resp = checking
                        self.history.buffer[chat_id] = parsed
                elif text.startswith("#address ") and len(text) > 9:
                    self.history.buffer[chat_id].address = Web3.to_checksum_address(
                        text[9:]
                    )
                    happened(chat_id, user, name, "Added contract address")
                    resp = "Thank you! " + checking
            self.msg_out(chat_id, sender, resp, msg.id)
            if resp == checking:
                buffer = self.history.buffer[chat_id]
                abi = BlockExplorer.get_abi(buffer.address)
                if abi:
                    if '"name":"implementation"' in abi:
                        happened(chat_id, user, name, "Got ABI by it's a proxy")
                        self.msg_out(chat_id, sender, proxying, msg.id)
                        impl_address = (
                            Web3(Web3.HTTPProvider(RPC.arbitrum.calls.https))
                            .eth.contract(
                                address=buffer.address,
                                abi=abi,
                            )
                            .functions.implementation()
                            .call()
                        )
                        abi = BlockExplorer.get_abi(
                            Web3.to_checksum_address(impl_address)
                        )
                    buffer.abi = abi
                    happened(chat_id, user, name, "Got ABI")
                    if buffer.decimals:
                        buffer.decimals = (
                            Web3(Web3.HTTPProvider(RPC.arbitrum.calls.https))
                            .eth.contract(
                                address=buffer.address,
                                abi=abi,
                            )
                            .functions.decimals()
                            .call()
                        )
                        happened(chat_id, user, name, "Got decimals")
                    else:
                        buffer.decimals = 0
                    buffer.method = self.llm.call_for_json(
                        PROMPTS.method,
                        f"Intention: {buffer.intention}\nABI: {buffer.abi}",
                    ).event
                    happened(chat_id, user, name, "Got event name: " + buffer.method)
                    self.db.commit(
                        "insert_request",
                        chat_id,
                        sender.id,
                        "event",
                        buffer.address,
                        buffer.abi,
                        buffer.method,
                        "",  # buffer.args
                        buffer.condition,
                        buffer.decimals,
                        buffer.intention,
                    )
                else:
                    happened(chat_id, user, name, "ABI not found")
                self.msg_out(
                    chat_id,
                    sender,
                    done
                    + f"\nIntention: {buffer.intention}\nContract: {buffer.address}\nEvent: {buffer.method}\nCondition: {buffer.condition if buffer.condition else 'None'}",
                    msg.id,
                )

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
        received(chat_id, sender.username, sender.first_name, text)
        self.db.commit("insert_message", chat_id, sender.id, text)
        self.history.insert_msg(chat_id, sender.id, text, sender, sender.first_name)

    def msg_out(self, chat_id, receiver, text, msg_id=None):
        msg = (
            self.safe.send(text, chat_id)
            if not msg_id
            else self.safe.edit(text, chat_id, msg_id)
        )
        sent(chat_id, *self.history.get_user(self.me.id), text)
        self.db.commit("insert_message", chat_id, self.me.id, text)
        self.history.insert_msg(chat_id, receiver.id, text)
        return msg

    def notify(self, chat_id, receiver_id, text):
        self.safe.send(text, chat_id)
        sent(chat_id, *self.history.get_user(self.me.id), text)
        self.db.commit("insert_message", chat_id, self.me.id, text)
        self.history.insert_msg(chat_id, receiver_id, text)


bot = SafeBot()

if __name__ == "__main__":
    bot.start()
