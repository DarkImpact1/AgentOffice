import aiosqlite
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, List, Dict

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    source_agent TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    due_date TEXT,
    metadata TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_states (
    agent_name TEXT PRIMARY KEY,
    status TEXT DEFAULT 'idle',
    last_run TEXT,
    last_result TEXT,
    error_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cached INTEGER DEFAULT 0,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cache (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    job_title TEXT NOT NULL,
    job_url TEXT,
    budget TEXT,
    proposal TEXT,
    status TEXT DEFAULT 'draft',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS platform_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    status TEXT NOT NULL,
    earnings TEXT,
    available_tasks INTEGER,
    details TEXT,
    checked_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(source_agent);
CREATE INDEX IF NOT EXISTS idx_token_usage_agent ON token_usage(agent_name);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at);
"""


class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        if not self._conn:
            raise RuntimeError("Database not connected")
        return self._conn

    async def execute(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        cursor = await self.conn.execute(query, params)
        await self.conn.commit()
        return cursor

    async def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        cursor = await self.conn.execute(query, params)
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        cursor = await self.conn.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def add_task(
        self,
        title: str,
        source_agent: str,
        description: str = "",
        priority: int = 0,
        due_date: Optional[str] = None,
        metadata: str = "",
    ) -> int:
        cursor = await self.execute(
            """INSERT INTO tasks (title, description, source_agent, priority, due_date, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (title, description, source_agent, priority, due_date, metadata),
        )
        return cursor.lastrowid or 0

    async def get_tasks(self, status: Optional[str] = None, agent: Optional[str] = None) -> List[Dict]:
        query = "SELECT * FROM tasks WHERE 1=1"
        params: List[Any] = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if agent:
            query += " AND source_agent = ?"
            params.append(agent)
        query += " ORDER BY priority DESC, created_at DESC"
        return await self.fetch_all(query, tuple(params))

    async def update_task_status(self, task_id: int, status: str) -> None:
        await self.execute(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
            (status, datetime.now().isoformat(), task_id),
        )

    async def log_token_usage(
        self, agent: str, model: str, input_tokens: int, output_tokens: int, cached: bool = False
    ) -> None:
        await self.execute(
            "INSERT INTO token_usage (agent_name, model, input_tokens, output_tokens, cached) VALUES (?, ?, ?, ?, ?)",
            (agent, model, input_tokens, output_tokens, int(cached)),
        )

    async def get_token_stats(self, agent: Optional[str] = None) -> Dict:
        query = "SELECT SUM(input_tokens) as input, SUM(output_tokens) as output FROM token_usage"
        params: tuple = ()
        if agent:
            query += " WHERE agent_name = ?"
            params = (agent,)
        result = await self.fetch_one(query, params)
        return {"input_tokens": result.get("input") or 0, "output_tokens": result.get("output") or 0} if result else {"input_tokens": 0, "output_tokens": 0}

    async def set_cache(self, key: str, value: str, expires_at: str) -> None:
        await self.execute(
            "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
            (key, value, expires_at),
        )

    async def get_cache(self, key: str) -> Optional[str]:
        now = datetime.now().isoformat()
        result = await self.fetch_one(
            "SELECT value FROM cache WHERE key = ? AND expires_at > ?", (key, now)
        )
        return result["value"] if result else None

    async def clear_expired_cache(self) -> None:
        await self.execute("DELETE FROM cache WHERE expires_at < ?", (datetime.now().isoformat(),))

    async def update_agent_state(self, agent: str, status: str, result: str = "") -> None:
        await self.execute(
            """INSERT OR REPLACE INTO agent_states (agent_name, status, last_run, last_result)
               VALUES (?, ?, ?, ?)""",
            (agent, status, datetime.now().isoformat(), result),
        )

    async def get_agent_state(self, agent: str) -> Optional[Dict]:
        return await self.fetch_one("SELECT * FROM agent_states WHERE agent_name = ?", (agent,))

    async def add_job_application(
        self, platform: str, job_title: str, job_url: str, budget: str, proposal: str
    ) -> int:
        cursor = await self.execute(
            "INSERT INTO job_applications (platform, job_title, job_url, budget, proposal) VALUES (?, ?, ?, ?, ?)",
            (platform, job_title, job_url, budget, proposal),
        )
        return cursor.lastrowid or 0

    async def get_pending_applications(self) -> List[Dict]:
        return await self.fetch_all(
            "SELECT * FROM job_applications WHERE status = 'draft' ORDER BY created_at DESC"
        )

    async def approve_application(self, app_id: int) -> None:
        await self.execute("UPDATE job_applications SET status = 'approved' WHERE id = ?", (app_id,))

    async def add_platform_status(
        self, platform: str, status: str, earnings: str = "", available_tasks: int = 0, details: str = ""
    ) -> None:
        await self.execute(
            "INSERT INTO platform_status (platform, status, earnings, available_tasks, details) VALUES (?, ?, ?, ?, ?)",
            (platform, status, earnings, available_tasks, details),
        )

    async def get_latest_platform_status(self) -> List[Dict]:
        return await self.fetch_all(
            """SELECT * FROM platform_status WHERE id IN 
               (SELECT MAX(id) FROM platform_status GROUP BY platform)"""
        )
