from app.models.db import init_db, get_connection
from app.models.user import UserRepository

init_db()

with get_connection() as conn:
    conn.execute("DELETE FROM users WHERE username=?", ("admin",))
    conn.execute("UPDATE users SET status=1 WHERE status IS NULL OR status=0 AND id>0")
    conn.commit()

result = UserRepository.create_user("admin", "admin888", role="admin", remark="系统管理员")
print("创建 admin 账号:", result)

user = UserRepository.get_user_by_username("admin")
print("用户信息:", dict(user) if user else None)

verify = UserRepository.verify_user("admin", "admin888")
print("登录验证:", verify)
