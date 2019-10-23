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


class IndexHandler(RequestHandler):
    def get(self):
        self.render("base.html")


class ChatHandler(WebSocketHandler):
    users = {}  # 用来存放在线用户的容器

    def open(self):
        # 建立连接后添加用户到容器中
        remote_ip, port = self.request.connection.context.address
        self.users[':'.join([remote_ip, str(port)])] = self
        # 向已在线用户发送消息
        now = datetime.now().strftime("%H:%M:%S")
        self.write_message("[{}]欢迎-[{}:{}]-进入聊天室".format(now, remote_ip, port))

    def on_message(self, message):
        # 向在线用户广播消息
        print(message)
        data = {
            'spoken': message,
            'appid': APPID,
            'userid': USERID
        }
        res = requests.post('https://api.ownthink.com/bot', data=data, timeout=2)
        response = '听不见，听不见！'
        if res.status_code == 200:
            print(res.json())
            response = res.json()['data']['info']['text']
        now = datetime.now().strftime("%H:%M:%S")
        remote_ip, port = self.request.connection.context.address
        user = self.users[':'.join([remote_ip, str(port)])]
        user.write_message("[{}] {}".format(now, response))

    def on_close(self):
        # 用户关闭连接后从容器中移除用户
        remote_ip, port = self.request.connection.context.address
        del self.users[':'.join([remote_ip, str(port)])]

    def check_origin(self, origin):
        return True  # 允许WebSocket的跨域请求


class AdminHandler(RequestHandler):
    """
    管理员页面
    """
    pass


if __name__ == '__main__':
    tornado.options.parse_command_line()

    app = tornado.web.Application([
        (r"/", IndexHandler),
        (r"/chat", ChatHandler),
        (r'/admin', AdminHandler)
    ],
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        debug=False
    )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()
