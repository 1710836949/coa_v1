import os
import re
from datetime import datetime

import img2pdf
from flask import render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.orm import load_only

from db import get_session, insert_material, insert_quality_report, insert_user_permission
from models import User, Material

# 确保上传文件夹存在
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def home_routes(app):
    @app.route('/home')
    def home():
        with get_session() as session:
            users = session.query(User).options(load_only(User.id, User.username)).all()
            materials = session.query(Material).options(
                load_only(Material.id, Material.material_code, Material.material_name)).all()
            # 将用户和物料实例转换为字典
            users_data = [{'id': user.id, 'username': user.username} for user in users]
            materials_data = [
                {'id': material.id, 'material_code': material.material_code, 'material_name': material.material_name}
                for material in materials]
        return render_template('home.html', users=users_data, materials=materials_data)

    @app.route('/create_material_folder', methods=['POST'])
    def create_material_folder():
        material_code = request.form.get('material_code')
        material_name = request.form.get('material_name')

        if not material_code or not material_name:
            flash('物料编码和物料名称不能为空，请重新输入。', 'error')
            return redirect(url_for('home'))

        # 验证物料编码是否为 7 - 10 位数字
        if not re.match(r'^\d{7,10}$', material_code):
            flash('物料编码必须是 7 - 10 位数字，请重新输入。', 'error')
            return redirect(url_for('home'))

        with get_session() as session:
            # 检查物料编码是否已存在
            existing_material = session.query(Material).filter_by(material_code=material_code).first()
            if existing_material:
                flash('该物料编码已被使用，请选择其他编码。', 'error')
                return redirect(url_for('home'))

            try:
                # 插入物料信息到数据库
                insert_material(material_code, material_name)
                # 创建对应的文件夹
                folder_name = f"{material_code}-{material_name}"
                folder_path = os.path.join(UPLOAD_FOLDER, folder_name)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                flash('物料文件夹创建成功！', 'success')
            except Exception as e:
                flash(f'物料文件夹创建失败：{str(e)}', 'error')
        return redirect(url_for('home'))

    @app.route('/upload_quality_report', methods=['POST'])
    def upload_quality_report():
        material_id = request.form.get('material_id')
        file = request.files.get('report_file')

        if not material_id or not file:
            flash('请选择物料和上传文件。', 'error')
            return redirect(url_for('home'))

        with get_session() as session:
            material = session.query(Material).filter_by(id=material_id).first()
            if not material:
                flash('所选物料不存在，请重新选择。', 'error')
                return redirect(url_for('home'))

            folder_name = f"{material.material_code}-{material.material_name}"
            folder_path = os.path.join(UPLOAD_FOLDER, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            # 获取当前时间并格式化为字符串
            current_time = datetime.now().strftime("%Y%m%d%H%M%S")
            pdf_path = os.path.join(folder_path, f'{current_time}.pdf')  # 修改文件名

            try:
                with open(pdf_path, "wb") as f:
                    f.write(img2pdf.convert(file.read()))
                insert_quality_report(material_id, pdf_path)
                flash('质检报告上传成功！', 'success')
            except Exception as e:
                flash(f'质检报告上传失败：{str(e)}', 'error')

        return redirect(url_for('home'))

    @app.route('/set_user_permission', methods=['POST'])
    def set_user_permission():
        user_id = request.form.get('user_id')
        material_ids = request.form.getlist('material_id_permission[]')  # 修改为 getlist

        if not user_id or not material_ids:
            return jsonify({'success': False, 'message': '请选择用户和至少一个物料'}), 400

        with get_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                return jsonify({'success': False, 'message': '所选用户不存在，请重新选择'}), 400

            for material_id in material_ids:
                material = session.query(Material).filter_by(id=material_id).first()
                if not material:
                    return jsonify({'success': False, 'message': f'物料 ID {material_id} 不存在，请重新选择'}), 400

            try:
                for material_id in material_ids:
                    insert_user_permission(user_id, material_id)
                session.commit()  # 提交事务，确保权限设置保存到数据库
                return jsonify({'success': True, 'message': '用户权限设置成功！'}), 200
            except Exception as e:
                session.rollback()  # 若出现异常，回滚事务
                return jsonify({'success': False, 'message': f'用户权限设置失败：{str(e)}'}), 500