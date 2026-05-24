import hashlib
import secrets
import sqlite3

from app.models.db import get_connection

def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return dk.hex()

class UserRepository:
    @staticmethod
    def create_user(username: str, password: str, role: str = "user", remark: str = "") -> bool:
        salt = secrets.token_bytes(16)
        password_hash = _hash_password(password, salt)
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO users(username,password_hash,salt,role,remark) VALUES(?,?,?,?,?)",
                    (username, password_hash, salt.hex(), role, remark),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def get_user_by_username(username: str):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id,username,role,status,remark,password_hash,salt,create_at,update_at FROM users WHERE username = ?",
                (username,)
            ).fetchone()
        return row

    @staticmethod
    def verify_user(username: str, password: str) -> bool:
        row = UserRepository.get_user_by_username(username)
        if not row:
            return False
        if row["status"] != 1:
            return False
        salt = bytes.fromhex(row["salt"])
        return _hash_password(password, salt) == row["password_hash"]

    @staticmethod
    def get_user_list(page: int = 1, page_size: int = 20, keyword: str = "", role: str = "", status: int = -1):
        offset = (page - 1) * page_size
        conditions = []
        params = []
        if keyword:
            conditions.append("username LIKE ?")
            params.append(f"%{keyword}%")
        if role:
            conditions.append("u.role = ?")
            params.append(role)
        if status >= 0:
            conditions.append("u.status = ?")
            params.append(status)
        where = " AND ".join(conditions) if conditions else "1=1"
        with get_connection() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM users u WHERE {where}", params
            ).fetchone()[0]
            rows = conn.execute(
                f"SELECT u.id,u.username,u.role,r.role_name as role_display,u.status,u.remark,u.create_at,u.update_at FROM users u LEFT JOIN roles r ON u.role=r.role_code WHERE {where} ORDER BY u.id DESC LIMIT ? OFFSET ?",
                params + [page_size, offset]
            ).fetchall()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "data": [dict(r) for r in rows]
        }

    @staticmethod
    def update_user(user_id: int, role: str = None, status: int = None, remark: str = None, password: str = None) -> bool:
        row = UserRepository.get_user_by_id(user_id)
        if not row:
            return False
        if row["username"] == "admin":
            role = None
            status = None
            remark = None
        fields = []
        params = []
        if role is not None:
            fields.append("role = ?")
            params.append(role)
        if status is not None:
            fields.append("status = ?")
            params.append(status)
        if remark is not None:
            fields.append("remark = ?")
            params.append(remark)
        if password is not None:
            salt = secrets.token_bytes(16)
            password_hash = _hash_password(password, salt)
            fields.append("password_hash = ?")
            params.append(password_hash)
            fields.append("salt = ?")
            params.append(salt.hex())
        if not fields:
            return False
        fields.append("update_at = datetime('now')")
        params.append(user_id)
        try:
            with get_connection() as conn:
                conn.execute(
                    f"UPDATE users SET {', '.join(fields)} WHERE id = ?",
                    params
                )
            return True
        except Exception:
            return False

    @staticmethod
    def get_user_by_id(user_id: int):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id,username,role,status,remark,password_hash,salt,create_at,update_at FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def delete_user(user_id: int) -> bool:
        try:
            with get_connection() as conn:
                row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
                if row and row["username"] == "admin":
                    return False
                conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            return True
        except Exception:
            return False

    @staticmethod
    def batch_delete_user(user_ids: list) -> bool:
        try:
            with get_connection() as conn:
                placeholders = ",".join("?" for _ in user_ids)
                conn.execute(f"DELETE FROM users WHERE id IN ({placeholders}) AND username != 'admin'", user_ids)
            return True
        except Exception:
            return False

    @staticmethod
    def get_all_roles():
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id,role_code,role_name,description,status FROM roles WHERE status = 1 ORDER BY id"
            ).fetchall()
        return [dict(r) for r in rows]
