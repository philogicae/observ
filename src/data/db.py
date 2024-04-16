import sqlite3

from addict import Dict


class DB:
    DATA = "src/data/"
    DB = DATA + "base.db"
    SCRIPTS = DATA + "scripts/"
    READ = Dict(
        get_user="SELECT username, first_name FROM users WHERE user_id = ? LIMIT 1",
        get_users="SELECT * FROM users ORDER BY time DESC LIMIT ?",
        get_user_chat="SELECT * FROM messages WHERE chat_id = ? AND user_id = ? ORDER BY time DESC LIMIT ?",
        get_chat="SELECT * FROM messages WHERE chat_id = ? ORDER BY time DESC LIMIT ?",
        get_messages="SELECT * FROM messages ORDER BY time DESC LIMIT ?",
        get_requests="SELECT * FROM requests ORDER BY time DESC LIMIT ?",
        get_active_requests="SELECT * FROM requests WHERE active = 1 ORDER BY time DESC LIMIT ?",
        get_active_event_requests="SELECT * FROM requests WHERE active = 1 AND watch_type = 'event' ORDER BY time DESC LIMIT ?",
        get_active_call_requests="SELECT * FROM requests WHERE active = 1 AND watch_type = 'call' ORDER BY time DESC LIMIT ?",
        get_inactive_requests="SELECT * FROM requests WHERE active = 0 ORDER BY time DESC LIMIT ?",
        get_inactive_event_requests="SELECT * FROM requests WHERE active = 0 AND watch_type = 'event' ORDER BY time DESC LIMIT ?",
        get_inactive_call_requests="SELECT * FROM requests WHERE active = 0 AND watch_type = 'call' ORDER BY time DESC LIMIT ?",
        get_active_requests_by_user_chat="SELECT * FROM requests WHERE chat_id = ? AND user_id = ? AND active = 1 ORDER BY time DESC LIMIT ?",
        get_inactive_requests_by_user_chat="SELECT * FROM requests WHERE chat_id = ? AND user_id = ? AND active = 0 ORDER BY time DESC LIMIT ?",
    )
    WRITE = Dict(
        insert_user="INSERT INTO users (user_id, username, first_name, time) VALUES (?, ?, ?, datetime('now'))",
        insert_message="INSERT INTO messages (chat_id, user_id, content, agent, time) VALUES (?, ?, ?, ?, datetime('now'))",
        insert_request="INSERT INTO requests (chat_id, user_id, watch_type, addr, abi, method, args, condition, decimals, intention, active, time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, datetime('now'))",
        enable_request="UPDATE requests SET active = 1 WHERE id = ?",
        disable_request="UPDATE requests SET active = 0 WHERE id = ?",
        delete_all_user_requests="DELETE FROM requests WHERE chat_id = ? AND user_id = ?",
    )

    def reset(self):
        self.run_script("reset")
        self.run_script("init")

    def run_script(self, name, iter=1):
        with sqlite3.connect(self.DB) as db:
            c = db.cursor()
            with open(self.SCRIPTS + name + ".sql", "r") as f:
                script = f.read()
                for _ in range(iter):
                    c.executescript(script)
                db.commit()

    def fetch(self, query, *values):
        with sqlite3.connect(self.DB) as db:
            c = db.cursor()
            c.execute(self.READ.get(query), values)
            return c.fetchall()

    def commit(self, query, *values):
        with sqlite3.connect(self.DB) as db:
            c = db.cursor()
            c.execute(self.WRITE.get(query), values)
            new_id = c.lastrowid
            db.commit()
            return new_id
