from flask_mail import Message
import time


# 注册用验证码
def send_verification_email(email, verification_codes, verification_request_times):
    from app import mail, app
    verification_code = generate_verification_code()
    expiration = time.time() + 300  # 验证码有效期 5 分钟
    verification_codes[email] = (verification_code, expiration)
    verification_request_times[email] = time.time()  # 记录请求时间以防止重复发送

    msg = Message(subject='注册验证码',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[email],
                  body=f'您的注册验证码是：{verification_code}')
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def is_valid_verification_code(email, code, verification_codes):
    stored_info = verification_codes.get(email)
    if not stored_info:
        return False
    stored_code, expiration = stored_info
    return code == stored_code and time.time() < expiration


def generate_verification_code():
    import random
    import string
    return ''.join(random.choices(string.digits, k=6))  # 纯数字


# 登录用验证码

def send_login_verification_email(email, verification_codes, verification_request_times):
    from app import mail, app
    verification_code = generate_verification_code()
    expiration = time.time() + 300  # 验证码有效期 5 分钟
    verification_codes[email] = (verification_code, expiration)
    verification_request_times[email] = time.time()  # 记录请求时间以防止重复发送

    msg = Message(subject='登录验证码',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[email],
                  body=f'您的登录验证码是：{verification_code}')
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def is_valid_login_verification_code(email, code, verification_codes):
    stored_info = verification_codes.get(email)
    if not stored_info:
        return False
    stored_code, expiration = stored_info
    return code == stored_code and time.time() < expiration


def generate_login_verification_code():
    import random
    import string
    return ''.join(random.choices(string.digits, k=6))  # 纯数字
