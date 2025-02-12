import mimetypes
import os

from flask import render_template, request, redirect, url_for, flash, session, send_file

from db import get_user_permitted_materials, search_user_permitted_materials, get_session, get_all_materials, \
    get_quality_reports_by_material
from models import User, Material


def index_routes(app):
    @app.route('/index')
    def user_dashboard():
        user_identifier = session.get('user_identifier')
        if not user_identifier:
            flash('请先登录。')
            return redirect(url_for('login'))

        with get_session() as session_db:
            user = session_db.query(User).filter(
                (User.username == user_identifier) | (User.email == user_identifier)
            ).first()
            if not user:
                flash('用户不存在，请重新登录。')
                return redirect(url_for('login'))

            # 获取所有物料信息
            all_materials_data = get_all_materials()
            # 获取用户被授权的物料信息
            permitted_materials = get_user_permitted_materials(user.id)
            permitted_material_ids = [material['id'] for material in permitted_materials]

        return render_template('index.html', all_materials=all_materials_data,
                               permitted_material_ids=permitted_material_ids)

    @app.route('/user_search_materials', methods=['GET'])
    def user_search_materials():
        user_identifier = session.get('user_identifier')
        if not user_identifier:
            flash('请先登录。')
            return redirect(url_for('login'))

        keyword = request.args.get('keyword')
        if not keyword:
            flash('请输入搜索关键词。')
            return redirect(url_for('user_dashboard'))

        with get_session() as session_db:
            user = session_db.query(User).filter(
                (User.username == user_identifier) | (User.email == user_identifier)
            ).first()
            if not user:
                flash('用户不存在，请重新登录。')
                return redirect(url_for('login'))

            materials = search_user_permitted_materials(user.id, keyword)
            # 获取用户被授权的物料信息
            permitted_materials = get_user_permitted_materials(user.id)
            permitted_material_ids = [material['id'] for material in permitted_materials]

            return render_template('index.html', all_materials=materials, permitted_material_ids=permitted_material_ids,
                                   keyword=keyword)

    @app.route('/report_list/<int:material_id>')
    def report_list(material_id):
        # 检查用户是否登录
        user_identifier = session.get('user_identifier')
        if not user_identifier:
            flash('请先登录。')
            return redirect(url_for('login'))

        # 查询该物料的质检报告
        reports = get_quality_reports_by_material(material_id)

        # 查询物料信息
        with get_session() as session_db:
            material = session_db.query(Material).filter_by(id=material_id).first()
            if not material:
                flash('未找到该物料。')
                return redirect(url_for('user_dashboard'))

            # 在会话关闭前提取物料信息到字典
            material_data = {
                'id': material.id,
                'material_code': material.material_code,
                'material_name': material.material_name
            }

        return render_template('report_list.html', material=material_data, reports=reports)

    @app.route('/view_quality_report/<int:material_id>')
    def view_quality_report(material_id):
        # 检查用户是否登录
        user_identifier = session.get('user_identifier')
        if not user_identifier:
            flash('请先登录。')
            return redirect(url_for('login'))

        # 查询该物料的质检报告
        reports = get_quality_reports_by_material(material_id)

        # 查询物料信息
        with get_session() as session_db:
            material = session_db.query(Material).filter_by(id=material_id).first()
            if not material:
                flash('未找到该物料。')
                return redirect(url_for('user_dashboard'))

            # 在会话关闭前提取物料信息到字典
            material_data = {
                'id': material.id,
                'material_code': material.material_code,
                'material_name': material.material_name
            }

        # 获取报告索引
        report_index = request.args.get('report_index', type=int, default=0)
        if report_index < 0 or report_index >= len(reports):
            report_index = 0

        return render_template('quality_report.html', material=material_data, reports=reports,
                               report_index=report_index)

    @app.route('/download_report/<path:report_path>')
    def download_report(report_path):
        # 检查用户是否登录
        user_identifier = session.get('user_identifier')
        if not user_identifier:
            flash('请先登录。')
            return redirect(url_for('login'))

        # 检查文件是否存在
        if os.path.exists(report_path):
            # 获取文件的 MIME 类型
            mimetype, _ = mimetypes.guess_type(report_path)
            if mimetype:
                return send_file(report_path, mimetype=mimetype)
            else:
                # 如果无法确定 MIME 类型，默认以二进制流形式返回
                return send_file(report_path, mimetype='application/octet-stream')
        else:
            flash('文件未找到。')
            return redirect(url_for('user_dashboard'))

    return app
