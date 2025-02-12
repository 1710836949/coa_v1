from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    registration_date = Column(TIMESTAMP, default=func.now())
    is_admin = Column(Boolean, default=False)  # 新增字段，默认值为 False 表示普通用户

    # 定义与 UserPermission 的关系
    permissions = relationship("UserPermission", back_populates="user")


class Material(Base):
    __tablename__ = 'materials'
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_code = Column(String(50), nullable=False)
    material_name = Column(String(100), nullable=False)

    # 定义与 QualityReport 和 UserPermission 的关系
    quality_reports = relationship("QualityReport", back_populates="material")
    permissions = relationship("UserPermission", back_populates="material")


class QualityReport(Base):
    __tablename__ = 'quality_reports'
    id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False)
    report_path = Column(String(255), nullable=False)
    upload_time = Column(TIMESTAMP, default=func.now())

    # 定义与 Material 的关系
    material = relationship("Material", back_populates="quality_reports")


class UserPermission(Base):
    __tablename__ = 'user_permissions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False)

    # 定义与 User 和 Material 的关系
    user = relationship("User", back_populates="permissions")
    material = relationship("Material", back_populates="permissions")