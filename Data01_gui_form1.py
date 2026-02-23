# """
# GUI窗体1：股票数据下载界面
# 使用PyQt6实现。
# 修改说明：
#   - 支持选择 Excel (.xlsx) 股票清单文件
#   - 读取时强制将日期列作为字符串，保留 YYYYMMDD 格式
#   - 文件读取由 file_utils.read_stock_list 统一处理
# """
import sys
import os
import time
from datetime import timedelta
from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QFileDialog,
                             QVBoxLayout, QMessageBox, QApplication)
from PyQt6.QtCore import QThread, pyqtSignal

# 导入自定义模块
import Data01_config
import Data01_file_utils
import Data01_tushare_utils


class DownloadWorker(QThread):
#    """
#    下载工作线程，避免阻塞GUI。
#    发射信号更新进度。
#    """
    progress = pyqtSignal(int, int, float)  # 当前序号，总数，已用秒数
    log = pyqtSignal(str)                   # 日志消息
    finished = pyqtSignal(int, float)        # 成功下载数量，总用时秒数

    def __init__(self, stock_list_df, save_dir):
        super().__init__()
        self.stock_list = stock_list_df
        self.save_dir = save_dir
        self.pro = None

    def run(self):
        start_time = time.time()
        # 初始化tushare
        token = Data01_config.TUSHARE_TOKEN
        self.pro = Data01_tushare_utils.init_tushare(token)

        total = len(self.stock_list)
        success_count = 0

        for idx, row in self.stock_list.iterrows():
            current = idx + 1
            # 更新进度
            elapsed = time.time() - start_time
            self.progress.emit(current, total, elapsed)

            stock_code = row['stock_code']
            start_date = row['start_date']
            end_date = row['end_date']
            data_type = row['data_type']

            # 确定文件名
            if data_type == '日数据':
                suffix = 'day'
                log_file = Data01_config.LOG_DAY_FILE
            else:  # 分钟数据
                suffix = 'min'
                log_file = Data01_config.LOG_MIN_FILE

            filename = f"{stock_code}_{suffix}.csv"
            filepath = os.path.join(self.save_dir, filename)

            # 下载数据
            self.log.emit(f"正在下载 ({current}/{total}): {stock_code}")
            df = Data01_tushare_utils.download_stock_data(self.pro, stock_code,
                                                    start_date, end_date, data_type)
            if df is not None:
                Data01_tushare_utils.save_data_to_csv(df, filepath)
                # 更新日志文件
                Data01_file_utils.update_log_file(log_file, stock_code,
                                           start_date, end_date, data_type)
                success_count += 1
            else:
                self.log.emit(f"下载失败: {stock_code}")

            # 可添加短暂延时避免请求频率过高
            time.sleep(0.5)

        total_time = time.time() - start_time
        self.finished.emit(success_count, total_time)


