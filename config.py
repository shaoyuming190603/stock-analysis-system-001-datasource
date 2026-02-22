# """
# 配置文件，包含程序运行所需的各种常量、路径、token等。
# """
import os

# 基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 下载数据存储文件夹
STOCK_DATA_DIR = os.path.join(BASE_DIR, "002_StockDownLoad")

# 日志文件（Excel格式）
LOG_DAY_FILE = os.path.join(STOCK_DATA_DIR, "002_StockDownLoad_log_day.xlsx")
LOG_MIN_FILE = os.path.join(STOCK_DATA_DIR, "002_StockDownLoad_log_min.xlsx")

# tushare token，建议从环境变量获取，避免硬编码
# 可以在系统环境变量中设置 TUSHARE_TOKEN
TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN", "你的默认token")
if not TUSHARE_TOKEN:
    raise ValueError("TUSHARE_TOKEN  未在 .env 文件中设置")

# 数据库配置（以SQLite为例，可以改为MySQL等）
DB_TYPE = "sqlite"  # 可选 "sqlite", "mysql"
# SQLite数据库文件路径
SQLITE_DB_PATH = os.path.join(BASE_DIR, "stock_data.db")
# MySQL配置示例（如果使用MySQL需要配置以下参数）
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "password",
    "database": "stock_db"
}