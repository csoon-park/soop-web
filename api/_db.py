import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS streamers (
            id SERIAL PRIMARY KEY,
            soop_id VARCHAR(100) UNIQUE NOT NULL,
            nickname VARCHAR(200),
            access_token TEXT,
            refresh_token TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS balloon_records (
            id SERIAL PRIMARY KEY,
            streamer_id INTEGER REFERENCES streamers(id),
            user_id VARCHAR(100) NOT NULL,
            user_nickname VARCHAR(200),
            count INTEGER NOT NULL,
            tag VARCHAR(50),
            memo TEXT DEFAULT '',
            recorded_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_balloon_streamer
        ON balloon_records(streamer_id)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_balloon_user
        ON balloon_records(streamer_id, user_id)
    """)
    conn.commit()
    cur.close()
    conn.close()
