CREATE TABLE
    messages (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER,
        user_id INTEGER,
        content TEXT,
        time TIMESTAMP
    );