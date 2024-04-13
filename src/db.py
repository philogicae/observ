import sqlite3
from addict import Dict


class DB:
    DATA = "src/data/"
    DB = DATA + "base.db"
    SCRIPTS = DATA + "scripts/"
    READ = Dict(
        get_messages="SELECT * FROM messages ORDER BY time DESC LIMIT 100",
    )
    WRITE = Dict(
        insert_message="INSERT INTO messages (chat_id, user_id, content, time) VALUES (?, ?, ?, datetime('now'))",
        update_message="UPDATE messages SET content = ?, time = datetime('now') WHERE id = ?",
    )

    def __init__(self):
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

    def fetch(self, query):
        with sqlite3.connect(self.DB) as db:
            c = db.cursor()
            c.execute(self.READ.get(query))
            return c.fetchall()

    def commit(self, query, *values):
        with sqlite3.connect(self.DB) as db:
            c = db.cursor()
            c.execute(self.WRITE.get(query), values)
            db.commit()
