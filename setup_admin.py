from app.models.db import init_db, get_connection
from app.models.user import UserRepository
import random
import datetime

print("正在初始化数据库结构...")
init_db()

with get_connection() as conn:
    # 清理已有数据以进行干净重置
    conn.execute("DELETE FROM users WHERE username IN ('admin', 'user1', 'editor1', 'ops_dev')")
    conn.execute("DELETE FROM roles WHERE role_code IN ('editor', 'ops')")
    conn.execute("DELETE FROM model_services WHERE model_code = 'claude-3-5-sonnet'")
    conn.execute("DELETE FROM model_token_logs")
    conn.execute("UPDATE model_services SET total_tokens=0, request_count=0")
    
    # 1. 插入新角色
    conn.execute(
        "INSERT INTO roles(role_code, role_name, description, status) VALUES('editor', '内容编辑员', '负责数字员工会话及内容模板编辑', 1)"
    )
    conn.execute(
        "INSERT INTO roles(role_code, role_name, description, status) VALUES('ops', '系统运维专员', '负责模型接口及资源监控运维', 1)"
    )
    
    # 获取角色 ID 并分配部分权限
    editor_role = conn.execute("SELECT id FROM roles WHERE role_code = 'editor'").fetchone()
    ops_role = conn.execute("SELECT id FROM roles WHERE role_code = 'ops'").fetchone()
    
    # 给运维分配系统监控/模型相关模块权限
    all_perms = conn.execute("SELECT id, permission_code FROM permissions").fetchall()
    for perm in all_perms:
        # 给编辑角色分配基础查看和列表权限
        if 'list' in perm['permission_code'] or 'view' in perm['permission_code']:
            conn.execute("INSERT OR IGNORE INTO role_permissions(role_id, permission_id) VALUES(?, ?)", (editor_role['id'], perm['id']))
        # 给运维角色分配编辑和查看权限
        if 'user' not in perm['permission_code']:
            conn.execute("INSERT OR IGNORE INTO role_permissions(role_id, permission_id) VALUES(?, ?)", (ops_role['id'], perm['id']))

    # 2. 插入一个新的模型服务
    conn.execute(
        """
        INSERT OR IGNORE INTO model_services(model_name, model_code, api_base_url, api_key, is_default, status, description)
        VALUES(?, ?, ?, ?, ?, ?, ?)
        """,
        ("Claude-3.5-Sonnet", "claude-3-5-sonnet", "https://api.anthropic.com/v1", "sk-ant-dummykey123456", 0, 1, "Anthropic 高级推理模型，适用于复杂智能 Agent 任务")
    )
    
    # 3. 为模型生成模拟 token 消耗数据，使柱状图立即可见
    model_ds = conn.execute("SELECT id FROM model_services WHERE model_code = 'deepseek-v3'").fetchone()
    model_claude = conn.execute("SELECT id FROM model_services WHERE model_code = 'claude-3-5-sonnet'").fetchone()
    
    now = datetime.datetime.now()
    if model_ds:
        ds_id = model_ds['id']
        total_toks = 0
        req_cnt = 0
        for i in range(15):
            p_tok = random.randint(100, 3000)
            c_tok = random.randint(200, 5000)
            t_tok = p_tok + c_tok
            dur = random.randint(800, 4000)
            success = 1 if random.random() > 0.05 else 0
            log_time = (now - datetime.timedelta(minutes=30 * (15 - i))).strftime("%Y-%m-%d %H:%M:%S")
            
            conn.execute(
                "INSERT INTO model_token_logs(model_id, prompt_tokens, completion_tokens, total_tokens, duration_ms, success, create_at) VALUES(?,?,?,?,?,?,?)",
                (ds_id, p_tok, c_tok, t_tok, dur, success, log_time)
            )
            if success:
                total_toks += t_tok
                req_cnt += 1
        conn.execute("UPDATE model_services SET total_tokens=?, request_count=? WHERE id=?", (total_toks, req_cnt, ds_id))

    if model_claude:
        cl_id = model_claude['id']
        total_toks = 0
        req_cnt = 0
        for i in range(10):
            p_tok = random.randint(200, 4000)
            c_tok = random.randint(400, 6000)
            t_tok = p_tok + c_tok
            dur = random.randint(1200, 5000)
            success = 1
            log_time = (now - datetime.timedelta(minutes=45 * (10 - i))).strftime("%Y-%m-%d %H:%M:%S")
            
            conn.execute(
                "INSERT INTO model_token_logs(model_id, prompt_tokens, completion_tokens, total_tokens, duration_ms, success, create_at) VALUES(?,?,?,?,?,?,?)",
                (cl_id, p_tok, c_tok, t_tok, dur, success, log_time)
            )
            total_toks += t_tok
            req_cnt += 1
        conn.execute("UPDATE model_services SET total_tokens=?, request_count=? WHERE id=?", (total_toks, req_cnt, cl_id))

    conn.commit()

# 4. 插入多组模拟测试账号
UserRepository.create_user("admin", "admin888", role="admin", remark="系统超级管理员，拥有全局控制权限")
UserRepository.create_user("user1", "123456", role="user", remark="外部合作伙伴对接测试账号")
UserRepository.create_user("editor1", "123456", role="editor", remark="数字员工内容编辑员，拥有部分查阅权限")
UserRepository.create_user("ops_dev", "123456", role="ops", remark="系统运维人员，负责日常接口监控")

print("===== 数据库初始化与模拟数据填充完成 =====")
print("1. 管理员账号: admin / admin888 (超级管理员)")
print("2. 演示账号1: user1 / 123456 (普通用户)")
print("3. 演示账号2: editor1 / 123456 (编辑角色)")
print("4. 演示账号3: ops_dev / 123456 (运维角色)")
print("5. 演示模型: 已初始化 DeepSeek-V3 与 Claude-3.5-Sonnet，并填充 25 条 Token 日志")

