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
        watch_type TEXT,
        addr TEXT,
        abi TEXT,
        method TEXT,
        args TEXT,
        condition TEXT,
        decimals INTEGER,
        active BOOLEAN,
        time TIMESTAMP
    )