# """
# 数据库操作工具模块，支持SQLite和MySQL配置。
# 根据config中的DB_TYPE选择。
# """
import sqlite3
import pandas as pd
from datetime import datetime
import config

def get_db_connection():
#     """根据配置获取数据库连接"""
    if config.DB_TYPE == "sqlite":
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        # 启用外键支持（可选）
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    elif config.DB_TYPE == "mysql":
        # 需要安装pymysql或mysql-connector-python
        import pymysql
        conn = pymysql.connect(
            host=config.MYSQL_CONFIG['host'],
            port=config.MYSQL_CONFIG['port'],
            user=config.MYSQL_CONFIG['user'],
            password=config.MYSQL_CONFIG['password'],
            database=config.MYSQL_CONFIG['database'],
            charset='utf8mb4'
        )
        return conn
    else:
        raise ValueError(f"不支持的数据库类型: {config.DB_TYPE}")

def create_day_table_if_not_exists(conn, stock_code):
#     """创建日线数据表（如果不存在），主键为日期"""
    table_name = f"stock_{stock_code}_day"
    if config.DB_TYPE == "sqlite":
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            trade_date TEXT PRIMARY KEY,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            pre_close REAL,
            change REAL,
            pct_chg REAL,
            vol REAL,
            amount REAL,
            ts_code TEXT
        )
        """
    else:  # mysql
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            trade_date DATE PRIMARY KEY,
            open DECIMAL(10,2),
            high DECIMAL(10,2),
            low DECIMAL(10,2),
            close DECIMAL(10,2),
            pre_close DECIMAL(10,2),
            change DECIMAL(10,2),
            pct_chg DECIMAL(10,2),
            vol BIGINT,
            amount DECIMAL(20,4),
            ts_code VARCHAR(20)
        )
        """
    cursor = conn.cursor()
    cursor.execute(create_sql)
    conn.commit()

def create_min_table_if_not_exists(conn, stock_code):
#     """创建分钟数据表（如果不存在），主键为时间"""
    table_name = f"stock_{stock_code}_min"
    # 分钟数据表结构假设包含 trade_time 或类似列
    # 根据tushare分钟数据接口调整列名
    if config.DB_TYPE == "sqlite":
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            trade_time TEXT PRIMARY KEY,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            amount REAL,
            ts_code TEXT
        )
        """
    else:
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            trade_time DATETIME PRIMARY KEY,
            open DECIMAL(10,2),
            high DECIMAL(10,2),
            low DECIMAL(10,2),
            close DECIMAL(10,2),
            volume BIGINT,
            amount DECIMAL(20,4),
            ts_code VARCHAR(20)
        )
        """
    cursor = conn.cursor()
    cursor.execute(create_sql)
    conn.commit()

def import_day_data(conn, stock_code, df):
#     """
#     导入日线数据到对应表。如果表不存在则创建，然后使用INSERT OR REPLACE或类似方式。
#     假设DataFrame包含列：trade_date, open, high, low, close, ... 
#     具体列名需与tushare返回一致。
#     """
    table_name = f"stock_{stock_code}_day"
    create_day_table_if_not_exists(conn, stock_code)
    
    # 处理数据，确保列名匹配
    # 假设df包含标准tushare daily列，如trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount, ts_code
    # 我们需要根据实际列名调整
    # 将数据写入数据库，使用replace策略（如果主键冲突则替换）
    df_to_insert = df.copy()
    # 如果日期列是trade_date，确保为字符串，方便SQLite
    if 'trade_date' in df_to_insert.columns:
        df_to_insert['trade_date'] = df_to_insert['trade_date'].astype(str)
    
    # 写入数据库，使用pandas的to_sql，设置if_exists='append'，但主键冲突会导致错误，需使用replace
    # 对于SQLite，可以使用INSERT OR REPLACE，但pandas to_sql不支持。所以手动执行。
    # 手动逐行插入，使用replace语法。
    # 简化：使用pandas to_sql并设置if_exists='append'，然后假设主键冲突由数据库处理（需表设置主键，且使用replace？）
    # 更稳健：手动编写replace语句。
    # 为了代码简洁，我们使用pandas的to_sql，但需要处理重复主键。SQLite支持INSERT OR REPLACE，但pandas to_sql默认是INSERT。
    # 我们可以先将数据写入临时表，然后合并，但较复杂。这里采用逐行upsert。
    # 但数据量可能不大，逐行效率可接受。
    cursor = conn.cursor()
    for _, row in df_to_insert.iterrows():
        # 构建插入语句（适用于SQLite）
        # 列名需要根据实际df列处理。这里简化，假设df列是固定的
        # 实际使用时，可能需要更通用处理，如根据df列动态生成。
        # 假设列列表如下（根据tushare daily文档）：
        columns = ['trade_date', 'open', 'high', 'low', 'close', 'pre_close', 'change', 'pct_chg', 'vol', 'amount', 'ts_code']
        # 过滤出df中存在的列
        cols_present = [col for col in columns if col in df_to_insert.columns]
        placeholders = ','.join(['?' for _ in cols_present])
        col_names = ','.join(cols_present)
        # 生成替换语句
        if config.DB_TYPE == "sqlite":
            sql = f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})"
        else:  # mysql使用 REPLACE INTO
            sql = f"REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})"
        values = [row[col] for col in cols_present]
        cursor.execute(sql, values)
    conn.commit()

def import_min_data(conn, stock_code, df):
#     """
#     导入分钟数据到对应表。类似日数据，但主键可能是trade_time。
#     假设df包含列：trade_time, open, high, low, close, volume, amount, ts_code等。
#     """
    table_name = f"stock_{stock_code}_min"
    create_min_table_if_not_exists(conn, stock_code)
    
    cursor = conn.cursor()
    # 根据tushare分钟数据接口调整列名
    # 假设列有：trade_time, open, high, low, close, volume, amount, ts_code
    columns = ['trade_time', 'open', 'high', 'low', 'close', 'volume', 'amount', 'ts_code']
    cols_present = [col for col in columns if col in df.columns]
    placeholders = ','.join(['?' for _ in cols_present])
    col_names = ','.join(cols_present)
    
    for _, row in df.iterrows():
        if config.DB_TYPE == "sqlite":
            sql = f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})"
        else:
            sql = f"REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})"
        values = [row[col] for col in cols_present]
        cursor.execute(sql, values)
    conn.commit()