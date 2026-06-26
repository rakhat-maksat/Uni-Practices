import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

DB_CONFIG = {
    "host":     "localhost",
    "database": "snake",
    "user":     "rakhatmaksat",
    "password": "",
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def init_db():
    sql = """
    CREATE TABLE IF NOT EXISTS players (
        id       SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS game_sessions (
        id            SERIAL PRIMARY KEY,
        player_id     INTEGER REFERENCES players(id),
        score         INTEGER   NOT NULL,
        level_reached INTEGER   NOT NULL,
        played_at     TIMESTAMP DEFAULT NOW()
    );
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

# получить или создать игрока 

def get_or_create_player(username: str) -> int:
    """Возвращает player_id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM players WHERE username = %s", (username,))
            row = cur.fetchone()
            if row:
                return row[0]
            cur.execute(
                "INSERT INTO players (username) VALUES (%s) RETURNING id",
                (username,)
            )
            player_id = cur.fetchone()[0]
        conn.commit()
    return player_id

#сохранить 

def save_session(username: str, score: int, level_reached: int):
    player_id = get_or_create_player(username)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO game_sessions (player_id, score, level_reached)
                VALUES (%s, %s, %s)
                """,
                (player_id, score, level_reached)
            )
        conn.commit()

# топ-10 

def get_top10():
    """
    Возвращает список словарей:
    [{"rank": 1, "username": "...", "score": ..., "level": ..., "date": "..."}, ...]
    """
    sql = """
    SELECT
        ROW_NUMBER() OVER (ORDER BY gs.score DESC) AS rank,
        p.username,
        gs.score,
        gs.level_reached,
        gs.played_at
    FROM game_sessions gs
    JOIN players p ON p.id = gs.player_id
    ORDER BY gs.score DESC
    LIMIT 10
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    result = []
    for row in rows:
        result.append({
            "rank":     row["rank"],
            "username": row["username"],
            "score":    row["score"],
            "level":    row["level_reached"],
            "date":     row["played_at"].strftime("%Y-%m-%d") if row["played_at"] else "-",
        })
    return result

# личный рекорд игрока

def get_personal_best(username: str) -> int:
    """Возвращает лучший счёт игрока или 0 если игрока нет."""
    sql = """
    SELECT MAX(gs.score)
    FROM game_sessions gs
    JOIN players p ON p.id = gs.player_id
    WHERE p.username = %s
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (username,))
            row = cur.fetchone()
    if row and row[0] is not None:
        return row[0]
    return 0