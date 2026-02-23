# """
# GUI窗体2：CSV数据更新到SQL数据库界面
# """
import sys
import os
import re
import pandas as pd
import PyQt6.QtCore
from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout,
                             QListWidget, QListWidgetItem, QCheckBox,
                             QMessageBox, QApplication, QHBoxLayout, 
                             QRadioButton, QButtonGroup, QLineEdit, QGroupBox,
                             QFormLayout)
from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import QAbstractItemView   # 如果使用 PyQt6

import Data01_config
import Data01_file_utils
import Data01_db_utils

class Form2(QWidget):
    def __init__(self):
        super().__init__()
        self.csv_files = []  # 存储文件路径列表
        self.checkboxes = []  # 存储复选框，便于全选
        self.db_type = "mssql"  # 默认数据库类型
        self.init_ui()
        self.load_csv_files()
    
    def init_ui(self):
        self.setWindowTitle("数据更新到SQL数据库 - Form2")
        self.setGeometry(350, 350, 600, 600)
        
        self.label_info = QLabel("请选择要导入的CSV文件：")
        
        # 全选复选框
        self.cb_select_all = QCheckBox("全选")
        self.cb_select_all.stateChanged.connect(self.toggle_select_all)
        
        # 数据库类型选择
        self.label_db_type = QLabel("请设置要导入的数据库类型：")
        self.rb_mysql = QRadioButton("更新到mySQL")
        self.rb_mssql = QRadioButton("更新到MS SQL server")
        
        # 创建按钮组使单选框互斥
        self.db_group = QButtonGroup()
        self.db_group.addButton(self.rb_mysql, 1)
        self.db_group.addButton(self.rb_mssql, 2)
        
        # 默认选中MS SQL server
        self.rb_mssql.setChecked(True)
        self.db_group.buttonClicked.connect(self.on_db_type_changed)
        
        # 数据库参数设置区域
        self.mysql_group = QGroupBox("MySQL数据库设置")
        self.mssql_group = QGroupBox("MS SQL Server数据库设置")
        
        self.setup_db_params()
        
        # 文件列表控件
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        
        self.btn_import = QPushButton("导入到数据库")
        self.btn_import.clicked.connect(self.import_to_db)
        
        # 布局
        vbox = QVBoxLayout()
        vbox.addWidget(self.label_info)
        vbox.addWidget(self.cb_select_all)
        vbox.addWidget(self.list_widget)
        
        # 数据库类型选择布局
        db_type_layout = QHBoxLayout()
        db_type_layout.addWidget(self.rb_mysql)
        db_type_layout.addWidget(self.rb_mssql)
        db_type_layout.addStretch()
        
        vbox.addWidget(self.label_db_type)
        vbox.addLayout(db_type_layout)
        
        # 数据库参数设置布局
        vbox.addWidget(self.mysql_group)
        vbox.addWidget(self.mssql_group)
        
        # 初始状态设置
        self.update_db_param_visibility()
        
        vbox.addWidget(self.btn_import)
        self.setLayout(vbox)
    
    def setup_db_params(self):
        """设置数据库参数输入框"""
        # MySQL参数
        mysql_layout = QFormLayout()
        self.mysql_host = QLineEdit("localhost")
        self.mysql_port = QLineEdit("3306")
        self.mysql_user = QLineEdit("root")
        self.mysql_password = QLineEdit()
        self.mysql_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.mysql_database = QLineEdit("stock_db")
        
        mysql_layout.addRow("主机地址:", self.mysql_host)
        mysql_layout.addRow("端口:", self.mysql_port)
        mysql_layout.addRow("用户名:", self.mysql_user)
        mysql_layout.addRow("密码:", self.mysql_password)
        mysql_layout.addRow("数据库名:", self.mysql_database)
        self.mysql_group.setLayout(mysql_layout)
        
        # MS SQL Server参数
        mssql_layout = QFormLayout()
        self.mssql_server = QLineEdit("PC\SQLEXPRESS_BORIS")
        self.mssql_database_name = QLineEdit("stock_db")
        self.mssql_username = QLineEdit("PC\邵宇明")
        self.mssql_password = QLineEdit()
        self.mssql_password.setEchoMode(QLineEdit.EchoMode.Password)
        
        mssql_layout.addRow("服务器:", self.mssql_server)
        mssql_layout.addRow("数据库名:", self.mssql_database_name)
        mssql_layout.addRow("用户名:", self.mssql_username)
        mssql_layout.addRow("密码:", self.mssql_password)
        self.mssql_group.setLayout(mssql_layout)
    
    def on_db_type_changed(self, button):
        """数据库类型改变时的处理"""
        if button == self.rb_mysql:
            self.db_type = "mysql"
        else:
            self.db_type = "mssql"
        self.update_db_param_visibility()
    
    def update_db_param_visibility(self):
        """根据选择的数据库类型更新参数区域可见性"""
        self.mysql_group.setVisible(self.db_type == "mysql")
        self.mssql_group.setVisible(self.db_type == "mssql")
    
    def load_csv_files(self):
        """加载下载目录中的所有csv文件，并显示在列表中"""
        self.csv_files = Data01_file_utils.get_csv_files(Data01_config.STOCK_DATA_DIR)
        self.list_widget.clear()
        self.checkboxes.clear()
        for file_path in self.csv_files:
            item = QListWidgetItem(self.list_widget)
            # 修改点1：使用 Qt.ItemFlag.ItemIsUserCheckable
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setText(os.path.basename(file_path))
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.list_widget.addItem(item)
            self.checkboxes.append(item)
    
    def toggle_select_all(self, state):
        """全选/全不选"""
        # 修改点2：比较 state 与枚举的整数值
        check_state = Qt.CheckState.Checked if state == Qt.CheckState.Checked.value else Qt.CheckState.Unchecked
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(check_state)
    
    def get_selected_files(self):
        """获取用户选中的文件路径列表"""
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                file_path = item.data(Qt.ItemDataRole.UserRole)
                selected.append(file_path)
        return selected
    
    def get_db_connection_mssql(self):
        """获取MS SQL Server数据库连接"""
        try:
            import pyodbc
            server = self.mssql_server.text().strip()
            database = self.mssql_database_name.text().strip()
            username = self.mssql_username.text().strip()
            password = self.mssql_password.text().strip()
            
            if not all([server, database]):
                raise ValueError("MS SQL Server参数不完整")
            
            # 构建连接字符串
            if username and password:
                conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
            else:
                conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
            
            conn = pyodbc.connect(conn_str)
            return conn
        except ImportError:
            raise Exception("请安装pyodbc包: pip install pyodbc")
        except Exception as e:
            raise Exception(f"MS SQL Server连接失败: {str(e)}")
    
    def get_db_connection_mysql(self):
        """获取MySQL数据库连接"""
        try:
            import pymysql
            host = self.mysql_host.text().strip()
            port = int(self.mysql_port.text().strip())
            user = self.mysql_user.text().strip()
            password = self.mysql_password.text().strip()
            database = self.mysql_database.text().strip()
            
            if not all([host, user, database]):
                raise ValueError("MySQL参数不完整")
            
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                charset='utf8mb4'
            )
            return conn
        except ImportError:
            raise Exception("请安装pymysql包: pip install pymysql")
        except Exception as e:
            raise Exception(f"MySQL连接失败: {str(e)}")
    
    def import_day_data_mssql(self, conn, stock_code, df):
        """导入日线数据到MS SQL Server"""
        table_name = f"stock_{stock_code}_day"
        
        # 转换 trade_date 列：从 YYYYMMDD 整数转为 Python date 对象
        if 'trade_date' in df.columns:
            # 使用 pandas 将整数（如 20250101）解析为 datetime，再提取 date
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d').dt.date


        # 创建表（如果不存在）
        create_sql = f"""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{table_name}' AND xtype='U')
        CREATE TABLE {table_name} (
            [trade_date] DATE PRIMARY KEY,
            [open] DECIMAL(10,2),
            [high] DECIMAL(10,2),
            [low] DECIMAL(10,2),
            [close] DECIMAL(10,2),
            [pre_close] DECIMAL(10,2),
            [change] DECIMAL(10,2),
            [pct_chg] DECIMAL(10,2),
            [vol] BIGINT,
            [amount] DECIMAL(20,4),
            [ts_code] VARCHAR(20)
        )
        """
        cursor = conn.cursor()
        cursor.execute(create_sql)
        conn.commit()
        
        # 插入数据 确定DataFrame中存在的列
        columns = ['trade_date', 'open', 'high', 'low', 'close', 'pre_close', 'change', 'pct_chg', 'vol', 'amount', 'ts_code']
        cols_present = [col for col in columns if col in df.columns]
        # 将列名用方括号括起来
        cols_quoted = [f"[{col}]" for col in cols_present]
        
        # 使用MERGE语句实现upsert - 列名加方括号
        merge_sql = f"""
        MERGE {table_name} AS target
        USING (VALUES ({','.join(['?' for _ in cols_present])})) AS source ({','.join(cols_quoted)})
        ON target.[trade_date] = source.[trade_date]
        WHEN MATCHED THEN
            UPDATE SET {','.join([f'target.[{col}] = source.[{col}]' for col in cols_present if col != 'trade_date'])}
        WHEN NOT MATCHED THEN
            INSERT ({','.join(cols_quoted)}) VALUES ({','.join([f'source.[{col}]' for col in cols_present])});
        """
        
        for _, row in df.iterrows():
            values = [row[col] for col in cols_present]
            cursor.execute(merge_sql, values)
        conn.commit()
    
    def import_min_data_mssql(self, conn, stock_code, df):
        """导入分钟数据到MS SQL Server"""
        table_name = f"stock_{stock_code}_min"
        
        # 创建表（如果不存在）
        create_sql = f"""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{table_name}' AND xtype='U')
        CREATE TABLE {table_name} (
            [trade_time] DATETIME PRIMARY KEY,
            [open] DECIMAL(10,2),
            [high] DECIMAL(10,2),
            [low] DECIMAL(10,2),
            [close] DECIMAL(10,2),
            [volume] BIGINT,
            [amount] DECIMAL(20,4),
            [ts_code] VARCHAR(20)
        )
        """
        cursor = conn.cursor()
        cursor.execute(create_sql)
        conn.commit()
        
        # 插入数据
        columns = ['trade_time', 'open', 'high', 'low', 'close', 'volume', 'amount', 'ts_code']
        cols_present = [col for col in columns if col in df.columns]
        cols_quoted = [f"[{col}]" for col in cols_present]
        
        # 使用MERGE语句实现upsert
        merge_sql = f"""
        MERGE {table_name} AS target
        USING (VALUES ({','.join(['?' for _ in cols_present])})) AS source ({','.join(cols_quoted)})
        ON target.[trade_time] = source.[trade_time]
        WHEN MATCHED THEN
            UPDATE SET {','.join([f'target.[{col}] = source.[{col}]' for col in cols_present if col != 'trade_time'])}
        WHEN NOT MATCHED THEN
            INSERT ({','.join(cols_quoted)}) VALUES ({','.join([f'source.[{col}]' for col in cols_present])});
        """
        
        for _, row in df.iterrows():
            values = [row[col] for col in cols_present]
            cursor.execute(merge_sql, values)
        conn.commit()
    
    def import_to_db(self):
        """执行导入数据库操作"""
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "警告", "请至少选择一个文件")
            return
        
        # 获取数据库连接
        try:
            if self.db_type == "mysql":
                conn = self.get_db_connection_mysql()
                cursor = conn.cursor()
                cursor.execute("SELECT DB_NAME()")
                db_name = cursor.fetchone()[0]
                print(f"当前连接的数据库：{db_name}")



                import_func_day = Data01_db_utils.import_day_data
                import_func_min = Data01_db_utils.import_min_data
            else:  # mssql
                conn = self.get_db_connection_mssql()
                import_func_day = self.import_day_data_mssql
                import_func_min = self.import_min_data_mssql
        except Exception as e:
            QMessageBox.critical(self, "数据库连接失败", str(e))
            return
        
        success_count = 0
        fail_count = 0
        for file_path in selected_files:
            filename = os.path.basename(file_path)
            # 根据文件名判断是日数据还是分钟数据
            if "_day" in filename:
                data_type = "day"
            elif "_min" in filename:
                data_type = "min"
            else:
                print(f"跳过未知类型文件: {filename}")
                continue
            
            # 提取股票代码（前6位数字，假设文件名格式如 "300502.SZ_day.csv"）
            # 注意：可能包含.SZ等后缀，我们需要提取前6位数字。正则表达式提取数字
            import re
            match = re.search(r'(\d{6})', filename)
            if not match:
                print(f"无法从文件名提取股票代码: {filename}")
                fail_count += 1
                continue
            stock_code = match.group(1)
            
            # 读取csv文件到DataFrame
            import pandas as pd
            try:
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            except Exception as e:
                print(f"读取CSV失败 {file_path}: {e}")
                fail_count += 1
                continue
            
            # 调用对应的导入函数
            try:
                if data_type == "day":
                    import_func_day(conn, stock_code, df)
                else:
                    import_func_min(conn, stock_code, df)
                success_count += 1
            except Exception as e:
                print(f"导入数据失败 {file_path}: {e}")
                fail_count += 1
        
        conn.close()
        QMessageBox.information(self, "完成", f"导入完成！成功：{success_count}，失败：{fail_count}")
        # 可选刷新列表或关闭窗口
        self.close()

# 独立测试
if __name__ == '__main__':
    app = QApplication(sys.argv)
    form2 = Form2()
    form2.show()
    sys.exit(app.exec_())