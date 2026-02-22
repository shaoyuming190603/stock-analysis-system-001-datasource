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
                             QMessageBox, QApplication)
from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import QAbstractItemView   # 如果使用 PyQt6

import config
import file_utils
import db_utils

class Form2(QWidget):
    def __init__(self):
        super().__init__()
        self.csv_files = []  # 存储文件路径列表
        self.checkboxes = []  # 存储复选框，便于全选
        self.init_ui()
        self.load_csv_files()
    
    def init_ui(self):
        self.setWindowTitle("数据更新到SQL数据库 - Form2")
        self.setGeometry(350, 350, 500, 400)
        
        self.label_info = QLabel("请选择要导入的CSV文件：")
        
        # 全选复选框
        self.cb_select_all = QCheckBox("全选")
        self.cb_select_all.stateChanged.connect(self.toggle_select_all)
        
        # 文件列表控件（使用QListWidget，但我们需要每个项带复选框，可以用QListWidget + QCheckBox作为item widget，但更简单是使用QListWidget设置标志）
        # 为了简单，我们使用QListWidget并设置项为可选中复选框模式
        self.list_widget = QListWidget()
        # self.list_widget.setSelectionMode(QListWidget.NoSelection)  # QT5语法，不兼容，所以此处禁用。禁止普通选择，通过复选框
        # self.list_widget.setSelectionMode(Qt.SelectionMode.NoSelection) # 改为QT6语法，禁止普通选择，通过复选框
        # self.list_widget.setSelectionMode(QAbstractItemView.NoSelection)  # 改为QT6语法，禁止普通选择，通过复选框
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)  # 正确PyQt6枚举
        # self.list_widget.setSelectionMode(self.list_widget.NoSelection) # 在212，23，42行产生多项错误

        self.btn_import = QPushButton("导入到数据库")
        self.btn_import.clicked.connect(self.import_to_db)
        
        # 布局
        vbox = QVBoxLayout()
        vbox.addWidget(self.label_info)
        vbox.addWidget(self.cb_select_all)
        vbox.addWidget(self.list_widget)
        vbox.addWidget(self.btn_import)
        self.setLayout(vbox)
    
    def load_csv_files(self):
        """加载下载目录中的所有csv文件，并显示在列表中"""
        self.csv_files = file_utils.get_csv_files(config.STOCK_DATA_DIR)
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
#         """获取用户选中的文件路径列表"""
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                file_path = item.data(Qt.ItemDataRole.UserRole)
                selected.append(file_path)
        return selected
    
    def import_to_db(self):
#         """执行导入数据库操作"""
        selected_files = self.get_selected_files()
        if not selected_files:
            QMessageBox.warning(self, "警告", "请至少选择一个文件")
            return
        
        # 初始化数据库连接
        try:
            conn = db_utils.get_db_connection()
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
            
            # 调用db_utils处理
            try:
                if data_type == "day":
                    db_utils.import_day_data(conn, stock_code, df)
                else:
                    db_utils.import_min_data(conn, stock_code, df)
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