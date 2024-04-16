CREATE TABLE
    users (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        username TEXT,
        first_name TEXT,
        time TIMESTAMP
    );

CREATE TABLE
    messages (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER,
        user_id INTEGER,
        content TEXT,
        agent TEXT,
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
        intention TEXT,
        active BOOLEAN,
        time TIMESTAMP
    )