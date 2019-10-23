# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function
from datetime import datetime
import os
import tornado
import requests
from tornado.options import define, options
from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler
from CONF import *

# 设置服务器端口
define("port", default=PORT, type=int)
users = {}  # 用来存放在线用户的容器
admin = None


class IndexHandler(RequestHandler):
    def get(self):
        self.render("base.html", port=PORT)


class ChatHandler(WebSocketHandler):

    def open(self):
        # 建立连接后添加用户到容器中
        global admin
        if int(self.get_argument('admin', '0')) == 1:
            admin = self
            for user, con in users.items():
                self.write_message("[{}]-已开始聊天".format(user))
        else:
            remote_ip, port = self.request.connection.context.address
            users[':'.join([remote_ip, str(port)])] = self
            # 向已在线用户发送消息
            now = datetime.now().strftime("%H:%M:%S")
            self.write_message("[{}]欢迎-[{}:{}]-来聊天".format(now, remote_ip, port))
            if admin:
                admin.write_message("[{}] [{}:{}]-开始聊天".format(now, remote_ip, port))

    def on_message(self, message):
        # 向在线用户回复消息
        data = {
            'spoken': message,
            'appid': APPID,
            'userid': USERID
        }
        res = requests.post('https://api.ownthink.com/bot', data=data, timeout=2)
        response = '听不见，听不见！'
        try:
            response = res.json()['data']['info']['text']
        except requests.exceptions.BaseHTTPError:
            pass
        now = datetime.now().strftime("%H:%M:%S")
        remote_ip, port = self.request.connection.context.address
        user = users[':'.join([remote_ip, str(port)])]
        user.write_message("[{}] {}".format(now, response))

    def on_close(self):
        # 用户关闭连接后从容器中移除用户
        global admin
        remote_ip, port = self.request.connection.context.address
        if int(self.get_argument('admin', '0')) == 0:
            del users[':'.join([remote_ip, str(port)])]
        else:
            admin=None
        now = datetime.now().strftime("%H:%M:%S")
        if admin:
            admin.write_message("[{}] [{}:{}]-结束聊天".format(now, remote_ip, port))

    def check_origin(self, origin):
        return True  # 允许WebSocket的跨域请求


class AdminHandler(RequestHandler):
    """
    管理员页面
    """

    def get(self):
        self.render("admin.html", port=PORT)


class App:
    def __init__(self):
        self.app = tornado.web.Application([
            (r"/", IndexHandler),
            (r"/chat", ChatHandler),
            (r'/admin', AdminHandler)
        ],
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            debug=False
        )

    def start(self):
        tornado.options.parse_command_line()
        http_server = tornado.httpserver.HTTPServer(self.app)
        http_server.listen(options.port)
        tornado.ioloop.IOLoop.current().start()