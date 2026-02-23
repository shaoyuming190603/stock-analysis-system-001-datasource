# """
# 程序启动入口：创建 QApplication 并显示窗体1。
# """

import sys
from PyQt6.QtWidgets import QApplication
from Data01_gui_form1 import Form1   # 注意：该模块也需要适配 PyQt6

def main():
    app = QApplication(sys.argv)
    form1 = Form1()
    form1.show()
    sys.exit(app.exec())       # exec_() → exec()

if __name__ == '__main__':
    main()