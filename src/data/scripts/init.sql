CREATE TABLE
    messages (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER,
        user_id INTEGER,
        content TEXT,
        time TIMESTAMP
    );

CREATE TABLE
    requests (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER,
        user_id INTEGER,
        data TEXT,
        type TEXT,
        condition TEXT,
        active BOOLEAN,
        time TIMESTAMP
    )