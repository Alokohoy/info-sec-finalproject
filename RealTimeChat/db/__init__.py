import sqlite3
import pathlib
import contextlib

DB_FILE = pathlib.Path(__file__).parent.parent / "chat.db"


def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def init_db():
    create_sql = """
    CREATE TABLE IF NOT EXISTS messages (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT    NOT NULL,
        text TEXT    NOT NULL,
        ts   DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    with contextlib.closing(get_conn()) as con:
        con.execute(create_sql)
        con.commit()


def save_message(user: str, text: str) -> None:
    with contextlib.closing(get_conn()) as con:
        con.execute(
            "INSERT INTO messages (user, text) VALUES (?, ?)",
            (user, text),
        )
        con.commit()


def clear_messages() -> None:
    with contextlib.closing(get_conn()) as con:
        con.execute("DELETE FROM messages;")
        con.commit()


def latest_messages(limit: int = 50):
    with contextlib.closing(get_conn()) as con:
        cur = con.execute(
            "SELECT user, text, ts FROM messages ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(zip(("username", "text", "ts"), row)) for row in cur]