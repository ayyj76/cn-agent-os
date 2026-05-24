import json
import tornado.web

from app.controllers.base import BaseHandler
from app.models.user import UserRepository
from app.models.permission import ModuleRepository, PermissionRepository, RoleRepository
from app.models.model_engine import ModelServiceRepository


class AdminLoginHandler(BaseHandler):
    def get(self):
        self.render("admin_login.html", title="AI智能瞭望系统 - 管理员登录", error=None)

    def post(self):
        username = (self.get_body_argument("username", "") or "").strip()
        password = self.get_body_argument("password", "")
        if not username or not password:
            return self.render("admin_login.html", title="AI智能瞭望系统 - 管理员登录", error="用户名或密码不能为空")
        if not UserRepository.verify_user(username, password):
            return self.render("admin_login.html", title="AI智能瞭望系统 - 管理员登录", error="用户名或密码错误，或账号已被禁用")
        user = UserRepository.get_user_by_username(username)
        if user["role"] != "admin":
            return self.render("admin_login.html", title="AI智能瞭望系统 - 管理员登录", error="您没有管理员权限，请使用管理员账号登录")
        self.set_secure_cookie("admin_user", username)
        self.set_secure_cookie("admin_role", user["role"])
        self.redirect("/admin")


class AdminLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("admin_user")
        self.clear_cookie("admin_role")
        self.redirect("/admin/login")


