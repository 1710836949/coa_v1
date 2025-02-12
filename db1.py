import bcrypt
import logging
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
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
    :return: 包含所有物料对象的列表
    """
    with get_session() as session:
        try:
            # 查询所有的物料信息
            materials = session.query(Material).all()
            return materials
        except Exception as e:
            # 若出现异常，可根据需要进行处理，这里简单打印错误信息
            print(f"查询物料信息时出现错误: {e}")
            return []