from flask import request, render_template, redirect, url_for, flash, session
from db import insert_user, is_username_exists, is_email_exists
from mail import send_verification_email, is_valid_verification_code
import random
import string
import time
import re

# 用于存储验证码和请求时间的字典
verification_codes = {}
verification_request_times = {}


# 生成随机验证码
def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))  # 纯数字


def register_routes(app):
    @app.route('/register')
    def register():  # 注册页面
        return render_template('register.html')

    @app.route('/request_code', methods=['POST'])
    def request_verification_code():
        email = request.form.get('email')
        if not email:
            flash('请输入有效的邮箱地址。')
            return redirect(url_for('register'))

        # 防止重复发送验证码（例如，每分钟最多发送一次）
        last_request_time = verification_request_times.get(email)
        if last_request_time and time.time() - last_request_time < 60:
            flash('请稍后再试，验证码发送有频率限制。')
            return redirect(url_for('register'))

        if send_verification_email(email, verification_codes, verification_request_times):
            flash('验证码已发送到您的邮箱，请查收。')
        else:
            flash('验证码发送失败，请稍后重试。')
        return redirect(url_for('register'))

    @app.route('/submit_registration', methods=['POST'])
    def submit_registration():
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        verification_code = request.form.get('verification_code')

        # 基本输入验证
        if not all([username, password, email, verification_code]):
            flash('请填写所有必填字段。')
            return redirect(url_for('register'))

        # 检查用户名是否已存在
        if is_username_exists(username):
            flash('该用户名已被使用，请选择其他用户名。')
            return redirect(url_for('register'))

        # 检查邮箱是否已存在
        if is_email_exists(email):
            flash('该邮箱已被注册，请使用其他邮箱。')
            return redirect(url_for('register'))

        # 检查密码长度和格式
        if len(password) < 6:
            flash('密码长度必须为 6 位及以上。')
            return redirect(url_for('register'))
        pattern = re.compile(r'(?=.*[a-zA-Z])(?=.*\d)')
        if not pattern.search(password):
            flash('密码必须包含字母和数字。')
            return redirect(url_for('register'))

        if not is_valid_verification_code(email, verification_code, verification_codes):
            flash('无效的验证码或验证码已过期。')
            return redirect(url_for('register'))

        # 存储用户数据到数据库
        try:
            insert_user(username, password, email,is_admin=False)
        except Exception as e:
            flash('注册失败，请稍后重试。')
            print(f"Error inserting user: {e}")
            return redirect(url_for('register'))

        # 清理验证码和请求时间
        verification_codes.pop(email, None)
        verification_request_times.pop(email, None)

        flash('注册成功！')
        # 重定向到登录页面
        return redirect(url_for('login'))
