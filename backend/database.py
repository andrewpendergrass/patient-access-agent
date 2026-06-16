import json
import uuid
import aiosqlite
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "audit.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                request TEXT NOT NULL,
                intent TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                response TEXT NOT NULL,
                case_summary TEXT NOT NULL,
                steps TEXT NOT NULL
            )
        """)
        await db.commit()


async def log_case(
    request: str,
    intent: str,
    risk_level: str,
    response: str,
    case_summary: dict,
    steps: list,
) -> str:
    case_id = f"PAT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO cases (id, created_at, request, intent, risk_level, response, case_summary, steps)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                case_id,
                datetime.utcnow().isoformat(),
                request,
                intent,
                risk_level,
                response,
                json.dumps(case_summary),
                json.dumps(steps),
            ),
        )
        await db.commit()
    return case_id


async def get_cases(limit: int = 50) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM cases ORDER BY created_at DESC LIMIT ?", (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
    results = []
    for row in rows:
        r = dict(row)
        r["case_summary"] = json.loads(r["case_summary"])
        r["steps"] = json.loads(r["steps"])
        results.append(r)
    return results