class Form1(QWidget):
#    """
#    主窗体，负责选择股票清单、下载数据、打开form2
#    """
    def __init__(self):
        super().__init__()
        self.stock_list_df = None  # 存储加载的股票清单
        self.save_dir = Data01_config.STOCK_DATA_DIR
        self.init_ui()
        self.check_and_prepare_directory()

    def init_ui(self):
        self.setWindowTitle("股票数据下载工具 - Form1")
        self.setGeometry(300, 300, 600, 400)

        # 标签和按钮
        self.label_info = QLabel("请选择股票清单文件")
        self.btn_select = QPushButton("选择股票清单")
        self.btn_select.clicked.connect(self.select_stock_list)

        self.label_count = QLabel("股票数量: 0")
        self.btn_download = QPushButton("下载数据")
        self.btn_download.setEnabled(True)  # 初始就可用
        self.btn_download.clicked.connect(self.start_download)

        self.label_status = QLabel("就绪")
        self.btn_to_form2 = QPushButton("更新到SQL数据库")
        self.btn_to_form2.clicked.connect(self.open_form2)
        self.btn_to_form2.setEnabled(True)  # 下载完成前就启用

        # 布局
        vbox = QVBoxLayout()
        vbox.addWidget(self.label_info)
        vbox.addWidget(self.btn_select)
        vbox.addWidget(self.label_count)
        vbox.addWidget(self.btn_download)
        vbox.addWidget(self.label_status)
        vbox.addWidget(self.btn_to_form2)
        self.setLayout(vbox)

        # 下载工作线程
        self.worker = None

    def check_and_prepare_directory(self):
        """检查并准备下载目录：创建目录，删除历史csv文件"""
        Data01_file_utils.ensure_dir(self.save_dir)
        Data01_file_utils.clear_csv_files(self.save_dir)
        self.label_status.setText("已清理历史CSV文件")

    def select_stock_list(self):
        """选择股票清单文件（支持 .csv 和 .xlsx），加载并显示数量"""
        # 文件过滤器同时包含 Excel 和 CSV
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择股票清单文件",
            "",
            "Excel文件 (*.xlsx);;CSV文件 (*.csv);;所有文件 (*)"
        )
        if not file_path:
            return

        try:
            # 调用 file_utils 读取文件，返回带标准列名的 DataFrame
            df = Data01_file_utils.read_stock_list(file_path)
            self.stock_list_df = df
            count = len(df)
            self.label_count.setText(f"股票数量: {count}")
            self.btn_download.setEnabled(True)
            self.label_info.setText(f"已加载: {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取股票清单文件失败：{str(e)}")

    def start_download(self):
        """开始下载，禁用按钮，启动工作线程"""
        if self.stock_list_df is None or self.stock_list_df.empty:
            QMessageBox.warning(self, "警告", "请先选择有效的股票清单")
            return

        # 再次确认目录已清理（可能用户手动添加了文件）
        Data01_file_utils.clear_csv_files(self.save_dir)

        self.btn_download.setEnabled(True)
        self.btn_select.setEnabled(True)
        self.btn_to_form2.setEnabled(True)

        self.worker = DownloadWorker(self.stock_list_df, self.save_dir)
        self.worker.progress.connect(self.update_progress)
        self.worker.log.connect(self.update_status)
        self.worker.finished.connect(self.download_finished)
        self.worker.start()

    def update_progress(self, current, total, elapsed_seconds):
        """更新进度显示，包括预计剩余时间"""
        elapsed_str = str(timedelta(seconds=int(elapsed_seconds)))
        if current > 0:
            avg_time_per = elapsed_seconds / current
            remaining = avg_time_per * (total - current)
            remaining_str = str(timedelta(seconds=int(remaining)))
            self.label_status.setText(
                f"正在下载第 {current} 只 (共 {total} 只)，"
                f"已用 {elapsed_str}，预计剩余 {remaining_str}"
            )
        else:
            self.label_status.setText(f"已用 {elapsed_str}")

    def update_status(self, message):
        """更新状态栏消息（可用于日志）"""
        # 这里简单打印到控制台，可根据需要改为显示在界面
        print(message)

    def download_finished(self, success_count, total_seconds):
        """下载完成处理"""
        total_time_str = str(timedelta(seconds=int(total_seconds)))
        self.label_status.setText(f"下载完成：成功 {success_count} 只，总用时 {total_time_str}")
        self.btn_download.setEnabled(True)   # 可再次下载
        self.btn_select.setEnabled(True)
        self.btn_to_form2.setEnabled(True)
        QMessageBox.information(self, "完成", f"数据下载完成！成功下载 {success_count} 只股票。")

    def open_form2(self):
        """打开Form2（数据更新到SQL）"""
        # 延迟导入，避免循环依赖
        from Data01_gui_form2 import Form2
        self.form2 = Form2()
        self.form2.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form1 = Form1()
    form1.show()
    sys.exit(app.exec())