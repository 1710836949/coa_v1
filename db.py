import os

import bcrypt
import logging
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from mail import is_valid_verification_code
from models import Base, User, Material, QualityReport, UserPermission
import mysql.connector

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 数据库引擎实例，使用单例模式
engine = None


def create_engine_instance():
    global engine
    if engine:
        return engine
    try:
        engine = create_engine('mysql+mysqlconnector://root:wc147258@localhost:3306/user_registration')
        # 尝试连接到数据库
        with engine.connect():
            pass
    except mysql.connector.errors.ProgrammingError as e:
        if e.errno == 1049:  # 数据库不存在
            logging.info("Database 'user_registration' does not exist. Creating...")
            try:
                # 创建数据库连接，不指定数据库名
                conn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="wc147258"
                )
                cursor = conn.cursor()
                # 创建数据库
                cursor.execute("CREATE DATABASE IF NOT EXISTS user_registration")
                logging.info("Database 'user_registration' created successfully.")
                conn.close()
                engine = create_engine('mysql+mysqlconnector://root:wc147258@localhost:3306/user_registration')
            except mysql.connector.Error as err:
                logging.error(f"Error creating database: {err}")
                raise
        else:
            raise e
    Base.metadata.create_all(engine)
    return engine


@contextmanager
def get_session():
    engine = create_engine_instance()
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


# ... 其他函数保持不变 ...

def get_all_materials():
    """
    获取数据库中所有的物料信息
    :return: 包含所有物料信息的字典列表
    """
    with get_session() as session:
        try:
            # 查询所有的物料信息
            materials = session.query(Material).all()
            return [
                {
                    'id': material.id,
                    'material_code': material.material_code,
                    'material_name': material.material_name
                }
                for material in materials
            ]
        except Exception as e:
            # 若出现异常，可根据需要进行处理，这里简单打印错误信息
            logging.error(f"查询物料信息时出现错误: {e}")
            return []


def insert_user(username, password, email, is_admin=False):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    user = User(username=username, password=hashed.decode('utf-8'), email=email, is_admin=is_admin)
    with get_session() as session:
        session.add(user)


def check_existence(column, value):
    with get_session() as session:
        stmt = select(User).where(column == value)
        result = session.execute(stmt).first()
        return result is not None


def is_username_exists(username):
    return check_existence(User.username, username)


def is_email_exists(email):
    return check_existence(User.email, email)


def check_credentials(identifier, password):
    with get_session() as session:
        stmt_username = select(User).where(User.username == identifier)
        stmt_email = select(User).where(User.email == identifier)
        result_username = session.execute(stmt_username).first()
        result_email = session.execute(stmt_email).first()
        if result_username:
            stored_password = result_username[0].password
            return bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
        elif result_email:
            stored_password = result_email[0].password
            return bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
        return False


def check_credentials_with_code(email, code):
    return is_valid_verification_code(email, code)


# 新增插入物料信息的函数
def insert_material(material_code, material_name):
    material = Material(material_code=material_code, material_name=material_name)
    with get_session() as session:
        session.add(material)
        session.flush()
        return material.id


# 新增插入质检报告信息的函数
def insert_quality_report(material_id, report_path):
    report = QualityReport(material_id=material_id, report_path=report_path)
    with get_session() as session:
        session.add(report)


# 新增插入用户权限信息的函数
def insert_user_permission(user_id, material_id):
    permission = UserPermission(user_id=user_id, material_id=material_id)
    with get_session() as session:
        session.add(permission)


# 新增获取用户有权限的物料列表的函数
def get_user_permitted_materials(user_id):
    with get_session() as session:
        stmt = select(Material).join(UserPermission).where(UserPermission.user_id == user_id)
        materials = session.execute(stmt).scalars().all()
        return [
            {
                'id': material.id,
                'material_code': material.material_code,
                'material_name': material.material_name
            }
            for material in materials
        ]


# 新增根据物料 ID 获取质检报告列表的函数
def get_quality_reports_by_material(material_id):
    with get_session() as session:
        stmt = select(QualityReport).where(QualityReport.material_id == material_id)
        reports = session.execute(stmt).scalars().all()
        return [
            {
                'id': report.id,
                'material_id': report.material_id,
                'report_path': report.report_path,
                'upload_time': report.upload_time,
                'filename': os.path.basename(report.report_path)  # 获取文件名
            }
            for report in reports
        ]


def get_user_by_identifier(identifier):
    with get_session() as session:
        stmt_username = select(User).where(User.username == identifier)
        stmt_email = select(User).where(User.email == identifier)
        result_username = session.execute(stmt_username).first()
        result_email = session.execute(stmt_email).first()
        if result_username:
            return result_username[0]
        elif result_email:
            return result_email[0]
    return None


def search_user_permitted_materials(user_id, keyword):
    """
    根据用户 ID 和搜索关键词查找用户被授权查看的物料
    :param user_id: 用户的 ID
    :param keyword: 搜索关键词，可以匹配物料编码或名称
    :return: 符合条件的物料列表
    """
    with get_session() as session:
        # 构建 SQLAlchemy 查询语句
        stmt = select(Material).join(UserPermission).where(
            # 确保物料和用户权限记录关联
            UserPermission.user_id == user_id,
            # 使用 contains 方法进行模糊匹配，查找物料编码或名称中包含关键词的记录
            (Material.material_code.contains(keyword)) | (Material.material_name.contains(keyword))
        )
        # 执行查询并获取结果
        result = session.execute(stmt)
        # 使用 scalars().all() 方法获取所有的物料对象
        materials = result.scalars().all()
        return [
            {
                'id': material.id,
                'material_code': material.material_code,
                'material_name': material.material_name
            }
            for material in materials
        ]
