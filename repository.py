"""Every line that talks to Postgres lives in this module."""
import os
import time

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

SEED_TASKS = [("Buy milk", False), ("Walk the dog", False), ("Write README", True)]
COLUMNS = "id, title, done"


def database_url() -> str:
    return os.environ["DATABASE_URL"]


def connect():
    return psycopg.connect(database_url(), row_factory=dict_row)


def init_db(retries: int = 30) -> None:
    """Create the tasks table if missing; seed three rows only when it is empty.

    Retries because under docker compose the API can start before Postgres accepts connections.
    """
    for attempt in range(retries):
        try:
            conn = connect()
            break
        except psycopg.OperationalError:
            if attempt == retries - 1:
                raise
            time.sleep(1)
    with conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS tasks ("
            "id SERIAL PRIMARY KEY, title TEXT NOT NULL, done BOOLEAN NOT NULL DEFAULT FALSE)"
        )
        count = conn.execute("SELECT COUNT(*) AS n FROM tasks").fetchone()["n"]
        if count == 0:
            with conn.cursor() as cur:
                cur.executemany("INSERT INTO tasks (title, done) VALUES (%s, %s)", SEED_TASKS)
    conn.close()
