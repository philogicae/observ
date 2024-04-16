from logging import INFO, basicConfig, getLogger

from rich.logging import RichHandler

basicConfig(
    format="%(message)s", datefmt="[%d-%m %X]", level=INFO, handlers=[RichHandler()]
)
logger = getLogger("rich")
shorten = lambda text: text[0:100] + ("..." if len(text) > 250 else "")
msg_log = lambda log_type, chat_id, user, name, log, full=True: logger.info(
    f"{log_type}[{chat_id}](@{user}) {name}: {log if full else shorten(log)}"
)


class Log:
    debug = logger.info
    error = logger.error
    sent = lambda chat_id, user, name, log: msg_log("<--", chat_id, user, name, log)
    received = lambda chat_id, user, name, log: msg_log("-->", chat_id, user, name, log)
    info = lambda chat_id, user, name, log: msg_log("-X-", chat_id, user, name, log)
