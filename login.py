from flask import request, render_template, redirect, url_for, flash, session, jsonify
from db import check_credentials, get_session
from mail import send_login_verification_email, is_valid_login_verification_code
import time
from models import User

# 用于存储登录验证码和请求时间的字典
login_verification_codes = {}
login_verification_request_times = {}


def login_routes(app):
    @app.route('/')
    def login():
        return render_template('login.html')

    @app.route('/request_login_code', methods=['POST'])
    def request_login_verification_code():
        try:
            email = request.form.get('email')
            if not email:
                flash('请输入有效的邮箱地址。')
                return jsonify({'success': False, 'message': '请输入有效的邮箱地址。'})

            # 防止重复发送验证码（例如，每分钟最多发送一次）
            last_request_time = login_verification_request_times.get(email)
            if last_request_time and time.time() - last_request_time < 60:
                flash('请稍后再试，验证码发送有频率限制。')
                return jsonify({'success': False, 'message': '请稍后再试，验证码发送有频率限制。'})

            if send_login_verification_email(email, login_verification_codes, login_verification_request_times):
                flash('验证码已发送到您的邮箱，请查收。')
                return jsonify({'success': True, 'message': '验证码已发送到您的邮箱，请查收。'})
            else:
                flash('验证码发送失败，请稍后重试。')
                return jsonify({'success': False, 'message': '验证码发送失败，请稍后重试。'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'服务器内部错误：{str(e)}'})

    @app.route('/submit_login', methods=['POST'])
    def submit_login():
        login_method = request.form.get('login_method')
        print(f"接收到的登录方式: {login_method}")

        if login_method == 'password':
            identifier = request.form.get('identifier')  # 可以是用户名或邮箱
            password = request.form.get('password')
            print(f"用户名/邮箱: {identifier}, 密码: {password}")

            if not all([identifier, password]):
                flash('请填写用户名/邮箱和密码。')
                return redirect(url_for('login'))

            if check_credentials(identifier, password):
                with get_session() as session_db:
                    user = session_db.query(User).filter(
                        (User.username == identifier) | (User.email == identifier)
                    ).first()
                    if user and user.is_admin:
                        session['user_identifier'] = identifier
                        return redirect(url_for('home'))
                    elif user:
                        session['user_identifier'] = identifier
                        return redirect(url_for('user_dashboard'))
                    else:
                        flash('用户名/邮箱或密码错误，请重试。')
                        return redirect(url_for('login'))
            else:
                flash('用户名/邮箱或密码错误，请重试。')
                return redirect(url_for('login'))

        elif login_method == 'code':
            email = request.form.get('email')
            code = request.form.get('verification_code')
            print(f"邮箱: {email}, 验证码: {code}")

            if not all([email, code]):
                flash('请填写邮箱和验证码。')
                return redirect(url_for('login'))

            if is_valid_login_verification_code(email, code, login_verification_codes):
                with get_session() as session_db:
                    user = session_db.query(User).filter_by(email=email).first()
                    if user and user.is_admin:
                        session['user_identifier'] = email
                        return redirect(url_for('home'))
                    elif user:
                        session['user_identifier'] = email
                        return redirect(url_for('user_dashboard'))
                    else:
                        flash('无效的验证码或用户不存在，请重试。')
                        return redirect(url_for('login'))
            else:
                flash('无效的验证码或验证码已过期，请重试。')
                return redirect(url_for('login'))

        else:
            flash('无效的登录方式，请选择正确的登录方式。')
            return redirect(url_for('login'))
