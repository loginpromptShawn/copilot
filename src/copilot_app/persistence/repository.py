from .database import get_connection
from .models import User, SystemInfo


class UserRepository:
    def create_user(self, name: str) -> User:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name) VALUES (?)", (name,))
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return User(id=user_id, name=name)

    def get_user(self, id: int) -> User | None:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM users WHERE id = ?", (id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return User(id=row["id"], name=row["name"])
        return None

    def list_users(self) -> list[User]:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM users ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return [User(id=r["id"], name=r["name"]) for r in rows]


class SystemInfoRepository:
    def save_system_info(self, os: str, version: str) -> SystemInfo:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO system_info (os, version) VALUES (?, ?)", (os, version)
        )
        conn.commit()
        info_id = cur.lastrowid
        conn.close()
        return SystemInfo(id=info_id, os=os, version=version)

    def get_latest_system_info(self) -> SystemInfo | None:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, os, version FROM system_info ORDER BY id DESC LIMIT 1"
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return SystemInfo(id=row["id"], os=row["os"], version=row["version"])
        return None
