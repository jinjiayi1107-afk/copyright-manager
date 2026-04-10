#!/usr/bin/env python3
"""
版权管理系统 - 数据库模块
使用MySQL存储数据
"""

import pymysql
from pymysql.cursors import DictCursor
import os
from datetime import datetime

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'copyright_user',
    'password': 'copyright123',
    'database': 'copyright_manager',
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def init_db():
    """初始化数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
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
    conn.close()
    print("MySQL数据库初始化完成！")

# CRUD操作函数
def create_record(table, data):
    """创建记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['created_at'] = now
    data['updated_at'] = now
    
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['%s' for _ in data])
    cursor.execute(f'INSERT INTO {table} ({columns}) VALUES ({placeholders})', list(data.values()))
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return record_id

def get_records(table, conditions=None, order_by=None):
    """获取记录列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = f'SELECT * FROM {table}'
    if conditions:
        query += f' WHERE {conditions}'
    if order_by:
        query += f' ORDER BY {order_by}'
    
    cursor.execute(query)
    records = cursor.fetchall()
    conn.close()
    return records

def get_record_by_id(table, record_id):
    """根据ID获取单条记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM {table} WHERE id = %s', (record_id,))
    record = cursor.fetchone()
    conn.close()
    return record if record else None

def update_record(table, record_id, data):
    """更新记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    set_clause = ', '.join([f'{key} = %s' for key in data.keys()])
    cursor.execute(f'UPDATE {table} SET {set_clause} WHERE id = %s', list(data.values()) + [record_id])
    conn.commit()
    conn.close()

def delete_record(table, record_id):
    """删除记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM {table} WHERE id = %s', (record_id,))
    conn.commit()
    conn.close()

def count_records(table, conditions=None):
    """统计记录数量"""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f'SELECT COUNT(*) as count FROM {table}'
    if conditions:
        query += f' WHERE {conditions}'
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result['count']

def get_statistics():
    """获取统计数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {
        'total_books': count_records('books'),
        'total_contracts': count_records('contracts'),
        'total_translators': count_records('translators'),
        'total_foreign_publishers': count_records('foreign_publishers'),
        'total_topic_ideas': count_records('topic_ideas'),
        'total_royalties': count_records('royalties'),
        # 按状态统计
        'books_by_status': {},
        'contracts_by_status': {},
        'topic_ideas_by_status': {},
    }
    
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
    
    conn.close()
    return stats

def get_reminders():
    """获取所有待提醒项目"""
    from datetime import timedelta
    conn = get_db_connection()
    cursor = conn.cursor()
    
    reminders = []
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    thirty_days_later = (today + timedelta(days=30)).strftime('%Y-%m-%d')
    ninety_days_ago = (today - timedelta(days=90)).strftime('%Y-%m-%d')
    sixty_days_ago = (today - timedelta(days=60)).strftime('%Y-%m-%d')
    
    # 1. 合同到期提醒（30天内到期的执行中合同）
    cursor.execute('''
        SELECT id, contract_name, end_date, foreign_publisher_name,
               DATEDIFF(end_date, %s) as days_left
        FROM contracts c
        LEFT JOIN foreign_publishers fp ON c.foreign_publisher_id = fp.id
        WHERE end_date IS NOT NULL 
          AND end_date != ''
          AND contract_status = '执行中'
          AND end_date >= %s
          AND end_date <= %s
        ORDER BY end_date ASC
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
    
    # 2. 意向选题超时提醒 - 紧急（超过90天未洽谈）
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
    
    # 3. 意向选题超时提醒 - 初级（超过30天但不超过90天）
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
    
    conn.close()
    return reminders

def migrate_from_sqlite(sqlite_path):
    """从SQLite迁移数据到MySQL"""
    import sqlite3
    
    print(f"开始从SQLite迁移数据: {sqlite_path}")
    
    # 连接SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # 连接MySQL
    mysql_conn = get_db_connection()
    mysql_cursor = mysql_conn.cursor()
    
    tables = ['topic_ideas', 'foreign_publishers', 'translators', 'contracts', 'books', 'royalties']
    
    for table in tables:
        try:
            # 获取SQLite数据
            sqlite_cursor.execute(f'SELECT * FROM {table}')
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f'{table}: 无数据')
                continue
            
            # 构建插入语句
            columns = list(rows[0].keys())
            placeholders = ', '.join(['%s' for _ in columns])
            columns_str = ', '.join(columns)
            
            # 插入到MySQL
            for row in rows:
                values = [row[col] for col in columns]
                try:
                    mysql_cursor.execute(
                        f'INSERT INTO {table} ({columns_str}) VALUES ({placeholders})',
                        values
                    )
                except Exception as e:
                    print(f'插入失败: {e}')
                    continue
            
            mysql_conn.commit()
            print(f'{table}: 迁移 {len(rows)} 条记录')
        except Exception as e:
            print(f'{table} 迁移失败: {e}')
    
    sqlite_conn.close()
    mysql_conn.close()
    print("数据迁移完成！")

# 初始化数据库
if __name__ == '__main__':
    init_db()
