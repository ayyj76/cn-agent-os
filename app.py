#程序的主入口
#承担服务器容器+程序作用
#服务器容器：提供http容器服务，程序放置于该容器中运行
#程序：本体-智能瞭望与智能问数系统 B/s架构
import os
import tornado.ioloop
import tornado.web
from tornado.httpserver import HTTPServer

from app.controllers.auth import LoginHandler, LogoutHandler, IndexHandler
from app.controllers.admin import AdminLoginHandler, AdminLogoutHandler, AdminHomeHandler, AdminWelcomeHandler, AdminUserHandler, AdminApiHandler, AdminModuleHandler, AdminPermissionHandler, AdminRoleHandler, AdminModelHandler, ModelChatSSEHandler
from app.models.db import init_db

#class HealthHandler(tornado.web.RequestHandler):
#	def get(self):
#		self.write({"status":"ok"})

#class LoginHandler(tornado.web.RequestHandler):
#	def get(self):
#		self.write(f"""<h3>模拟登录验证测试BaseHandler<h3>

#			<form method="post">

			
#			<button type="submit">登录admin</button>
#			"""
#			+ self.xsrf_form_html() +
#			"""
#			</form>
#			""")

#		def post(self):
#			next_url = self.get_argument("next","/private")
#			self.set_secure_cookie("username","admin")
#			self.redirect(next_url)

#class PrivateHandler(BaseHandler):
#	@tornado.web.authenticated
#	def get(self):
#		self.write(self.current_user)



def make_app():
#	return tornado.web.Application([
#		("/abc",HealthHandler),
#		("/login.jsp",HealthHandler),
#		("/",HealthHandler),
#		("/login.php",HealthHandler)
#		],debug=True)
#	return tornado.web.Application([
#			(r"/",LoginHandler),
#			(r"/login",LoginHandler),
#			(r"/abc",HealthHandler),
#			(r"/private",PrivateHandler)
#		],
#		cookie_secret="demo-cokie-secret-change-me",
#		login_url="/",
#		xsrf_cookies=True,
#		debug=True
#	)
	base_url = os.path.dirname(os.path.abspath(__file__))

	settings = dict(
		template_path=os.path.join(base_url,"app","templates"),
		static_path=os.path.join(base_url,"app","static"),
	    cookie_secret="demo-cookie-secret-change-me",
	    login_url="/auth/login",
	    xsrf_cookies=True,
	    debug=True,
	    autoreload=True
	)
	return tornado.web.Application(
		[
			(r"/", IndexHandler),
			(r"/auth/login",LoginHandler),
			(r"/auth/logout", LogoutHandler),
			(r"/admin/login", AdminLoginHandler),
			(r"/admin/logout", AdminLogoutHandler),
			(r"/admin", AdminHomeHandler),
			(r"/admin/home/welcome", AdminWelcomeHandler),
			(r"/admin/users", AdminUserHandler),
			(r"/admin/modules", AdminModuleHandler),
			(r"/admin/permissions", AdminPermissionHandler),
			(r"/admin/roles", AdminRoleHandler),
			(r"/admin/models", AdminModelHandler),
			(r"/admin/models/chat", ModelChatSSEHandler),
			(r"/api/menu", AdminApiHandler),
		],
		**settings
	)

if __name__ == "__main__":
	init_db()
	app = make_app()
	server = HTTPServer(app)
	server.bind(10088)
	#启动CPU核心数
	server.start()

	print("===== Server 启动成功 ====== 端口：10088",flush=True)
	tornado.ioloop.IOLoop.current().start()