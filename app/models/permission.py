from app.models.db import get_connection


class ModuleRepository:
    @staticmethod
    def get_all_modules():
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id,module_code,module_name,icon,href,sort_order,status,parent_id,description,create_at FROM modules ORDER BY sort_order"
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add_module(module_code, module_name, icon, href, sort_order, status, parent_id=0, description=""):
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO modules(module_code,module_name,icon,href,sort_order,status,parent_id,description) VALUES(?,?,?,?,?,?,?,?)",
                    (module_code, module_name, icon, href, sort_order, status, parent_id, description)
                )
            return True
        except Exception:
            return False

    @staticmethod
    def update_module(module_id, module_name=None, icon=None, href=None, sort_order=None, status=None, parent_id=None, description=None):
        fields = []
        params = []
        if module_name is not None:
            fields.append("module_name=?"); params.append(module_name)
        if icon is not None:
            fields.append("icon=?"); params.append(icon)
        if href is not None:
            fields.append("href=?"); params.append(href)
        if sort_order is not None:
            fields.append("sort_order=?"); params.append(sort_order)
        if status is not None:
            fields.append("status=?"); params.append(status)
        if parent_id is not None:
            fields.append("parent_id=?"); params.append(parent_id)
        if description is not None:
            fields.append("description=?"); params.append(description)
        if not fields:
            return False
        params.append(module_id)
        try:
            with get_connection() as conn:
                conn.execute(f"UPDATE modules SET {', '.join(fields)} WHERE id=?", params)
            return True
        except Exception:
            return False

    @staticmethod
    def delete_module(module_id):
        try:
            with get_connection() as conn:
                conn.execute("DELETE FROM modules WHERE id=?", (module_id,))
            return True
        except Exception:
            return False


class PermissionRepository:
    @staticmethod
    def get_permissions_by_module(module_id):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT p.id,p.module_id,m.module_code,m.module_name,p.permission_code,p.permission_name,p.description,p.create_at FROM permissions p LEFT JOIN modules m ON p.module_id=m.id WHERE p.module_id=? ORDER BY p.id",
                (module_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_all_permissions():
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT p.id,p.module_id,m.module_code,m.module_name,p.permission_code,p.permission_name,p.description,p.create_at FROM permissions p LEFT JOIN modules m ON p.module_id=m.id ORDER BY m.sort_order, p.id"
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add_permission(module_id, permission_code, permission_name, description=""):
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO permissions(module_id,permission_code,permission_name,description) VALUES(?,?,?,?)",
                    (module_id, permission_code, permission_name, description)
                )
            return True
        except Exception:
            return False

    @staticmethod
    def update_permission(permission_id, module_id=None, permission_code=None, permission_name=None, description=None):
        fields = []
        params = []
        if module_id is not None:
            fields.append("module_id=?"); params.append(module_id)
        if permission_code is not None:
            fields.append("permission_code=?"); params.append(permission_code)
        if permission_name is not None:
            fields.append("permission_name=?"); params.append(permission_name)
        if description is not None:
            fields.append("description=?"); params.append(description)
        if not fields:
            return False
        params.append(permission_id)
        try:
            with get_connection() as conn:
                conn.execute(f"UPDATE permissions SET {', '.join(fields)} WHERE id=?", params)
            return True
        except Exception:
            return False

    @staticmethod
    def delete_permission(permission_id):
        try:
            with get_connection() as conn:
                conn.execute("DELETE FROM permissions WHERE id=?", (permission_id,))
            return True
        except Exception:
            return False


class RoleRepository:
    @staticmethod
    def get_all_roles():
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id,role_code,role_name,description,status,is_default,create_at FROM roles ORDER BY id"
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add_role(role_code, role_name, description="", status=1):
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO roles(role_code,role_name,description,status) VALUES(?,?,?,?)",
                    (role_code, role_name, description, status)
                )
            return True
        except Exception:
            return False

    @staticmethod
    def update_role(role_id, role_name=None, description=None, status=None):
        fields = []
        params = []
        if role_name is not None:
            fields.append("role_name=?"); params.append(role_name)
        if description is not None:
            fields.append("description=?"); params.append(description)
        if status is not None:
            fields.append("status=?"); params.append(status)
        if not fields:
            return False
        params.append(role_id)
        try:
            with get_connection() as conn:
                conn.execute(f"UPDATE roles SET {', '.join(fields)} WHERE id=?", params)
            return True
        except Exception:
            return False

    @staticmethod
    def delete_role(role_id):
        try:
            with get_connection() as conn:
                row = conn.execute("SELECT is_default FROM roles WHERE id=?", (role_id,)).fetchone()
                if row and row["is_default"] == 1:
                    return False
                conn.execute("DELETE FROM roles WHERE id=?", (role_id,))
                conn.execute("DELETE FROM role_permissions WHERE role_id=?", (role_id,))
            return True
        except Exception:
            return False

    @staticmethod
    def get_role_permissions(role_id):
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT permission_id FROM role_permissions WHERE role_id=?", (role_id,)
            ).fetchall()
        return [r["permission_id"] for r in rows]

    @staticmethod
    def assign_permissions(role_id, permission_ids):
        try:
            with get_connection() as conn:
                conn.execute("DELETE FROM role_permissions WHERE role_id=?", (role_id,))
                for pid in permission_ids:
                    if pid:
                        conn.execute(
                            "INSERT INTO role_permissions(role_id,permission_id) VALUES(?,?)",
                            (role_id, int(pid))
                        )
            return True
        except Exception:
            return False
