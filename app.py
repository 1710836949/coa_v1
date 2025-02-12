from flask import Flask
from flask_mail import Mail
import os
from index import index_routes
from login import login_routes
from routes import register_routes
from home import home_routes
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)  # 使用随机密钥来增加安全性
app.config['MAIL_SERVER'] = 'smtp.qq.com'  # 替换为你的 SMTP 服务器
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '1710836949@qq.com'  # 替换为你的邮箱地址
app.config['MAIL_PASSWORD'] = 'ljejyuytwvogehii'  # 替换为你的邮箱密码（注意：不要在代码中硬编码密码）

app.jinja_env.add_extension('jinja2.ext.do')

mail = Mail(app)
login_routes(app)
register_routes(app)
home_routes(app)
index_routes(app)
if __name__ == '__main__':
    app.run(debug=True)