import sys
import ctypes
from PyQt6.QtCore import Qt, QProcess, QDateTime
from PyQt6.QtGui import QPainter, QColor, QBrush, QPainterPath, QFont
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QTextEdit, QHBoxLayout
)


class UFoff(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("UFoff")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(480, 400)

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(15, 15, 15, 15)
        mainLayout.setSpacing(10)

        # Header
        headerLayout = QHBoxLayout()
        titleLabel = QLabel("UFoff")
        titleLabel.setFont(QFont("微软雅黑", 18, QFont.Weight.Bold))
        titleLabel.setStyleSheet("color: #0078d7")

        subtitleLabel = QLabel("by 霄叁川")
        subtitleLabel.setFont(QFont("微软雅黑", 10))
        subtitleLabel.setStyleSheet("color: gray")

        headerText = QVBoxLayout()
        headerText.addWidget(titleLabel)
        headerText.addWidget(subtitleLabel)
        headerLayout.addLayout(headerText)
        headerLayout.addStretch()

        closeButton = QPushButton("✕")
        closeButton.setFixedSize(30, 30)
        closeButton.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                font-size: 14px;
                color: #d9534f;
                border: none;
                margin: 4px;
            }
            QPushButton:hover {
                color: #c9302c;
            }
        """)

        closeButton.clicked.connect(self.close)
        # 新增一层包装布局，来放置 closeButton 在右上角
        headerContainer = QVBoxLayout()
        headerContainer.setSpacing(0)
        headerContainer.setContentsMargins(0, 0, 0, 0)

        topRightLayout = QHBoxLayout()
        topRightLayout.setContentsMargins(0, 0, 0, 0)
        topRightLayout.addStretch()
        topRightLayout.addWidget(closeButton)

        headerContainer.addLayout(topRightLayout)
        headerContainer.addLayout(headerLayout)

        mainLayout.addLayout(headerContainer)

        # Buttons
        self.loopbackButton = self.createButton("解除UWP回环", self.removeLoopback)
        self.firewallButton = self.createButton("关闭防火墙", self.disableFirewall)
        self.checkButton = self.createButton("检查当前状态", self.checkStatus)
        mainLayout.addWidget(self.loopbackButton)
        mainLayout.addWidget(self.firewallButton)
        mainLayout.addWidget(self.checkButton)

        # Log
        self.logBox = QTextEdit()
        self.logBox.setReadOnly(True)
        self.logBox.setStyleSheet("background-color: #f4f4f4; border: 1px solid #ccc; border-radius: 8px; padding: 6px")
        mainLayout.addWidget(self.logBox)

        # Admin label
        self.adminLabel = QLabel("")
        self.adminLabel.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.adminLabel.setFont(QFont("微软雅黑", 9))
        self.adminLabel.setStyleSheet("color: #666")
        mainLayout.addWidget(self.adminLabel)

        self.setLayout(mainLayout)
        self.checkAdmin()

    def createButton(self, text, slot):
        button = QPushButton(text)
        button.setFont(QFont("微软雅黑", 12))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(slot)
        button.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        return button

    def paintEvent(self, event):
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillPath(path, QBrush(QColor(255, 255, 255)))
        painter.drawPath(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def log(self, message):
        time = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.logBox.append(f"[{time}] {message}")

    def checkAdmin(self):
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        self.adminLabel.setText("🔒 管理员权限: " + ("是" if is_admin else "否"))

    def removeLoopback(self):
        self.log("▶️ 正在解除 UWP 回环限制，请稍等...")
        process = QProcess(self)
        cmd = 'Get-AppxPackage | ForEach-Object { CheckNetIsolation LoopbackExempt -a -n="$($_.PackageFamilyName)" }'
        process.start("powershell", ["-Command", cmd])
        process.finished.connect(lambda: self.log("✅ UWP解除成功喵"))

    def disableFirewall(self):
        self.log("▶️ 正在关闭防火墙（使用 PowerShell）...")
        process = QProcess(self)
        cmd = 'Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False'
        process.start("powershell", ["-Command", cmd])
        process.finished.connect(lambda: self.log("✅ 防火墙关闭成功喵"))

    def checkStatus(self):
        self.log("🔍 正在检查状态，请稍等...")

        # ------- 检查 UWP 回环限制 -------
        uwp_process = QProcess(self)
        uwp_process.setProgram("powershell")
        uwp_process.setArguments(["-Command", "CheckNetIsolation LoopbackExempt -s"])

        def checkFirewall():
            # ------- 检查防火墙状态 -------
            fw_process = QProcess(self)
            fw_process.setProgram("powershell")
            fw_process.setArguments([
                "-Command", "Get-NetFirewallProfile | Select-Object -ExpandProperty Enabled"
            ])

            def handleFirewallFinished():
                fw_output = bytes(fw_process.readAllStandardOutput()).decode("utf-8", errors="ignore").strip()
                fw_error = bytes(fw_process.readAllStandardError()).decode("utf-8", errors="ignore").strip()

                if fw_error:
                    self.log("❌ 检查防火墙状态时出错:\n" + fw_error)
                    return

                false_count = fw_output.lower().count("false")
                if false_count == 3:
                    self.log("✅ 防火墙状态：已关闭")
                elif false_count == 0:
                    self.log("❌ 防火墙状态：全部开启")
                else:
                    self.log(f"⚠️ 防火墙状态：部分开启（{3 - false_count}/3）")

            fw_process.finished.connect(handleFirewallFinished)
            fw_process.start()

        def handleUwpFinished():
            output = bytes(uwp_process.readAllStandardOutput()).decode("utf-8", errors="ignore")
            if "microsoft." in output.lower():
                self.log("✅ UWP 回环限制：已解除")
            else:
                self.log("⚠️ UWP 回环限制：未解除")

            # 检查完回环限制再继续检查防火墙
            checkFirewall()

        uwp_process.finished.connect(handleUwpFinished)
        uwp_process.start()




if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = UFoff()
    window.show()
    sys.exit(app.exec())
