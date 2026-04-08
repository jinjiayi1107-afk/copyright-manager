#!/usr/bin/env python3
"""
版权管理系统 - Flask后端API
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
from datetime import datetime
from database import (
    init_db, create_record, get_records, get_record_by_id,
    update_record, delete_record, count_records, get_statistics, get_reminders
)

app = Flask(__name__, static_folder='static')
CORS(app)

# 上传文件目录和配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 允许的文件类型
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}
# 文件大小限制：10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

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
def create_foreign_publisher():
    """创建外商"""
    try:
        data = request.json
        required = ['original_name', 'country']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'})
        
        record_id = create_record('foreign_publishers', data)
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
def update_foreign_publisher(id):
    """更新外商"""
    try:
        data = request.json
        update_record('foreign_publishers', id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/foreign-publishers/<int:id>', methods=['DELETE'])
def delete_foreign_publisher(id):
    """删除外商"""
    try:
        delete_record('foreign_publishers', id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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
def create_translator():
    """创建译者"""
    try:
        data = request.json
        if 'name' not in data or not data['name']:
            return jsonify({'success': False, 'error': '缺少必填字段: 姓名'})
        if 'languages' not in data or not data['languages']:
            return jsonify({'success': False, 'error': '缺少必填字段: 语种'})
        
        record_id = create_record('translators', data)
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
def update_translator(id):
    """更新译者"""
    try:
        data = request.json
        update_record('translators', id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/translators/<int:id>', methods=['DELETE'])
def delete_translator(id):
    """删除译者"""
    try:
        delete_record('translators', id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==================== 合同管理接口 ====================
@app.route('/api/contracts', methods=['GET'])
def get_contracts():
    """获取合同列表"""
    try:
        records = get_records('contracts', order_by='id DESC')
        # 补充外商名称
        for record in records:
            if record.get('foreign_publisher_id'):
                publisher = get_record_by_id('foreign_publishers', record['foreign_publisher_id'])
                if publisher:
                    record['foreign_publisher_name'] = publisher.get('chinese_name') or publisher.get('original_name')
        return jsonify({'success': True, 'data': records})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/contracts', methods=['POST'])
def create_contract():
    """创建合同"""
    try:
        data = request.json
        required = ['contract_name', 'related_book_count', 'start_date', 'sign_date', 'validity_type', 'royalty_type']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'})
        
        record_id = create_record('contracts', data)
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
def update_contract(id):
    """更新合同"""
    try:
        data = request.json
        update_record('contracts', id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/contracts/<int:id>', methods=['DELETE'])
def delete_contract(id):
    """删除合同"""
    try:
        delete_record('contracts', id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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
def update_book(id):
    """更新图书"""
    try:
        data = request.json
        update_record('books', id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    """删除图书"""
    try:
        delete_record('books', id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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
def create_topic_idea():
    """创建意向选题"""
    try:
        data = request.json
        required = ['original_publisher_name', 'chinese_publisher_name', 'publisher_country', 'author_name', 'intention_date']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'})
        
        record_id = create_record('topic_ideas', data)
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
def update_topic_idea(id):
    """更新意向选题"""
    try:
        data = request.json
        update_record('topic_ideas', id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/topic-ideas/<int:id>', methods=['DELETE'])
def delete_topic_idea(id):
    """删除意向选题"""
    try:
        delete_record('topic_ideas', id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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
def create_royalty():
    """创建版税"""
    try:
        data = request.json
        required = ['contract_id', 'book_id', 'royalty_type']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'缺少必填字段: {field}'})
        
        record_id = create_record('royalties', data)
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
def update_royalty(id):
    """更新版税"""
    try:
        data = request.json
        update_record('royalties', id, data)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/royalties/<int:id>', methods=['DELETE'])
def delete_royalty(id):
    """删除版税"""
    try:
        delete_record('royalties', id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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
            if (keyword_lower in str(book.get('publisher_name', '') or '').lower() or
                keyword_lower in str(book.get('contract_name', '') or '').lower() or
                keyword_lower in str(book.get('publisher_country', '') or '').lower()):
                results.append({
                    'type': 'book',
                    'typeName': '图书档案',
                    'id': book['id'],
                    'title': book.get('publisher_name', '') or book.get('contract_name', ''),
                    'subtitle': book.get('contract_name', ''),
                    'status': book.get('book_status', '')
                })
        
        # 搜索合同管理
        contracts = get_records('contracts', order_by='id DESC')
        for contract in contracts:
            # 获取外商名称
            publisher_name = ''
            if contract.get('foreign_publisher_id'):
                publisher = get_record_by_id('foreign_publishers', contract['foreign_publisher_id'])
                if publisher:
                    publisher_name = publisher.get('chinese_name') or publisher.get('original_name', '')
            
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
def upload_file():
    """上传文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '文件名为空'})
        
        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '不支持的文件类型，仅支持：PDF、图片(PNG/JPG)、Word文档'})
        
        # 检查文件大小
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_FILE_SIZE:
            return jsonify({'success': False, 'error': '文件大小超过10MB限制'})
        
        # 生成唯一文件名
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # 返回文件路径
        file_url = f"/uploads/{filename}"
        return jsonify({'success': True, 'filename': filename, 'url': file_url})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/uploads/<filename>')
def serve_uploaded_file(filename):
    """访问上传的文件"""
    return send_from_directory(UPLOAD_FOLDER, filename)

# ==================== 文件删除接口 ====================
@app.route('/api/delete-file', methods=['POST'])
def delete_file():
    """删除上传的文件"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({'success': False, 'error': '缺少文件路径'})
        
        # 安全检查：只允许删除uploads目录下的文件
        # 防止路径遍历攻击
        if '..' in file_path or file_path.startswith('/') or file_path.startswith('\\'):
            return jsonify({'success': False, 'error': '非法文件路径'})
        
        # 完整文件路径
        full_path = os.path.join(UPLOAD_FOLDER, file_path)
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'error': '文件不存在'})
        
        # 检查文件是否在uploads目录内（防止目录遍历）
        real_upload_folder = os.path.realpath(UPLOAD_FOLDER)
        real_file_path = os.path.realpath(full_path)
        if not real_file_path.startswith(real_upload_folder):
            return jsonify({'success': False, 'error': '非法文件路径'})
        
        # 删除文件
        os.remove(full_path)
        
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
