from os import getenv
from time import sleep, time

from addict import Dict
from dotenv import load_dotenv
from telebot import TeleBot, types
from web3 import Web3

from api import BlockExplorer
from bot import Log
from data import DB
from llm import LLM, Prompts
from watcher import RPC

load_dotenv()


# Responses
starting = "🔥 Welcome! 🔥\nTo get notifications about Arbitrum on-chain activity, just send me a contract address and describe what you want to monitooor.\nI will check constantly and notify you!\nStart by sending an intention and a contract address:\n#tellmewhen ... 0x..."
notice = "❓ How to use Observ ❓\nTo add a new alert:\n#tellmewhen ... 0x...\nTo enable/disable an alert-x:\n#on x\n#off x"
reset = "♻️ All alerts deleted ♻️"
waiting = "🛠️ Observ is thinking..."
checking = "🛠️ Observ is checking..."
proxying = "🛠️ Observ is checking the proxied contract..."
missing = "⌛ Please provide a contract address by sending:\n#address 0x..."
added = lambda x: f"✅ Successfully added Alert-{x} ✅"
on = lambda x: f"🟢 Alert-{x}: on 🟢"
off = lambda x: f"🔴 Alert-{x}: off 🔴"


class SafeRequest:
    def __init__(self, bot: TeleBot):
        self.bot = bot
        self.delay = 0.2
        self.last = time()

    def done(self):
        self.last = time()

    def is_free(self):
        return self.last + self.delay < time()

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
    def __init__(self, db):
        self.db = db
        self.buffer = Dict()

    def get_user(self, user_id):
        return self.db.fetch("get_user", user_id)

    def insert_user(self, user_id, user, name):
        self.db.commit("insert_user", user_id, user, name)

    def get_chat(self, chat_id):
        return self.db.fetch("get_chat", chat_id, 10)

    def get_user_chat(self, chat_id, user_id):
        return self.db.fetch("get_user_chat", chat_id, user_id, 10)

    def insert_msg(self, chat_id, user_id, message, bot=False):
        self.db.commit(
            "insert_message",
            chat_id,
            user_id,
            message,
            "user" if not bot else "assistant",
        )


