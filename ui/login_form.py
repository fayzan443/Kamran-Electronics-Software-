import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont, QIcon
from database.db_handler import check_admin_login

class LoginForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin Login")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Container with Shadow
        self.container = QFrame(self)
        self.container.setGeometry(10, 10, 380, 480)
        self.container.setObjectName("LoginFormContainer")
        self.container.setStyleSheet("""
            #LoginFormContainer {
                background-color: white;
                border-radius: 20px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.container.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Close Button
        close_btn = QPushButton("✕", self.container)
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                font-size: 18px;
                color: #636e72;
                border: none;
            }
            QPushButton:hover { color: #ff4757; }
        """)
        close_btn.clicked.connect(self.reject)
        close_btn.move(340, 10)
        
        # Title
        title_lbl = QLabel("Admin Login")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("font-size: 28px; font-weight: bold; color: #1b4d89; margin-bottom: 10px;")
        layout.addWidget(title_lbl)
        
        # Subtitle
        sub_lbl = QLabel("Please enter your credentials")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet("font-size: 14px; color: #636e72;")
        layout.addWidget(sub_lbl)
        
        layout.addStretch()
        
        # Username
        user_layout = QVBoxLayout()
        user_layout.setSpacing(8)
        user_lbl = QLabel("Username")
        user_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1b4d89;")
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Enter username")
        self.user_input.setFixedHeight(45)
        self.user_input.setStyleSheet("""
            QLineEdit {
                background-color: #f1f2f6;
                border: 2px solid #f1f2f6;
                border-radius: 8px;
                padding-left: 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #00a3af;
                background-color: white;
            }
        """)
        user_layout.addWidget(user_lbl)
        user_layout.addWidget(self.user_input)
        self.user_input.returnPressed.connect(self.handle_login)
        layout.addLayout(user_layout)
        
        # Password
        pwd_layout = QVBoxLayout()
        pwd_layout.setSpacing(8)
        pwd_lbl = QLabel("Password")
        pwd_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1b4d89;")
        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("Enter password")
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd_input.setFixedHeight(45)
        self.pwd_input.setStyleSheet("""
            QLineEdit {
                background-color: #f1f2f6;
                border: 2px solid #f1f2f6;
                border-radius: 8px;
                padding-left: 15px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #00a3af;
                background-color: white;
            }
        """)
        pwd_layout.addWidget(pwd_lbl)
        pwd_layout.addWidget(self.pwd_input)
        self.pwd_input.returnPressed.connect(self.handle_login)
        layout.addLayout(pwd_layout)
        
        layout.addSpacing(10)
        
        # Login Button
        self.login_btn = QPushButton("LOGIN")
        self.login_btn.setFixedHeight(50)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #1b4d89;
                color: white;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #245fa8; }
            QPushButton:pressed { background-color: #1b4d89; }
        """)
        self.login_btn.clicked.connect(self.handle_login)
        layout.addWidget(self.login_btn)
        
        layout.addStretch()
        
    def handle_login(self):
        username = self.user_input.text()
        password = self.pwd_input.text()
        
        if check_admin_login(username, password):
            self.accept()
        else:
            QMessageBox.warning(self, "Invalid Credentials", "The username or password you entered is incorrect.")
            self.pwd_input.clear()
            self.pwd_input.setFocus()

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = LoginForm()
    win.show()
    sys.exit(app.exec())
