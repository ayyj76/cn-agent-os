from app.models.db import get_connection


class ModelServiceRepository:
    @staticmethod
    def get_all_models():
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id,model_name,model_code,api_base_url,api_key,is_default,status,description,total_tokens,request_count,create_at,update_at FROM model_services ORDER BY is_default DESC, create_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def get_model_by_id(model_id):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id,model_name,model_code,api_base_url,api_key,is_default,status,description,total_tokens,request_count,create_at,update_at FROM model_services WHERE id=?",
                (model_id,)
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_default_model():
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id,model_name,model_code,api_base_url,api_key,is_default,status,description,total_tokens,request_count FROM model_services WHERE is_default=1 AND status=1"
            ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def add_model(model_name, model_code, api_base_url, api_key, description="", is_default=0):
        try:
            with get_connection() as conn:
                if is_default:
                    conn.execute("UPDATE model_services SET is_default=0")
                conn.execute(
                    "INSERT INTO model_services(model_name,model_code,api_base_url,api_key,is_default,description) VALUES(?,?,?,?,?,?)",
                    (model_name, model_code, api_base_url, api_key, is_default, description)
                )
            return True
        except Exception:
            return False

    @staticmethod
    def update_model(model_id, model_name=None, model_code=None, api_base_url=None, api_key=None, description=None, status=None, is_default=None):
        try:
            with get_connection() as conn:
                if is_default:
                    conn.execute("UPDATE model_services SET is_default=0")
                fields = []
                params = []
                if model_name is not None:
                    fields.append("model_name=?"); params.append(model_name)
                if model_code is not None:
                    fields.append("model_code=?"); params.append(model_code)
                if api_base_url is not None:
                    fields.append("api_base_url=?"); params.append(api_base_url)
                if api_key is not None:
                    fields.append("api_key=?"); params.append(api_key)
                if description is not None:
                    fields.append("description=?"); params.append(description)
                if status is not None:
                    fields.append("status=?"); params.append(status)
                if is_default is not None:
                    fields.append("is_default=?"); params.append(is_default)
                if not fields:
                    return False
                fields.append("update_at=datetime('now')")
                params.append(model_id)
                conn.execute(f"UPDATE model_services SET {', '.join(fields)} WHERE id=?", params)
            return True
        except Exception:
            return False

    @staticmethod
    def delete_model(model_id):
        try:
            with get_connection() as conn:
                conn.execute("DELETE FROM model_token_logs WHERE model_id=?", (model_id,))
                conn.execute("DELETE FROM model_services WHERE id=?", (model_id,))
            return True
        except Exception:
            return False

    @staticmethod
    def get_token_stats(model_id=None, limit=30):
        with get_connection() as conn:
            if model_id:
                rows = conn.execute(
                    "SELECT id,model_id,prompt_tokens,completion_tokens,total_tokens,duration_ms,success,create_at FROM model_token_logs WHERE model_id=? ORDER BY create_at DESC LIMIT ?",
                    (model_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id,model_id,prompt_tokens,completion_tokens,total_tokens,duration_ms,success,create_at FROM model_token_logs ORDER BY create_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def add_token_log(model_id, prompt_tokens, completion_tokens, total_tokens, duration_ms, success=1):
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO model_token_logs(model_id,prompt_tokens,completion_tokens,total_tokens,duration_ms,success) VALUES(?,?,?,?,?,?)",
                    (model_id, prompt_tokens, completion_tokens, total_tokens, duration_ms, success)
                )
                conn.execute(
                    "UPDATE model_services SET total_tokens=total_tokens+?, request_count=request_count+1, update_at=datetime('now') WHERE id=?",
                    (total_tokens, model_id)
                )
            return True
        except Exception:
            return False