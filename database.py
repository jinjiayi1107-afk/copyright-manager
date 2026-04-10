#!/usr/bin/env python3
"""
版权管理系统 - 数据库模块
使用MySQL存储数据，支持事务和异常处理
包含SQL注入防护（白名单+参数化查询）
"""

import pymysql
from pymysql.cursors import DictCursor
import os
from datetime import datetime, timedelta

# ==================== 安全白名单 ====================
# 允许的表名（防止SQL注入）
ALLOWED_TABLES = {
    'topic_ideas', 'foreign_publishers', 'translators', 
    'contracts', 'books', 'royalties'
}

# 允许的排序字段（每个表的允许字段）
ALLOWED_ORDER_FIELDS = {
    'topic_ideas': {'id', 'intention_date', 'created_at', 'updated_at'},
    'foreign_publishers': {'id', 'original_name', 'country', 'created_at', 'updated_at'},
    'translators': {'id', 'name', 'languages', 'level', 'created_at', 'updated_at'},
    'contracts': {'id', 'contract_name', 'sign_date', 'end_date', 'contract_status', 'created_at', 'updated_at'},
    'books': {'id', 'original_title', 'chinese_title', 'book_status', 'created_at', 'updated_at'},
    'royalties': {'id', 'contract_id', 'book_id', 'created_at', 'updated_at'}
}

def validate_table(table):
    """验证表名是否在白名单中"""
    if table not in ALLOWED_TABLES:
        raise ValueError(f"非法的表名: {table}")
    return True

def validate_order_by(table, order_by):
    """验证排序字段是否合法"""
    if not order_by:
        return None
    
    # 解析排序字段（支持 DESC/ASC）
    parts = order_by.strip().split()
    field = parts[0].lower()
    
    if table not in ALLOWED_ORDER_FIELDS:
        return None
    if field not in ALLOWED_ORDER_FIELDS[table]:
        return None
    
    # 只允许字段名和排序方向
    if len(parts) > 1:
        direction = parts[1].upper()
        if direction not in ('ASC', 'DESC'):
            direction = 'ASC'
        return f"{field} {direction}"
    return field

# ==================== 数据库配置 ====================
# 从环境变量读取配置，支持不同部署环境
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER', 'copyright_user'),
    'password': os.environ.get('DB_PASSWORD', 'copyright123'),
    'database': os.environ.get('DB_NAME', 'copyright_manager'),
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}