class SafeBot:
    def __init__(self):
        self.bot = TeleBot(
            token=getenv("TELEGRAM_BOT_ID"),
            threaded=False,
            disable_web_page_preview=True,
            skip_pending=True,
        )
        self.bot.set_my_commands(
            commands=[
                types.BotCommand("start", "🤖 Start Observ"),
                types.BotCommand("help", "❓ How to use Observ"),
                types.BotCommand("list", f"💾 List alerts"),
                types.BotCommand("reset", "♻️ Reset alerts"),
            ]
        )
        self.safe = SafeRequest(self.bot)
        self.db = DB()
        self.history = History(self.db)
        self.llm = LLM()
        self.myself = [self.bot.get_me().username, self.bot.get_me().first_name]

        @self.bot.message_handler(commands=["start"])
        def handle_start(message: types.Message):
            chat_id, sender, text = self.context(message)
            self.msg_in(chat_id, sender, text)
            self.msg_out(chat_id, sender, starting)

        @self.bot.message_handler(commands=["help"])
        def handle_help(message: types.Message):
            chat_id, sender, text = self.context(message)
            self.msg_in(chat_id, sender, text)
            self.msg_out(chat_id, sender, notice)

        @self.bot.message_handler(commands=["list"])
        def handle_list(message: types.Message):
            chat_id, sender, text = self.context(message)
            self.msg_in(chat_id, sender, text)
            actives = self.db.fetch(
                "get_active_requests_by_user_chat", chat_id, sender.id, 100
            )
            inactives = self.db.fetch(
                "get_inactive_requests_by_user_chat", chat_id, sender.id, 100
            )
            resp = "💾 My Alerts 💾"
            if not actives and not inactives:
                resp += "\nNo alerts"
            if actives:
                resp += f"\nActive:"
                for active in actives:
                    resp += f"\n- Alert-{active[0]}: {active[10]}"
            if inactives:
                resp += f"\nInactive:"
                for inactive in inactives:
                    resp += f"\n- Alert-{inactive[0]}: {inactive[10]}"
            self.msg_out(chat_id, sender, resp)

        @self.bot.message_handler(commands=["reset"])
        def handle_reset(message: types.Message):
            chat_id, sender, text = self.context(message)
            self.msg_in(chat_id, sender, text)
            self.db.commit("delete_all_user_requests", chat_id, sender.id)
            self.msg_out(chat_id, sender, reset)

        @self.bot.message_handler(content_types=["text"])
        def handle_message(message: types.Message):
            chat_id, sender, text = self.context(message)
            self.msg_in(chat_id, sender, text)
            msg = self.msg_out(chat_id, sender, waiting)
            if not text.startswith("#"):
                resp = self.llm.call(Prompts.default, text)
            else:
                user, name = self.myself
                if text.startswith("#tellmewhen ") and len(text) > 12:
                    parsed = self.llm.call_for_json(Prompts.analyse, text)
                    if parsed.address:
                        try:
                            parsed.address = Web3.to_checksum_address(parsed.address)
                        except Exception as e:
                            Log.info(chat_id, user, name, str(e))
                            parsed.address = None
                    if not parsed.address:
                        Log.info(
                            chat_id, user, name, "Missing or invalid contract address"
                        )
                        resp = missing
                    else:
                        Log.info(chat_id, user, name, str(parsed))
                        resp = checking
                        self.history.buffer[f"{chat_id}_{sender.id}"] = parsed
                elif (
                    text.startswith("#address ")
                    and len(text) > 9
                    and self.history.buffer[f"{chat_id}_{sender.id}"]
                ):
                    self.history.buffer[f"{chat_id}_{sender.id}"].address = (
                        Web3.to_checksum_address(text[9:])
                    )
                    Log.info(chat_id, user, name, "Added contract address")
                    resp = "Thank you! " + checking
                elif text.startswith("#on ") and len(text) > 4:
                    alert = int(text[4:])
                    self.db.commit("enable_request", alert)
                    resp = on(alert)
                elif text.startswith("#off ") and len(text) > 5:
                    alert = int(text[5:])
                    self.db.commit("disable_request", alert)
                    resp = off(alert)
            self.msg_out(chat_id, sender, resp, msg.id)
            if resp == checking:
                buffer = self.history.buffer[f"{chat_id}_{sender.id}"]
                abi = BlockExplorer.get_abi(buffer.address)
                if abi:
                    if '"name":"implementation"' in abi:
                        Log.info(chat_id, user, name, "Got ABI by it's a proxy")
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
                    Log.info(chat_id, user, name, "Got ABI")
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
                        Log.info(chat_id, user, name, "Got decimals")
                    else:
                        buffer.decimals = 0
                    buffer.method = self.llm.call_for_json(
                        Prompts.method,
                        f"Intention: {buffer.intention}\nABI: {buffer.abi}",
                    ).event
                    Log.info(chat_id, user, name, "Got event name: " + buffer.method)
                    new_id = self.db.commit(
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
                    condition = (
                        ("\nCondition: " + buffer.condition) if buffer.condition else ""
                    )
                    self.msg_out(
                        chat_id,
                        sender,
                        added(new_id)
                        + f"\nIntention: {buffer.intention}\nContract: {buffer.address}\nEvent: {buffer.method}{condition}",
                        msg.id,
                    )
                    del self.history.buffer[f"{chat_id}_{sender.id}"]
                else:
                    Log.info(chat_id, user, name, "ABI not found")

    def context(self, message: types.Message):
        return message.chat.id, message.from_user, message.text

    def start(self):
        try:
            Log.debug("Waiter: Started.")
            self.bot.infinity_polling(
                skip_pending=True, timeout=300, long_polling_timeout=300
            )
        except KeyboardInterrupt:
            Log.debug("Killed by KeyboardInterrupt")
        except Exception as e:
            Log.error(f"Error: {e}")

    def msg_in(self, chat_id, sender, text):
        if not self.history.get_user(sender.id):
            self.history.insert_user(sender.id, sender.username, sender.first_name)
        Log.received(chat_id, sender.username, sender.first_name, text)
        self.history.insert_msg(chat_id, sender.id, text)

    def msg_out(self, chat_id, receiver, text, msg_id=None):
        msg = (
            self.safe.send(text, chat_id)
            if not msg_id
            else self.safe.edit(text, chat_id, msg_id)
        )
        Log.sent(chat_id, *self.myself, text)
        self.history.insert_msg(chat_id, receiver.id, text, bot=True)
        return msg

    def notify(self, chat_id, receiver_id, text):
        self.safe.send(text, chat_id)
        Log.sent(chat_id, *self.myself, text)
        self.history.insert_msg(chat_id, receiver_id, text, bot=True)