class AdminHomeHandler(BaseHandler):
    def get(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            self.redirect("/admin/login")
            return
        import json as _json
        menu_tree = _json.dumps([
            {
                "title": "系统管理",
                "icon": "layui-icon layui-icon-set",
                "children": [
                    {"title": "用户管理", "icon": "layui-icon layui-icon-username", "href": "/admin/users"},
                    {"title": "功能管理", "icon": "layui-icon layui-icon-app", "href": "/admin/modules"},
                    {"title": "权限管理", "icon": "layui-icon layui-icon-auz", "href": "/admin/permissions"},
                    {"title": "角色管理", "icon": "layui-icon layui-icon-group", "href": "/admin/roles"},
                ]
            },
            {
                "title": "AI 能力",
                "icon": "layui-icon layui-icon-component",
                "children": [
                    {"title": "数字员工", "icon": "layui-icon layui-icon-user", "href": "javascript:;", "pending": True},
                    {"title": "模型引擎", "icon": "layui-icon layui-icon-engine", "href": "/admin/models"},
                ]
            },
            {
                "title": "数据管理",
                "icon": "layui-icon layui-icon-table",
                "children": [
                    {"title": "瞭望管理", "icon": "layui-icon layui-icon-read", "href": "javascript:;", "pending": True},
                    {"title": "数据仓库", "icon": "layui-icon layui-icon-file-b", "href": "javascript:;", "pending": True},
                ]
            },
            {
                "title": "系统运维",
                "icon": "layui-icon layui-icon-set-fill",
                "children": [
                    {"title": "数智大屏", "icon": "layui-icon layui-icon-chart-screen", "href": "javascript:;", "pending": True},
                    {"title": "系统设置", "icon": "layui-icon layui-icon-set", "href": "javascript:;", "pending": True},
                    {"title": "系统统计", "icon": "layui-icon layui-icon-chart", "href": "javascript:;", "pending": True},
                ]
            }
        ])
        self.render("admin_home.html", title="管理控制台", username=username.decode("utf-8"), menu_tree=menu_tree)


class AdminWelcomeHandler(BaseHandler):
    def get(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            self.redirect("/admin/login")
            return
        self.render("admin_welcome.html")


class AdminUserHandler(BaseHandler):
    def get(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            self.redirect("/admin/login")
            return
        self.render("admin_user.html", title="用户管理", username=username.decode("utf-8"), xsrf_token=self.xsrf_token)

    def post(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            self.write(json.dumps({"code": 401, "msg": "未登录"}))
            return
        action = self.get_body_argument("action", "")
        if action == "list":
            page = int(self.get_body_argument("page", 1))
            limit = int(self.get_body_argument("limit", 20))
            keyword = (self.get_body_argument("keyword", "") or "").strip()
            role = self.get_body_argument("role", "")
            status = int(self.get_body_argument("status", -1))
            result = UserRepository.get_user_list(page, limit, keyword, role, status)
            self.write(json.dumps({"code": 0, "msg": "", "count": result["total"], "data": result["data"]}))
        elif action == "add":
            new_username = (self.get_body_argument("username", "") or "").strip()
            password = self.get_body_argument("password", "")
            role = self.get_body_argument("role", "user")
            remark = (self.get_body_argument("remark", "") or "").strip()
            if not new_username or not password:
                self.write(json.dumps({"code": 1, "msg": "用户名和密码不能为空"}))
                return
            if UserRepository.create_user(new_username, password, role, remark):
                self.write(json.dumps({"code": 0, "msg": "添加成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "用户名已存在"}))
        elif action == "edit":
            user_id = int(self.get_body_argument("id", 0))
            role = self.get_body_argument("role", None)
            status_str = self.get_body_argument("status", None)
            status = int(status_str) if status_str is not None else None
            remark = self.get_body_argument("remark", None)
            password = self.get_body_argument("password", None) or None
            if password == "":
                password = None
            if UserRepository.update_user(user_id, role, status, remark, password):
                self.write(json.dumps({"code": 0, "msg": "修改成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "修改失败"}))
        elif action == "delete":
            user_id = int(self.get_body_argument("id", 0))
            if UserRepository.delete_user(user_id):
                self.write(json.dumps({"code": 0, "msg": "删除成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "删除失败"}))
        elif action == "batch_delete":
            ids_str = self.get_body_argument("ids", "")
            ids = [int(x) for x in ids_str.split(",") if x.strip()]
            if not ids:
                self.write(json.dumps({"code": 1, "msg": "请选择要删除的用户"}))
                return
            if UserRepository.batch_delete_user(ids):
                self.write(json.dumps({"code": 0, "msg": "批量删除成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "批量删除失败"}))
        elif action == "roles":
            roles = UserRepository.get_all_roles()
            self.write(json.dumps({"code": 0, "msg": "", "data": roles}))


class AdminApiHandler(BaseHandler):
    def get(self):
        self._handle_menu()

    def post(self):
        self._handle_menu()

    def _handle_menu(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            self.write(json.dumps({"code": 401, "msg": "未登录"}))
            return
        module = self.get_argument("module", "")
        if module == "tree":
            tree = [
                {
                    "title": "系统管理",
                    "icon": "layui-icon layui-icon-set",
                    "children": [
                        {"title": "用户管理", "icon": "layui-icon layui-icon-username", "href": "/admin/users"},
                        {"title": "功能管理", "icon": "layui-icon layui-icon-app", "href": "/admin/modules", "pending": True},
                        {"title": "权限管理", "icon": "layui-icon layui-icon-auz", "href": "/admin/permissions", "pending": True},
                        {"title": "角色管理", "icon": "layui-icon layui-icon-group", "href": "/admin/roles", "pending": True},
                    ]
                },
                {
                    "title": "AI 能力",
                    "icon": "layui-icon layui-icon-component",
                    "children": [
                        {"title": "数字员工", "icon": "layui-icon layui-icon-user", "href": "javascript:;", "pending": True},
                        {"title": "模型引擎", "icon": "layui-icon layui-icon-engine", "href": "javascript:;", "pending": True},
                    ]
                },
                {
                    "title": "数据管理",
                    "icon": "layui-icon layui-icon-table",
                    "children": [
                        {"title": "瞭望管理", "icon": "layui-icon layui-icon-read", "href": "javascript:;", "pending": True},
                        {"title": "数据仓库", "icon": "layui-icon layui-icon-file-b", "href": "javascript:;", "pending": True},
                    ]
                },
                {
                    "title": "系统运维",
                    "icon": "layui-icon layui-icon-set-fill",
                    "children": [
                        {"title": "数智大屏", "icon": "layui-icon layui-icon-chart-screen", "href": "javascript:;", "pending": True},
                        {"title": "系统设置", "icon": "layui-icon layui-icon-set", "href": "javascript:;", "pending": True},
                        {"title": "系统统计", "icon": "layui-icon layui-icon-chart", "href": "javascript:;", "pending": True},
                    ]
                }
            ]
            self.write(json.dumps({"code": 0, "msg": "", "data": tree}))
        elif module == "menu":
            modules = ModuleRepository.get_all_modules()
            menu = []
            for m in modules:
                if m["status"] == 1:
                    menu.append({
                        "title": m["module_name"],
                        "icon": m["icon"],
                        "href": m["href"]
                    })
            self.write(json.dumps({"code": 0, "msg": "", "data": menu}))


class AdminModuleHandler(BaseHandler):
    def get(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            self.redirect("/admin/login")
            return
        self.render("admin_module.html", title="功能管理", username=username.decode("utf-8"), xsrf_token=self.xsrf_token)

    def post(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            self.write(json.dumps({"code": 401, "msg": "未登录"}))
            return
        action = self.get_body_argument("action", "")
        if action == "list":
            modules = ModuleRepository.get_all_modules()
            self.write(json.dumps({"code": 0, "msg": "", "count": len(modules), "data": modules}))
        elif action == "add":
            module_code = (self.get_body_argument("module_code", "") or "").strip()
            module_name = (self.get_body_argument("module_name", "") or "").strip()
            icon = self.get_body_argument("icon", "")
            href = self.get_body_argument("href", "")
            sort_order = int(self.get_body_argument("sort_order", 0))
            status = int(self.get_body_argument("status", 1))
            parent_id = int(self.get_body_argument("parent_id", 0))
            description = (self.get_body_argument("description", "") or "").strip()
            if not module_code or not module_name:
                self.write(json.dumps({"code": 1, "msg": "模块编码和名称不能为空"}))
                return
            if ModuleRepository.add_module(module_code, module_name, icon, href, sort_order, status, parent_id, description):
                self.write(json.dumps({"code": 0, "msg": "添加成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "添加失败，模块编码可能已存在"}))
        elif action == "edit":
            module_id = int(self.get_body_argument("id", 0))
            module_name = self.get_body_argument("module_name", None)
            icon = self.get_body_argument("icon", None)
            href = self.get_body_argument("href", None)
            sort_order_str = self.get_body_argument("sort_order", None)
            sort_order = int(sort_order_str) if sort_order_str is not None else None
            status_str = self.get_body_argument("status", None)
            status = int(status_str) if status_str is not None else None
            parent_id_str = self.get_body_argument("parent_id", None)
            parent_id = int(parent_id_str) if parent_id_str is not None else None
            description = self.get_body_argument("description", None)
            if ModuleRepository.update_module(module_id, module_name, icon, href, sort_order, status, parent_id, description):
                self.write(json.dumps({"code": 0, "msg": "修改成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "修改失败"}))
        elif action == "delete":
            module_id = int(self.get_body_argument("id", 0))
            if ModuleRepository.delete_module(module_id):
                self.write(json.dumps({"code": 0, "msg": "删除成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "删除失败"}))


class AdminPermissionHandler(BaseHandler):
    def get(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            self.redirect("/admin/login")
            return
        self.render("admin_permission.html", title="权限管理", username=username.decode("utf-8"), xsrf_token=self.xsrf_token)

    def post(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            self.write(json.dumps({"code": 401, "msg": "未登录"}))
            return
        action = self.get_body_argument("action", "")
        if action == "list":
            module_id = self.get_body_argument("module_id", "")
            if module_id:
                perms = PermissionRepository.get_permissions_by_module(int(module_id))
            else:
                perms = PermissionRepository.get_all_permissions()
            self.write(json.dumps({"code": 0, "msg": "", "count": len(perms), "data": perms}))
        elif action == "modules":
            modules = ModuleRepository.get_all_modules()
            self.write(json.dumps({"code": 0, "msg": "", "data": modules}))
        elif action == "add":
            module_id = int(self.get_body_argument("module_id", 0))
            permission_code = (self.get_body_argument("permission_code", "") or "").strip()
            permission_name = (self.get_body_argument("permission_name", "") or "").strip()
            description = (self.get_body_argument("description", "") or "").strip()
            if not permission_code or not permission_name or not module_id:
                self.write(json.dumps({"code": 1, "msg": "权限编码、名称和所属功能不能为空"}))
                return
            if PermissionRepository.add_permission(module_id, permission_code, permission_name, description):
                self.write(json.dumps({"code": 0, "msg": "添加成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "添加失败，权限编码可能已存在"}))
        elif action == "edit":
            permission_id = int(self.get_body_argument("id", 0))
            module_id = int(self.get_body_argument("module_id", 0)) or None
            permission_code = (self.get_body_argument("permission_code", "") or "").strip() or None
            permission_name = (self.get_body_argument("permission_name", "") or "").strip() or None
            description = self.get_body_argument("description", None)
            if PermissionRepository.update_permission(permission_id, module_id, permission_code, permission_name, description):
                self.write(json.dumps({"code": 0, "msg": "修改成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "修改失败"}))
        elif action == "delete":
            permission_id = int(self.get_body_argument("id", 0))
            if PermissionRepository.delete_permission(permission_id):
                self.write(json.dumps({"code": 0, "msg": "删除成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "删除失败"}))


class AdminRoleHandler(BaseHandler):
    def get(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            self.redirect("/admin/login")
            return
        self.render("admin_role.html", title="角色管理", username=username.decode("utf-8"), xsrf_token=self.xsrf_token)

    def post(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            self.write(json.dumps({"code": 401, "msg": "未登录"}))
            return
        action = self.get_body_argument("action", "")
        if action == "list":
            roles = RoleRepository.get_all_roles()
            self.write(json.dumps({"code": 0, "msg": "", "data": roles}))
        elif action == "add":
            role_code = (self.get_body_argument("role_code", "") or "").strip()
            role_name = (self.get_body_argument("role_name", "") or "").strip()
            description = (self.get_body_argument("description", "") or "").strip()
            status = int(self.get_body_argument("status", 1))
            if not role_code or not role_name:
                self.write(json.dumps({"code": 1, "msg": "角色编码和名称不能为空"}))
                return
            if RoleRepository.add_role(role_code, role_name, description, status):
                self.write(json.dumps({"code": 0, "msg": "添加成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "添加失败，角色编码可能已存在"}))
        elif action == "edit":
            role_id = int(self.get_body_argument("id", 0))
            role_name = self.get_body_argument("role_name", None)
            description = self.get_body_argument("description", None)
            status_str = self.get_body_argument("status", None)
            status = int(status_str) if status_str is not None else None
            if RoleRepository.update_role(role_id, role_name, description, status):
                self.write(json.dumps({"code": 0, "msg": "修改成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "修改失败"}))
        elif action == "delete":
            role_id = int(self.get_body_argument("id", 0))
            if RoleRepository.delete_role(role_id):
                self.write(json.dumps({"code": 0, "msg": "删除成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "默认角色不能删除"}))
        elif action == "assign":
            role_id = int(self.get_body_argument("role_id", 0))
            perm_ids_str = self.get_body_argument("permission_ids", "")
            perm_ids = [x.strip() for x in perm_ids_str.split(",") if x.strip()]
            if RoleRepository.assign_permissions(role_id, perm_ids):
                self.write(json.dumps({"code": 0, "msg": "分配成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "分配失败"}))
        elif action == "perms":
            role_id = int(self.get_body_argument("role_id", 0))
            perm_ids = RoleRepository.get_role_permissions(role_id)
            self.write(json.dumps({"code": 0, "msg": "", "data": perm_ids}))
        elif action == "all_perms":
            perms = PermissionRepository.get_all_permissions()
            self.write(json.dumps({"code": 0, "msg": "", "data": perms}))
        elif action == "all_modules":
            modules = ModuleRepository.get_all_modules()
            self.write(json.dumps({"code": 0, "msg": "", "data": modules}))


class AdminModelHandler(BaseHandler):
    def get(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            self.redirect("/admin/login")
            return
        self.render("admin_model.html", title="模型引擎", username=username.decode("utf-8"), xsrf_token=self.xsrf_token)

    def post(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            self.write(json.dumps({"code": 401, "msg": "未登录"}))
            return
        action = self.get_body_argument("action", "")
        if action == "list":
            page = int(self.get_body_argument("page", 1))
            limit = int(self.get_body_argument("limit", 6))
            keyword = (self.get_body_argument("keyword", "") or "").strip()
            models = ModelServiceRepository.get_all_models()
            if keyword:
                models = [m for m in models if keyword.lower() in m["model_name"].lower() or keyword.lower() in m["model_code"].lower()]
            total = len(models)
            start = (page - 1) * limit
            end = start + limit
            page_data = models[start:end]
            self.write(json.dumps({"code": 0, "msg": "", "count": total, "data": page_data}))
        elif action == "add":
            model_name = (self.get_body_argument("model_name", "") or "").strip()
            model_code = (self.get_body_argument("model_code", "") or "").strip()
            api_base_url = (self.get_body_argument("api_base_url", "") or "").strip()
            api_key = (self.get_body_argument("api_key", "") or "").strip()
            description = (self.get_body_argument("description", "") or "").strip()
            is_default = int(self.get_body_argument("is_default", 0))
            if not model_name or not model_code or not api_base_url or not api_key:
                self.write(json.dumps({"code": 1, "msg": "模型名称、编码、API地址和密钥不能为空"}))
                return
            if ModelServiceRepository.add_model(model_name, model_code, api_base_url, api_key, description, is_default):
                self.write(json.dumps({"code": 0, "msg": "添加成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "添加失败，模型编码可能已存在"}))
        elif action == "edit":
            model_id = int(self.get_body_argument("id", 0))
            model_name = (self.get_body_argument("model_name", "") or "").strip() or None
            model_code = (self.get_body_argument("model_code", "") or "").strip() or None
            api_base_url = (self.get_body_argument("api_base_url", "") or "").strip() or None
            api_key = (self.get_body_argument("api_key", "") or "").strip() or None
            description = self.get_body_argument("description", None)
            status_str = self.get_body_argument("status", None)
            status = int(status_str) if status_str is not None else None
            is_default = int(self.get_body_argument("is_default", -1))
            if is_default == -1:
                is_default = None
            if ModelServiceRepository.update_model(model_id, model_name, model_code, api_base_url, api_key, description, status, is_default):
                self.write(json.dumps({"code": 0, "msg": "修改成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "修改失败"}))
        elif action == "delete":
            model_id = int(self.get_body_argument("id", 0))
            if ModelServiceRepository.delete_model(model_id):
                self.write(json.dumps({"code": 0, "msg": "删除成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "删除失败"}))
        elif action == "stats":
            model_id_str = self.get_body_argument("model_id", "")
            model_id = int(model_id_str) if model_id_str else None
            stats = ModelServiceRepository.get_token_stats(model_id, 30)
            self.write(json.dumps({"code": 0, "msg": "", "data": stats}))


class ModelChatSSEHandler(BaseHandler):
    async def post(self):
        username = self.get_secure_cookie("admin_user")
        if not username:
            self.write(json.dumps({"code": 401, "msg": "未登录"}))
            return
        model_id = int(self.get_body_argument("model_id", 0))
        message = (self.get_body_argument("message", "") or "").strip()
        if not model_id or not message:
            self.write(json.dumps({"code": 1, "msg": "参数错误"}))
            return
        model = ModelServiceRepository.get_model_by_id(model_id)
        if not model:
            self.write(json.dumps({"code": 1, "msg": "模型不存在"}))
            return

        self.set_header("Content-Type", "text/event-stream")
        self.set_header("Cache-Control", "no-cache")
        self.set_header("Connection", "keep-alive")
        self.set_header("X-Accel-Buffering", "no")

        import time
        import asyncio
        try:
            from openai import OpenAI
            loop = asyncio.get_event_loop()
            client = OpenAI(api_key=model["api_key"], base_url=model["api_base_url"])
            start_time = time.time()

            stream = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=model["model_code"],
                    messages=[{"role": "user", "content": message}],
                    stream=True
                )
            )

            full_content = ""
            prompt_tokens = 0
            completion_tokens = 0

            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        full_content += delta.content
                        data = json.dumps({"type": "content", "content": delta.content}, ensure_ascii=False)
                        self.write(f"data: {data}\n\n")
                        await self.flush()
                if hasattr(chunk, 'usage') and chunk.usage:
                    prompt_tokens = getattr(chunk.usage, 'prompt_tokens', 0)
                    completion_tokens = getattr(chunk.usage, 'completion_tokens', 0)

            duration_ms = int((time.time() - start_time) * 1000)
            total_tokens = prompt_tokens + completion_tokens
            if total_tokens > 0:
                ModelServiceRepository.add_token_log(model_id, prompt_tokens, completion_tokens, total_tokens, duration_ms)

            done_data = json.dumps({
                "type": "done",
                "full_content": full_content,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "duration_ms": duration_ms
                }
            }, ensure_ascii=False)
            self.write(f"data: {done_data}\n\n")
            await self.flush()
        except Exception as e:
            error_data = json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False)
            self.write(f"data: {error_data}\n\n")
            await self.flush()
        finally:
            self.write("data: [DONE]\n\n")
            await self.flush()