# ==================== 连接管理 ====================
def get_db_connection():
    """
    获取数据库连接
    返回：pymysql连接对象
    异常：连接失败时打印错误并返回None
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"[数据库错误] 连接失败: {e}")
        return None

# ==================== 数据库初始化 ====================
def init_db():
    """
    初始化数据库表结构
    创建所有必要的表（如果不存在）
    """
    conn = get_db_connection()
    if not conn:
        print("[数据库错误] 无法连接数据库，初始化失败")
        return False
    
    cursor = conn.cursor()
    
    try:
        # 1. 意向选题库
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS topic_ideas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                original_publisher_name VARCHAR(200) NOT NULL,
                chinese_publisher_name VARCHAR(200) NOT NULL,
                publisher_country VARCHAR(50) NOT NULL,
                author_name VARCHAR(100) NOT NULL,
                author_country VARCHAR(50),
                author_gender VARCHAR(10),
                sample_file VARCHAR(500),
                intention_date DATE NOT NULL,
                intention_status VARCHAR(20) NOT NULL DEFAULT '待洽谈',
                remarks TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # 2. 外商库
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS foreign_publishers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                original_name VARCHAR(200) NOT NULL,
                chinese_name VARCHAR(200),
                country VARCHAR(50) NOT NULL,
                sample_book_received TINYINT(1) DEFAULT 0,
                contact_name VARCHAR(100),
                contact_title VARCHAR(100),
                contact_email VARCHAR(200),
                has_multiple_contacts TINYINT(1) DEFAULT 0,
                remarks TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # 3. 译者库
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS translators (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                resume_file VARCHAR(500),
                languages VARCHAR(100) NOT NULL,
                specialization VARCHAR(200),
                level VARCHAR(50),
                rate_per_thousand VARCHAR(50),
                contract_file VARCHAR(500),
                contract_date DATE,
                contact_info VARCHAR(500),
                remarks TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # 4. 合同管理
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contracts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contract_name VARCHAR(200) NOT NULL,
                contract_file VARCHAR(500),
                countersign_file VARCHAR(500),
                chinese_translation_file VARCHAR(500),
                related_book_count INT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                sign_date DATE NOT NULL,
                validity_years INT,
                validity_type VARCHAR(50) NOT NULL,
                auto_renewal TINYINT(1) DEFAULT 0,
                agent_id INT,
                commission_fee VARCHAR(50),
                foreign_publisher_id INT,
                authorization_scope TEXT,
                translator_id INT,
                advance_payment VARCHAR(50),
                advance_paid TINYINT(1) DEFAULT 0,
                royalty_type VARCHAR(50) NOT NULL,
                royalty_rate VARCHAR(50),
                tiered_royalty TEXT,
                first_print_quantity INT,
                first_print_requirement TEXT,
                editor_id INT,
                book_number VARCHAR(100),
                contract_status VARCHAR(50) NOT NULL DEFAULT '草稿',
                remarks TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                INDEX idx_contract_status (contract_status),
                INDEX idx_end_date (end_date),
                FOREIGN KEY (foreign_publisher_id) REFERENCES foreign_publishers(id),
                FOREIGN KEY (translator_id) REFERENCES translators(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # 5. 外版图书档案
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contract_id INT NOT NULL,
                original_title VARCHAR(300) NOT NULL,
                chinese_title VARCHAR(300) NOT NULL,
                publisher_name VARCHAR(200) NOT NULL,
                publisher_country VARCHAR(50) NOT NULL,
                translator_id INT,
                translator_languages VARCHAR(100),
                book_number VARCHAR(100),
                sample_sent TINYINT(1) DEFAULT 0,
                reference_price VARCHAR(50) NOT NULL,
                actual_price VARCHAR(50),
                contract_reference_price VARCHAR(50),
                contract_actual_price VARCHAR(50),
                editor_sample_file VARCHAR(500),
                review_sample_file VARCHAR(500),
                quotation_file VARCHAR(500),
                contract_scan_file VARCHAR(500),
                countersign_file VARCHAR(500),
                book_status VARCHAR(50) NOT NULL DEFAULT '意向阶段',
                remarks TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                INDEX idx_book_status (book_status),
                FOREIGN KEY (contract_id) REFERENCES contracts(id),
                FOREIGN KEY (translator_id) REFERENCES translators(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        # 6. 版税管理
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS royalties (
                id INT AUTO_INCREMENT PRIMARY KEY,
                contract_id INT NOT NULL,
                book_id INT NOT NULL,
                royalty_type VARCHAR(50) NOT NULL,
                royalty_rate VARCHAR(50),
                tiered_structure TEXT,
                advance_amount VARCHAR(50),
                advance_paid TINYINT(1) DEFAULT 0,
                payment_cycle VARCHAR(50),
                last_payment_date DATE,
                total_paid_amount VARCHAR(50),
                report_date DATE,
                payment_reminder TINYINT(1) DEFAULT 0,
                remarks TEXT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                FOREIGN KEY (contract_id) REFERENCES contracts(id),
                FOREIGN KEY (book_id) REFERENCES books(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        ''')
        
        conn.commit()
        print("[数据库] 初始化完成")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"[数据库错误] 初始化失败: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# ==================== CRUD操作 ====================
def create_record(table, data):
    """
    创建记录
    参数：table - 表名, data - 字典形式的数据
    返回：记录ID（成功）或 None（失败）
    """
    try:
        validate_table(table)
    except ValueError as e:
        print(f"[数据库错误] {e}")
        return None
    
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data['created_at'] = now
        data['updated_at'] = now
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s' for _ in data])
        sql = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
        
        cursor.execute(sql, list(data.values()))
        conn.commit()
        
        return cursor.lastrowid
        
    except Exception as e:
        conn.rollback()
        print(f"[数据库错误] 创建记录失败: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_records(table, order_by='id DESC'):
    """
    获取记录列表
    参数：table - 表名, order_by - 排序字段
    返回：记录列表（字典形式）
    注意：排序字段已白名单校验，条件查询请使用get_records_by_condition
    """
    try:
        validate_table(table)
        order_by = validate_order_by(table, order_by)
    except ValueError as e:
        print(f"[数据库错误] {e}")
        return []
    
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    
    try:
        sql = f'SELECT * FROM {table}'
        if order_by:
            sql += f' ORDER BY {order_by}'
        
        cursor.execute(sql)
        return cursor.fetchall() or []
        
    except Exception as e:
        print(f"[数据库错误] 查询记录失败: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_records_by_condition(table, conditions, order_by='id DESC'):
    """
    条件查询记录（参数化查询，防止SQL注入）
    参数：table - 表名, conditions - 条件字典{字段: 值}, order_by - 排序字段
    返回：记录列表
    """
    try:
        validate_table(table)
        order_by = validate_order_by(table, order_by)
    except ValueError as e:
        print(f"[数据库错误] {e}")
        return []
    
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    
    try:
        sql = f'SELECT * FROM {table}'
        params = []
        
        if conditions:
            where_parts = [f'{k} = %s' for k in conditions.keys()]
            sql += ' WHERE ' + ' AND '.join(where_parts)
            params = list(conditions.values())
        
        if order_by:
            sql += f' ORDER BY {order_by}'
        
        cursor.execute(sql, params)
        return cursor.fetchall() or []
        
    except Exception as e:
        print(f"[数据库错误] 条件查询失败: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_record_by_id(table, record_id):
    """
    根据ID获取单条记录
    参数：table - 表名, record_id - 记录ID
    返回：记录字典（存在）或 None（不存在）
    """
    try:
        validate_table(table)
    except ValueError as e:
        print(f"[数据库错误] {e}")
        return None
    
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor()
    
    try:
        cursor.execute(f'SELECT * FROM {table} WHERE id = %s', (record_id,))
        return cursor.fetchone()
        
    except Exception as e:
        print(f"[数据库错误] 查询记录失败: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_record(table, record_id, data):
    """
    更新记录
    参数：table - 表名, record_id - 记录ID, data - 更新数据
    返回：True（成功）或 False（失败）
    """
    try:
        validate_table(table)
    except ValueError as e:
        print(f"[数据库错误] {e}")
        return False
    
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        set_clause = ', '.join([f'{key} = %s' for key in data.keys()])
        sql = f'UPDATE {table} SET {set_clause} WHERE id = %s'
        
        cursor.execute(sql, list(data.values()) + [record_id])
        conn.commit()
        return cursor.rowcount > 0
        
    except Exception as e:
        conn.rollback()
        print(f"[数据库错误] 更新记录失败: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def delete_record(table, record_id):
    """
    删除记录
    参数：table - 表名, record_id - 记录ID
    返回：'success'-成功, 'not_found'-记录不存在, 'foreign_key'-外键约束, 'error'-其他错误
    """
    try:
        validate_table(table)
    except ValueError as e:
        print(f"[数据库错误] {e}")
        return 'error'
    
    conn = get_db_connection()
    if not conn:
        return 'error'
    
    cursor = conn.cursor()
    
    try:
        # 先检查记录是否存在
        cursor.execute(f'SELECT id FROM {table} WHERE id = %s', (record_id,))
        if not cursor.fetchone():
            return 'not_found'
        
        # 尝试删除
        cursor.execute(f'DELETE FROM {table} WHERE id = %s', (record_id,))
        conn.commit()
        return 'success'
        
    except pymysql.err.IntegrityError as e:
        conn.rollback()
        error_code = e.args[0]
        if error_code == 1451:  # 外键约束阻止删除
            print(f"[数据库警告] 记录被其他数据引用，无法删除")
            return 'foreign_key'
        print(f"[数据库错误] 删除记录失败: {e}")
        return 'error'
    except Exception as e:
        conn.rollback()
        print(f"[数据库错误] 删除记录失败: {e}")
        return 'error'
    finally:
        cursor.close()
        conn.close()

def count_records(table):
    """
    统计记录数量
    参数：table - 表名
    返回：记录数量
    """
    try:
        validate_table(table)
    except ValueError as e:
        print(f"[数据库错误] {e}")
        return 0
    
    conn = get_db_connection()
    if not conn:
        return 0
    
    cursor = conn.cursor()
    
    try:
        cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
        result = cursor.fetchone()
        return result['count'] if result else 0
        
    except Exception as e:
        print(f"[数据库错误] 统计记录失败: {e}")
        return 0
    finally:
        cursor.close()
        conn.close()

# ==================== 统计与提醒 ====================
def get_statistics():
    """
    获取统计数据（优化版：单连接完成所有统计）
    """
    conn = get_db_connection()
    if not conn:
        return {}
    
    cursor = conn.cursor()
    
    try:
        stats = {
            'total_books': 0,
            'total_contracts': 0,
            'total_translators': 0,
            'total_foreign_publishers': 0,
            'total_topic_ideas': 0,
            'total_royalties': 0,
            'books_by_status': {},
            'contracts_by_status': {},
            'topic_ideas_by_status': {},
        }
        
        # 统计各表总数
        for table in ['books', 'contracts', 'translators', 'foreign_publishers', 'topic_ideas', 'royalties']:
            cursor.execute(f'SELECT COUNT(*) as count FROM {table}')
            result = cursor.fetchone()
            stats[f'total_{table}'] = result['count'] if result else 0
        
        # 图书状态统计
        cursor.execute('SELECT book_status, COUNT(*) as count FROM books GROUP BY book_status')
        for row in cursor.fetchall():
            stats['books_by_status'][row['book_status']] = row['count']
        
        # 合同状态统计
        cursor.execute('SELECT contract_status, COUNT(*) as count FROM contracts GROUP BY contract_status')
        for row in cursor.fetchall():
            stats['contracts_by_status'][row['contract_status']] = row['count']
        
        # 意向选题状态统计
        cursor.execute('SELECT intention_status, COUNT(*) as count FROM topic_ideas GROUP BY intention_status')
        for row in cursor.fetchall():
            stats['topic_ideas_by_status'][row['intention_status']] = row['count']
        
        return stats
        
    except Exception as e:
        print(f"[数据库错误] 获取统计失败: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

def get_reminders():
    """获取所有待提醒项目"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    
    try:
        reminders = []
        today = datetime.now()
        today_str = today.strftime('%Y-%m-%d')
        thirty_days_later = (today + timedelta(days=30)).strftime('%Y-%m-%d')
        ninety_days_ago = (today - timedelta(days=90)).strftime('%Y-%m-%d')
        sixty_days_ago = (today - timedelta(days=60)).strftime('%Y-%m-%d')
        
        # 合同到期提醒
        cursor.execute('''
            SELECT c.id, c.contract_name, c.end_date, fp.chinese_name as foreign_publisher_name,
                   DATEDIFF(c.end_date, %s) as days_left
            FROM contracts c
            LEFT JOIN foreign_publishers fp ON c.foreign_publisher_id = fp.id
            WHERE c.end_date IS NOT NULL 
              AND c.contract_status = '执行中'
              AND c.end_date >= %s
              AND c.end_date <= %s
            ORDER BY c.end_date ASC
        ''', (today_str, today_str, thirty_days_later))
        
        for row in cursor.fetchall():
            reminders.append({
                'type': 'contract_expiring',
                'title': f'合同即将到期：{row["contract_name"]}',
                'description': f'剩余 {row["days_left"]} 天到期',
                'detail': f'外方出版社：{row["foreign_publisher_name"] or "未指定"}',
                'date': row["end_date"],
                'days_left': row["days_left"],
                'priority': 'warning' if row["days_left"] <= 7 else 'normal',
                'record_id': row['id'],
                'module': 'contracts'
            })
        
        # 意向选题紧急提醒
        cursor.execute('''
            SELECT id, chinese_publisher_name, author_name, intention_date,
                   DATEDIFF(%s, intention_date) as days_passed
            FROM topic_ideas
            WHERE intention_status = '待洽谈'
              AND intention_date <= %s
            ORDER BY days_passed DESC
        ''', (today_str, ninety_days_ago))
        
        for row in cursor.fetchall():
            reminders.append({
                'type': 'topic_urgent',
                'title': f'选题洽谈紧急：{row["chinese_publisher_name"]}',
                'description': f'已等待 {row["days_passed"]} 天',
                'detail': f'作者：{row["author_name"]}',
                'date': row["intention_date"],
                'days_passed': row["days_passed"],
                'priority': 'urgent',
                'record_id': row['id'],
                'module': 'topicIdeas'
            })
        
        # 意向选题初级提醒
        cursor.execute('''
            SELECT id, chinese_publisher_name, author_name, intention_date,
                   DATEDIFF(%s, intention_date) as days_passed
            FROM topic_ideas
            WHERE intention_status = '待洽谈'
              AND intention_date > %s
              AND intention_date <= %s
            ORDER BY days_passed DESC
        ''', (today_str, ninety_days_ago, sixty_days_ago))
        
        for row in cursor.fetchall():
            reminders.append({
                'type': 'topic_warning',
                'title': f'选题待洽谈提醒：{row["chinese_publisher_name"]}',
                'description': f'已等待 {row["days_passed"]} 天',
                'detail': f'作者：{row["author_name"]}',
                'date': row["intention_date"],
                'days_passed': row["days_passed"],
                'priority': 'warning',
                'record_id': row['id'],
                'module': 'topicIdeas'
            })
        
        return reminders
        
    except Exception as e:
        print(f"[数据库错误] 获取提醒失败: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# ==================== 主入口 ====================
if __name__ == '__main__':
    init_db()
