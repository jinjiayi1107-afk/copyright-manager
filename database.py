#!/usr/bin/env python3
"""
版权管理系统 - 数据库模块
使用SQLite存储数据
"""

import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'copyright_manager.db')

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 意向选题库
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topic_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_publisher_name TEXT NOT NULL,
            chinese_publisher_name TEXT NOT NULL,
            publisher_country TEXT NOT NULL,
            author_name TEXT NOT NULL,
            author_country TEXT,
            author_gender TEXT,
            sample_file TEXT,
            intention_date TEXT NOT NULL,
            intention_status TEXT NOT NULL DEFAULT '待洽谈',
            remarks TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # 2. 外商库
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS foreign_publishers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_name TEXT NOT NULL,
            chinese_name TEXT,
            country TEXT NOT NULL,
            sample_book_received INTEGER DEFAULT 0,
            contact_name TEXT,
            contact_title TEXT,
            contact_email TEXT,
            has_multiple_contacts INTEGER DEFAULT 0,
            remarks TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # 3. 译者库
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS translators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            resume_file TEXT,
            languages TEXT NOT NULL,
            specialization TEXT,
            level TEXT,
            rate_per_thousand TEXT,
            contract_file TEXT,
            contract_date TEXT,
            contact_info TEXT,
            remarks TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # 4. 合同管理
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_name TEXT NOT NULL,
            contract_file TEXT,
            countersign_file TEXT,
            chinese_translation_file TEXT,
            related_book_count INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,
            sign_date TEXT NOT NULL,
            validity_years INTEGER,
            validity_type TEXT NOT NULL,
            auto_renewal INTEGER DEFAULT 0,
            agent_id INTEGER,
            commission_fee TEXT,
            foreign_publisher_id INTEGER,
            authorization_scope TEXT,
            translator_id INTEGER,
            advance_payment TEXT,
            advance_paid INTEGER DEFAULT 0,
            royalty_type TEXT NOT NULL,
            royalty_rate TEXT,
            tiered_royalty TEXT,
            first_print_quantity INTEGER,
            first_print_requirement TEXT,
            editor_id INTEGER,
            book_number TEXT,
            contract_status TEXT NOT NULL DEFAULT '草稿',
            remarks TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (foreign_publisher_id) REFERENCES foreign_publishers(id),
            FOREIGN KEY (translator_id) REFERENCES translators(id)
        )
    ''')
    
    # 5. 外版图书档案
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER NOT NULL,
            publisher_name TEXT NOT NULL,
            publisher_country TEXT NOT NULL,
            contract_name TEXT NOT NULL,
            translator_id INTEGER,
            translator_languages TEXT,
            book_number TEXT,
            sample_sent INTEGER DEFAULT 0,
            reference_price TEXT NOT NULL,
            actual_price TEXT,
            contract_reference_price TEXT,
            contract_actual_price TEXT,
            editor_sample_file TEXT,
            review_sample_file TEXT,
            quotation_file TEXT,
            contract_scan_file TEXT,
            countersign_file TEXT,
            book_status TEXT NOT NULL DEFAULT '意向阶段',
            remarks TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (contract_id) REFERENCES contracts(id),
            FOREIGN KEY (translator_id) REFERENCES translators(id)
        )
    ''')
    
    # 6. 版税管理
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS royalties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            royalty_type TEXT NOT NULL,
            royalty_rate TEXT,
            tiered_structure TEXT,
            advance_amount TEXT,
            advance_paid INTEGER DEFAULT 0,
            payment_cycle TEXT,
            last_payment_date TEXT,
            total_paid_amount TEXT,
            report_date TEXT,
            payment_reminder INTEGER DEFAULT 0,
            remarks TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (contract_id) REFERENCES contracts(id),
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("数据库初始化完成！")

# CRUD操作函数
def create_record(table, data):
    """创建记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['created_at'] = now
    data['updated_at'] = now
    
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data])
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
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return records

def get_record_by_id(table, record_id):
    """根据ID获取单条记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM {table} WHERE id = ?', (record_id,))
    record = cursor.fetchone()
    conn.close()
    return dict(record) if record else None

def update_record(table, record_id, data):
    """更新记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    set_clause = ', '.join([f'{key} = ?' for key in data.keys()])
    cursor.execute(f'UPDATE {table} SET {set_clause} WHERE id = ?', list(data.values()) + [record_id])
    conn.commit()
    conn.close()

def delete_record(table, record_id):
    """删除记录"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM {table} WHERE id = ?', (record_id,))
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

if __name__ == '__main__':
    init_db()
