#!/usr/bin/env python3
"""
版权管理系统 - Flask后端API
包含接口安全验证（Token机制）
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from functools import wraps
import os
import hmac
import uuid
from datetime import datetime
from database import (
    init_db, create_record, get_records, get_record_by_id,
    update_record, delete_record, get_statistics, get_reminders,
    save_file_record, get_original_filename
)

app = Flask(__name__, static_folder='static')
CORS(app)

# ==================== 安全配置 ====================
# 管理员访问令牌（从环境变量读取，必填）
# 部署时必须设置：export ADMIN_TOKEN=your_secure_token
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN')

# 需要Token验证的接口路径前缀
PROTECTED_PREFIXES = ('/api/foreign-publishers', '/api/translators', '/api/contracts',
                       '/api/books', '/api/topic-ideas', '/api/royalties', '/api/file',
                       '/api/upload')

def require_admin_token(f):
    """
    Token验证装饰器
    验证请求头中的 X-ADMIN-TOKEN 或 URL参数中的 token 是否与环境变量中的 ADMIN_TOKEN 匹配
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 如果未设置ADMIN_TOKEN，拒绝所有写操作
        if not ADMIN_TOKEN:
            return jsonify({
                'success': False, 
                'error': '服务器未配置访问令牌，请联系管理员'
            }), 500
        
        # 优先从请求头获取token，其次从URL参数获取
        token = request.headers.get('X-ADMIN-TOKEN') or request.args.get('token')
        
        if not token:
            return jsonify({
                'success': False, 
                'error': '缺少访问令牌，请在请求头中添加 X-ADMIN-TOKEN 或在URL中添加 token 参数'
            }), 401
        
        if not hmac.compare_digest(token, ADMIN_TOKEN):
            return jsonify({
                'success': False, 
                'error': '访问令牌无效'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== 文件上传配置 ====================
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 最大10MB
UPLOAD_FOLDER = '/data/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg'}

def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """返回主页"""
    return send_from_directory('static', 'index.html')

@app.route('/api/init', methods=['POST'])
def initialize():
    """初始化数据库"""
    try:
        init_db()
        return jsonify({'success': True, 'message': '数据库初始化成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==================== 统计接口 ====================
@app.route('/api/statistics', methods=['GET'])
def statistics():
    """获取统计数据"""
    try:
        stats = get_statistics()
        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==================== 提醒接口 ====================
@app.route('/api/reminders', methods=['GET'])
def get_all_reminders():
    """获取所有待提醒项目"""
    try:
        reminders = get_reminders()
        # 统计各类提醒数量
        counts = {
            'total': len(reminders),
            'contract_expiring': len([r for r in reminders if r['type'] == 'contract_expiring']),
            'topic_urgent': len([r for r in reminders if r['type'] == 'topic_urgent']),
            'topic_warning': len([r for r in reminders if r['type'] == 'topic_warning'])
        }
        return jsonify({'success': True, 'data': reminders, 'counts': counts})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==================== 外商库接口 ====================
@app.route('/api/foreign-publishers', methods=['GET'])
def get_foreign_publishers():
    """获取外商库列表"""
    try:
        records = get_records('foreign_publishers', order_by='id DESC')
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/foreign-publishers', methods=['POST'])
@require_admin_token
def create_foreign_publisher():
    """创建外商"""
    try:
        data = request.json
        required = ['original_name', 'country']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'})
        
        record_id = create_record('foreign_publishers', data)
        if record_id is None:
            return jsonify({'success': False, 'error': '创建失败，请检查数据库连接或字段格式'})
        return jsonify({'success': True, 'id': record_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/foreign-publishers/<int:id>', methods=['GET'])
def get_foreign_publisher(id):
    """获取单个外商"""
    try:
        record = get_record_by_id('foreign_publishers', id)
        if record:
            return jsonify({'success': True, 'data': record})
        return jsonify({'success': False, 'error': '记录不存在'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/foreign-publishers/<int:id>', methods=['PUT'])
@require_admin_token
def update_foreign_publisher(id):
    """更新外商"""
    try:
        data = request.json
        result = update_record('foreign_publishers', id, data)
        if result:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': '更新失败，记录不存在或数据库错误'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/foreign-publishers/<int:id>', methods=['DELETE'])
@require_admin_token
def delete_foreign_publisher(id):
    """删除外商"""
    result = delete_record('foreign_publishers', id)
    if result == 'success':
        return jsonify({'success': True})
    elif result == 'not_found':
        return jsonify({'success': False, 'error': '记录不存在'})
    elif result == 'foreign_key':
        return jsonify({'success': False, 'error': '该外商有关联合同，无法删除'})
    else:
        return jsonify({'success': False, 'error': '删除失败'})

# ==================== 译者库接口 ====================
@app.route('/api/translators', methods=['GET'])
def get_translators():
    """获取译者库列表"""
    try:
        records = get_records('translators', order_by='id DESC')
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/translators', methods=['POST'])
@require_admin_token
def create_translator():
    """创建译者"""
    try:
        data = request.json
        if 'name' not in data or not data['name']:
            return jsonify({'success': False, 'error': '缺少必填字段: 姓名'})
        if 'languages' not in data or not data['languages']:
            return jsonify({'success': False, 'error': '缺少必填字段: 语种'})
        
        record_id = create_record('translators', data)
        if record_id is None:
            return jsonify({'success': False, 'error': '创建失败，请检查数据库连接或字段格式'})
        return jsonify({'success': True, 'id': record_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/translators/<int:id>', methods=['GET'])
def get_translator(id):
    """获取单个译者"""
    try:
        record = get_record_by_id('translators', id)
        if record:
            return jsonify({'success': True, 'data': record})
        return jsonify({'success': False, 'error': '记录不存在'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/translators/<int:id>', methods=['PUT'])
@require_admin_token
def update_translator(id):
    """更新译者"""
    try:
        data = request.json
        result = update_record('translators', id, data)
        if result:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': '更新失败，记录不存在或数据库错误'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/translators/<int:id>', methods=['DELETE'])
@require_admin_token
def delete_translator(id):
    """删除译者"""
    result = delete_record('translators', id)
    if result == 'success':
        return jsonify({'success': True})
    elif result == 'not_found':
        return jsonify({'success': False, 'error': '记录不存在'})
    elif result == 'foreign_key':
        return jsonify({'success': False, 'error': '该译者有关联合同，无法删除'})
    else:
        return jsonify({'success': False, 'error': '删除失败'})

# ==================== 合同管理接口 ====================
@app.route('/api/contracts', methods=['GET'])
def get_contracts():
    """获取合同列表"""
    try:
        records = get_records('contracts', order_by='id DESC')
        
        # 批量获取外商信息，避免N+1查询（无条件构建映射，逻辑更清晰）
        all_publishers = get_records('foreign_publishers')
        pub_map = {p['id']: p for p in all_publishers}
        
        for record in records:
            pid = record.get('foreign_publisher_id')
            if pid and pid in pub_map:
                p = pub_map[pid]
                record['foreign_publisher_name'] = p.get('chinese_name') or p.get('original_name')
        
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/contracts', methods=['POST'])
@require_admin_token
def create_contract():
    """创建合同"""
    try:
        data = request.json
        required = ['contract_name', 'related_book_count', 'start_date', 'sign_date', 'validity_type', 'royalty_type']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'})
        
        record_id = create_record('contracts', data)
        if record_id is None:
            return jsonify({'success': False, 'error': '创建失败，请检查数据库连接或字段格式'})
        return jsonify({'success': True, 'id': record_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/contracts/<int:id>', methods=['GET'])
def get_contract(id):
    """获取单个合同"""
    try:
        record = get_record_by_id('contracts', id)
        if record:
            return jsonify({'success': True, 'data': record})
        return jsonify({'success': False, 'error': '记录不存在'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/contracts/<int:id>', methods=['PUT'])
@require_admin_token
def update_contract(id):
    """更新合同"""
    try:
        data = request.json
        result = update_record('contracts', id, data)
        if result:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': '更新失败，记录不存在或数据库错误'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/contracts/<int:id>', methods=['DELETE'])
@require_admin_token
def delete_contract(id):
    """删除合同"""
    result = delete_record('contracts', id)
    if result == 'success':
        return jsonify({'success': True})
    elif result == 'not_found':
        return jsonify({'success': False, 'error': '记录不存在'})
    elif result == 'foreign_key':
        return jsonify({'success': False, 'error': '该合同有关联图书或版税，无法删除'})
    else:
        return jsonify({'success': False, 'error': '删除失败'})

# ==================== 外版图书档案接口 ====================
@app.route('/api/books', methods=['GET'])
def get_books():
    """获取图书列表"""
    try:
        records = get_records('books', order_by='id DESC')
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/books', methods=['POST'])
@require_admin_token
def create_book():
    """创建图书"""
    try:
        data = request.json
        if 'contract_id' not in data or not data['contract_id']:
            return jsonify({'success': False, 'error': '缺少必填字段: 关联合同'})
        if 'original_title' not in data or not data['original_title']:
            return jsonify({'success': False, 'error': '缺少必填字段: 原文名'})
        if 'chinese_title' not in data or not data['chinese_title']:
            return jsonify({'success': False, 'error': '缺少必填字段: 中文名'})
        if 'publisher_name' not in data or not data['publisher_name']:
            return jsonify({'success': False, 'error': '缺少必填字段: 出版社名称'})
        if 'publisher_country' not in data or not data['publisher_country']:
            return jsonify({'success': False, 'error': '缺少必填字段: 出版社国家'})
        if 'reference_price' not in data or not data['reference_price']:
            return jsonify({'success': False, 'error': '缺少必填字段: 参考定价'})
        
        record_id = create_record('books', data)
        if record_id is None:
            return jsonify({'success': False, 'error': '创建失败，请检查数据库连接或字段格式'})
        return jsonify({'success': True, 'id': record_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/books/<int:id>', methods=['GET'])
def get_book(id):
    """获取单个图书"""
    try:
        record = get_record_by_id('books', id)
        if record:
            return jsonify({'success': True, 'data': record})
        return jsonify({'success': False, 'error': '记录不存在'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/books/<int:id>', methods=['PUT'])
@require_admin_token
def update_book(id):
    """更新图书"""
    try:
        data = request.json
        result = update_record('books', id, data)
        if result:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': '更新失败，记录不存在或数据库错误'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/books/<int:id>', methods=['DELETE'])
@require_admin_token
def delete_book(id):
    """删除图书"""
    result = delete_record('books', id)
    if result == 'success':
        return jsonify({'success': True})
    elif result == 'not_found':
        return jsonify({'success': False, 'error': '记录不存在'})
    elif result == 'foreign_key':
        return jsonify({'success': False, 'error': '该图书有关联版税，无法删除'})
    else:
        return jsonify({'success': False, 'error': '删除失败'})

# ==================== 意向选题库接口 ====================
@app.route('/api/topic-ideas', methods=['GET'])
def get_topic_ideas():
    """获取意向选题列表"""
    try:
        records = get_records('topic_ideas', order_by='id DESC')
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/topic-ideas', methods=['POST'])
@require_admin_token
def create_topic_idea():
    """创建意向选题"""
    try:
        data = request.json
        required = ['original_publisher_name', 'chinese_publisher_name', 'publisher_country', 'author_name', 'intention_date']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'})
        
        record_id = create_record('topic_ideas', data)
        if record_id is None:
            return jsonify({'success': False, 'error': '创建失败，请检查数据库连接或字段格式'})
        return jsonify({'success': True, 'id': record_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/topic-ideas/<int:id>', methods=['GET'])
def get_topic_idea(id):
    """获取单个意向选题"""
    try:
        record = get_record_by_id('topic_ideas', id)
        if record:
            return jsonify({'success': True, 'data': record})
        return jsonify({'success': False, 'error': '记录不存在'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/topic-ideas/<int:id>', methods=['PUT'])
@require_admin_token
def update_topic_idea(id):
    """更新意向选题"""
    try:
        data = request.json
        result = update_record('topic_ideas', id, data)
        if result:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': '更新失败，记录不存在或数据库错误'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/topic-ideas/<int:id>', methods=['DELETE'])
@require_admin_token
def delete_topic_idea(id):
    """删除意向选题"""
    result = delete_record('topic_ideas', id)
    if result == 'success':
        return jsonify({'success': True})
    elif result == 'not_found':
        return jsonify({'success': False, 'error': '记录不存在'})
    else:
        return jsonify({'success': False, 'error': '删除失败'})

# ==================== 版税管理接口 ====================
@app.route('/api/royalties', methods=['GET'])
def get_royalties():
    """获取版税列表"""
    try:
        records = get_records('royalties', order_by='id DESC')
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/royalties', methods=['POST'])
@require_admin_token
def create_royalty():
    """创建版税"""
    try:
        data = request.json
        required = ['contract_id', 'book_id', 'royalty_type']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'})
        
        record_id = create_record('royalties', data)
        if record_id is None:
            return jsonify({'success': False, 'error': '创建失败，请检查数据库连接或字段格式'})
        return jsonify({'success': True, 'id': record_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/royalties/<int:id>', methods=['GET'])
def get_royalty(id):
    """获取单个版税"""
    try:
        record = get_record_by_id('royalties', id)
        if record:
            return jsonify({'success': True, 'data': record})
        return jsonify({'success': False, 'error': '记录不存在'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/royalties/<int:id>', methods=['PUT'])
@require_admin_token
def update_royalty(id):
    """更新版税"""
    try:
        data = request.json
        result = update_record('royalties', id, data)
        if result:
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': '更新失败，记录不存在或数据库错误'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/royalties/<int:id>', methods=['DELETE'])
@require_admin_token
def delete_royalty(id):
    """删除版税"""
    result = delete_record('royalties', id)
    if result == 'success':
        return jsonify({'success': True})
    elif result == 'not_found':
        return jsonify({'success': False, 'error': '记录不存在'})
    else:
        return jsonify({'success': False, 'error': '删除失败'})

# ==================== 全局搜索接口 ====================
@app.route('/api/global-search', methods=['GET'])
def global_search():
    """全局搜索接口"""
    try:
        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return jsonify({'success': True, 'data': []})
        
        keyword_lower = keyword.lower()
        results = []
        
        # 搜索外版图书档案
        books = get_records('books', order_by='id DESC')
        for book in books:
            if (keyword_lower in str(book.get('original_title', '') or '').lower() or
                keyword_lower in str(book.get('chinese_title', '') or '').lower() or
                keyword_lower in str(book.get('publisher_name', '') or '').lower() or
                keyword_lower in str(book.get('publisher_country', '') or '').lower()):
                results.append({
                    'type': 'book',
                    'typeName': '图书档案',
                    'id': book['id'],
                    'title': book.get('chinese_title', '') or book.get('original_title', ''),
                    'subtitle': book.get('publisher_name', ''),
                    'status': book.get('book_status', '')
                })
        
        # 搜索合同管理
        contracts = get_records('contracts', order_by='id DESC')
        
        # 批量获取外商信息，避免N+1查询
        all_publishers = get_records('foreign_publishers')
        pub_map = {p['id']: p for p in all_publishers}
        
        for contract in contracts:
            # 从映射中获取外商名称
            publisher_name = ''
            if contract.get('foreign_publisher_id') and contract['foreign_publisher_id'] in pub_map:
                p = pub_map[contract['foreign_publisher_id']]
                publisher_name = p.get('chinese_name') or p.get('original_name', '')
            
            if (keyword_lower in str(contract.get('contract_name', '') or '').lower() or
                keyword_lower in publisher_name.lower()):
                results.append({
                    'type': 'contract',
                    'typeName': '合同',
                    'id': contract['id'],
                    'title': contract.get('contract_name', ''),
                    'subtitle': publisher_name,
                    'status': contract.get('contract_status', '')
                })
        
        # 搜索译者库
        translators = get_records('translators', order_by='id DESC')
        for translator in translators:
            if (keyword_lower in str(translator.get('name', '') or '').lower() or
                keyword_lower in str(translator.get('languages', '') or '').lower()):
                results.append({
                    'type': 'translator',
                    'typeName': '译者',
                    'id': translator['id'],
                    'title': translator.get('name', ''),
                    'subtitle': translator.get('languages', ''),
                    'status': translator.get('level', '')
                })
        
        # 搜索外商库
        publishers = get_records('foreign_publishers', order_by='id DESC')
        for publisher in publishers:
            if (keyword_lower in str(publisher.get('original_name', '') or '').lower() or
                keyword_lower in str(publisher.get('chinese_name', '') or '').lower() or
                keyword_lower in str(publisher.get('country', '') or '').lower()):
                results.append({
                    'type': 'foreignPublisher',
                    'typeName': '外商',
                    'id': publisher['id'],
                    'title': publisher.get('chinese_name', '') or publisher.get('original_name', ''),
                    'subtitle': publisher.get('original_name', ''),
                    'status': publisher.get('country', '')
                })
        
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==================== 文件上传接口 ====================
@app.route('/api/upload', methods=['POST'])
@require_admin_token
def upload_file():
    """上传文件接口（需要Token验证）"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'})
        
        # 检查文件类型（白名单校验）
        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'error': '不支持的文件类型，仅支持：PDF、Word文档(doc/docx)、图片(png/jpg)'
            })
        
        # 生成UUID文件名，保留原始扩展名
        ext = os.path.splitext(file.filename)[1]  # 获取扩展名（如 .pdf）
        file_id = uuid.uuid4().hex  # 生成32位UUID（无横杠）
        filename = f"{file_id}{ext}"  # 完整文件名
        
        # 保存文件到指定目录
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # 保存原始文件名到数据库
        original_filename = os.path.basename(file.filename)
        save_file_record(file_id, original_filename)
        
        # 返回文件ID（不返回路径，前端只保存ID）
        return jsonify({
            'success': True, 
            'file_id': file_id,  # 文件唯一标识（32位UUID）
            'filename': filename  # 完整文件名（含扩展名）
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==================== 文件下载接口 ====================
@app.route('/api/file/download', methods=['GET'])
@require_admin_token
def download_file():
    """文件下载接口（需要Token验证）"""
    try:
        file_id = request.args.get('id')
        
        if not file_id:
            return jsonify({'success': False, 'error': '缺少文件ID'})
        
        # 安全检查：文件ID必须是32位十六进制字符（UUID格式）
        if not all(c in '0123456789abcdef' for c in file_id.lower()) or len(file_id) != 32:
            return jsonify({'success': False, 'error': '非法的文件ID'})
        
        # 在上传目录中查找匹配的文件（ID相同，扩展名任意）
        matched_file = None
        for f in os.listdir(UPLOAD_FOLDER):
            if f.startswith(file_id):
                matched_file = f
                break
        
        if not matched_file:
            return jsonify({'success': False, 'error': '文件不存在'})
        
        # 构建完整路径并验证安全性
        file_path = os.path.join(UPLOAD_FOLDER, matched_file)
        real_upload_folder = os.path.realpath(UPLOAD_FOLDER)
        real_file_path = os.path.realpath(file_path)
        
        # 防止路径遍历攻击
        if not real_file_path.startswith(real_upload_folder):
            return jsonify({'success': False, 'error': '非法访问'})
        
        # 从数据库获取原始文件名，若无记录则使用UUID文件名
        original_filename = get_original_filename(file_id) or matched_file
        
        # 返回文件（自动设置Content-Type），使用原始文件名
        from flask import send_file
        return send_file(file_path, as_attachment=True, download_name=original_filename)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==================== 文件删除接口 ====================
@app.route('/api/file/delete', methods=['POST'])
@require_admin_token
def delete_file():
    """文件删除接口（需要Token验证）"""
    try:
        data = request.get_json()
        file_id = data.get('id')
        
        if not file_id:
            return jsonify({'success': False, 'error': '缺少文件ID'})
        
        # 安全检查：文件ID必须是32位十六进制字符（UUID格式）
        if not all(c in '0123456789abcdef' for c in file_id.lower()) or len(file_id) != 32:
            return jsonify({'success': False, 'error': '非法的文件ID'})
        
        # 在上传目录中查找匹配的文件
        matched_file = None
        for f in os.listdir(UPLOAD_FOLDER):
            if f.startswith(file_id):
                matched_file = f
                break
        
        if not matched_file:
            return jsonify({'success': False, 'error': '文件不存在'})
        
        # 构建完整路径并验证安全性
        file_path = os.path.join(UPLOAD_FOLDER, matched_file)
        real_upload_folder = os.path.realpath(UPLOAD_FOLDER)
        real_file_path = os.path.realpath(file_path)
        
        # 防止路径遍历攻击
        if not real_file_path.startswith(real_upload_folder):
            return jsonify({'success': False, 'error': '非法访问'})
        
        # 删除文件
        os.remove(file_path)
        
        return jsonify({'success': True, 'message': '文件删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==================== 枚举值接口 ====================
@app.route('/api/enums', methods=['GET'])
def get_enums():
    """获取枚举值"""
    enums = {
        'topicStatus': ['待洽谈', '洽谈中', '已签约', '已放弃'],
        'bookStatus': ['意向阶段', '合同签约阶段', '翻译中', '编辑中', '已出版', '近期需续约', '已过期', '已废弃'],
        'contractStatus': ['草稿', '已签约', '执行中', '已到期', '已作废'],
        'royaltyType': ['统一版税率', '阶梯版税率'],
        'validityType': ['签订日期开始', '出版日期开始'],
        'firstPrintRequirement': ['数量', '无要求'],
        'gender': ['男', '女'],
        'translatorLevel': ['初级', '中级', '高级', '资深'],
    }
    return jsonify({'success': True, 'data': enums})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    print("=" * 50)
    print("版权管理系统启动中...")
    print("=" * 50)
    init_db()
    print(f"\n服务运行在端口: {port}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)
