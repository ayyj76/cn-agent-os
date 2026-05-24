#数据库链接与建表
import os
import sqlite3

#获得项目根路径的方法
def _project_root():
	return os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir, os.pardir))

DB_PATH = os.path.join(_project_root(),"database","app.db")

def get_connection():
	os.makedirs(os.path.dirname(DB_PATH),exist_ok=True)
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	conn.execute("PRAGMA journal_mode=WAL")
	return conn

def init_db():
	with get_connection() as conn:
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS users(
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				username TEXT NOT NULL UNIQUE,
				password_hash TEXT NOT NULL,
				salt TEXT NOT NULL,
				role TEXT NOT NULL DEFAULT 'user',
				status INTEGER NOT NULL DEFAULT 1,
				remark TEXT DEFAULT '',
				create_at TEXT NOT NULL DEFAULT (datetime('now')),
				update_at TEXT NOT NULL DEFAULT ''
			)
			"""
		)
		cursor = conn.execute("PRAGMA table_info(users)")
		existing_columns = [row[1] for row in cursor.fetchall()]
		if "role" not in existing_columns:
			conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
		if "status" not in existing_columns:
			conn.execute("ALTER TABLE users ADD COLUMN status INTEGER NOT NULL DEFAULT 1")
		if "remark" not in existing_columns:
			conn.execute("ALTER TABLE users ADD COLUMN remark TEXT DEFAULT ''")
		if "update_at" not in existing_columns:
			conn.execute("ALTER TABLE users ADD COLUMN update_at TEXT NOT NULL DEFAULT ''")

		# 角色表
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS roles(
				id integer PRIMARY KEY AUTOINCREMENT,
				role_code TEXT NOT NULL UNIQUE,
				role_name TEXT NOT NULL,
				description TEXT DEFAULT '',
				status INTEGER NOT NULL DEFAULT 1,
				is_default INTEGER NOT NULL DEFAULT 0,
				create_at TEXT NOT NULL DEFAULT (datetime('now'))
				)
			"""
			)
		cursor_roles = conn.execute("PRAGMA table_info(roles)")
		existing_role_cols = [row[1] for row in cursor_roles.fetchall()]
		if "is_default" not in existing_role_cols:
			conn.execute("ALTER TABLE roles ADD COLUMN is_default INTEGER NOT NULL DEFAULT 0")

		# 用户角色关联表
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS user_roles(
				id integer PRIMARY KEY AUTOINCREMENT,
				user_id INTEGER NOT NULL,
				role_id INTEGER NOT NULL,
				FOREIGN KEY(user_id) REFERENCES users(id),
				FOREIGN KEY(role_id) REFERENCES roles(id)
				)
			"""
			)

		# 功能模块表
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS modules(
				id integer PRIMARY KEY AUTOINCREMENT,
				module_code TEXT NOT NULL UNIQUE,
				module_name TEXT NOT NULL,
				icon TEXT DEFAULT '',
				href TEXT DEFAULT '',
				sort_order INTEGER NOT NULL DEFAULT 0,
				status INTEGER NOT NULL DEFAULT 1,
				parent_id INTEGER NOT NULL DEFAULT 0,
				description TEXT DEFAULT '',
				create_at TEXT NOT NULL DEFAULT (datetime('now'))
				)
			"""
			)

		# 权限表
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS permissions(
				id integer PRIMARY KEY AUTOINCREMENT,
				module_id INTEGER NOT NULL,
				permission_code TEXT NOT NULL,
				permission_name TEXT NOT NULL,
				description TEXT DEFAULT '',
				create_at TEXT NOT NULL DEFAULT (datetime('now')),
				FOREIGN KEY(module_id) REFERENCES modules(id),
				UNIQUE(module_id, permission_code)
				)
			"""
			)

		# 迁移：为已存在的 permissions 表补 create_at 列
		cursor_perms = conn.execute("PRAGMA table_info(permissions)")
		existing_perm_cols = [row[1] for row in cursor_perms.fetchall()]
		if "create_at" not in existing_perm_cols:
			conn.execute("ALTER TABLE permissions ADD COLUMN create_at TEXT NOT NULL DEFAULT '1970-01-01 00:00:00'")
			conn.execute("UPDATE permissions SET create_at = datetime('now') WHERE create_at = '1970-01-01 00:00:00'")

		# 角色权限关联表
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS role_permissions(
				id integer PRIMARY KEY AUTOINCREMENT,
				role_id INTEGER NOT NULL,
				permission_id INTEGER NOT NULL,
				FOREIGN KEY(role_id) REFERENCES roles(id),
				FOREIGN KEY(permission_id) REFERENCES permissions(id),
				UNIQUE(role_id, permission_id)
				)
			"""
			)

		# 模型服务配置表
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS model_services(
				id integer PRIMARY KEY AUTOINCREMENT,
				model_name TEXT NOT NULL,
				model_code TEXT NOT NULL UNIQUE,
				api_base_url TEXT NOT NULL,
				api_key TEXT NOT NULL,
				is_default INTEGER NOT NULL DEFAULT 0,
				status INTEGER NOT NULL DEFAULT 1,
				description TEXT DEFAULT '',
				total_tokens INTEGER NOT NULL DEFAULT 0,
				request_count INTEGER NOT NULL DEFAULT 0,
				create_at TEXT NOT NULL DEFAULT (datetime('now')),
				update_at TEXT NOT NULL DEFAULT (datetime('now'))
				)
			"""
			)

		# 模型 Token 统计日志表
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS model_token_logs(
				id integer PRIMARY KEY AUTOINCREMENT,
				model_id INTEGER NOT NULL,
				prompt_tokens INTEGER NOT NULL DEFAULT 0,
				completion_tokens INTEGER NOT NULL DEFAULT 0,
				total_tokens INTEGER NOT NULL DEFAULT 0,
				duration_ms INTEGER NOT NULL DEFAULT 0,
				success INTEGER NOT NULL DEFAULT 1,
				create_at TEXT NOT NULL DEFAULT (datetime('now')),
				FOREIGN KEY(model_id) REFERENCES model_services(id)
				)
			"""
			)

		# 初始化默认角色
		conn.execute(
			"INSERT OR IGNORE INTO roles(role_code,role_name,description,is_default) VALUES('admin','超级管理员','系统最高权限',1)"
			)
		conn.execute(
			"INSERT OR IGNORE INTO roles(role_code,role_name,description,is_default) VALUES('user','普通用户','基本使用权限',1)"
			)

		# 初始化默认功能模块
		default_modules = [
			('sys_home', '系统首页', '&#xe68e;', '/admin', 1, 1, 0),
			('sys_user', '用户管理', '&#xe770;', '/admin/users', 2, 1, 0),
			('sys_function', '功能管理', '&#xe653;', '/admin/modules', 3, 1, 0),
			('sys_permission', '权限管理', '&#xe672;', '/admin/permissions', 4, 1, 0),
			('sys_role', '角色管理', '&#xe770;', '/admin/roles', 5, 1, 0),
			('sys_digital', '数字员工', '&#xe7d6;', 'javascript:;', 6, 1, 0),
			('sys_model', '模型引擎', '&#xe628;', 'javascript:;', 7, 1, 0),
			('sys_watch', '瞭望管理', '&#xe695;', 'javascript:;', 8, 1, 0),
			('sys_datastore', '数据仓库', '&#xe62d;', 'javascript:;', 9, 1, 0),
			('sys_screen', '数智大屏', '&#xe629;', 'javascript:;', 10, 1, 0),
			('sys_settings', '系统设置', '&#xe716;', 'javascript:;', 11, 1, 0),
			('sys_stats', '系统统计', '&#xe62c;', 'javascript:;', 12, 1, 0),
		]
		for mod in default_modules:
			conn.execute(
				"INSERT OR IGNORE INTO modules(module_code,module_name,icon,href,sort_order,status,parent_id) VALUES(?,?,?,?,?,?,?)",
				mod
			)

		# 初始化默认权限
		default_permissions = [
			('sys_user', 'user:list', '查看用户列表'),
			('sys_user', 'user:add', '新增用户'),
			('sys_user', 'user:edit', '编辑用户'),
			('sys_user', 'user:delete', '删除用户'),
			('sys_user', 'user:batch_delete', '批量删除用户'),
			('sys_function', 'function:list', '查看功能列表'),
			('sys_function', 'function:add', '新增功能'),
			('sys_function', 'function:edit', '编辑功能'),
			('sys_function', 'function:delete', '删除功能'),
			('sys_permission', 'permission:list', '查看权限列表'),
			('sys_permission', 'permission:add', '新增权限'),
			('sys_permission', 'permission:delete', '删除权限'),
			('sys_role', 'role:list', '查看角色列表'),
			('sys_role', 'role:add', '新增角色'),
			('sys_role', 'role:edit', '编辑角色'),
			('sys_role', 'role:delete', '删除角色'),
			('sys_role', 'role:assign', '分配权限'),
		]
		for mod_code, perm_code, perm_name in default_permissions:
			mod_row = conn.execute("SELECT id FROM modules WHERE module_code = ?", (mod_code,)).fetchone()
			if mod_row:
				conn.execute(
					"INSERT OR IGNORE INTO permissions(module_id,permission_code,permission_name) VALUES(?,?,?)",
					(mod_row["id"], perm_code, perm_name)
				)

		# 给超级管理员分配所有权限
		admin_role = conn.execute("SELECT id FROM roles WHERE role_code = 'admin'").fetchone()
		if admin_role:
			all_perms = conn.execute("SELECT id FROM permissions").fetchall()
			for perm in all_perms:
				conn.execute(
					"INSERT OR IGNORE INTO role_permissions(role_id,permission_id) VALUES(?,?)",
					(admin_role["id"], perm["id"])
				)

		# 初始化默认模型服务（DeepSeek-V3）
		conn.execute(
			"INSERT OR IGNORE INTO model_services(model_name,model_code,api_base_url,api_key,is_default,description) VALUES(?,?,?,?,?,?)",
			("DeepSeek-V3", "deepseek-v3", "https://aigc-api.aitoolcore.com/api/v1", "sk-aigc-a7f978cfb7903b1e1165b0f61e0dfec53693407b", 1, "DeepSeek-V3 大语言模型，默认系统模型")
		)