import os
import sys
from PyQt6.QtWidgets import (QVBoxLayout, QWidget, QLineEdit, 
                             QPushButton, QLabel, QHBoxLayout, QFrame, 
                             QTabWidget, QFormLayout, QTimeEdit, QMessageBox)
from PyQt6.QtCore import Qt, QTime, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from database.db_handler import get_app_settings, save_app_settings, generate_recovery_token
from ui.styles import STYLE_SHEET

class AdminSettingsView(QWidget):
    back_clicked = pyqtSignal()
    settings_saved = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setStyleSheet(STYLE_SHEET + " AdminSettingsView { background-color: #F0F4F8; }")
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(25)
        
        # --- HEADER ---
        header_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("⬅ BACK")
        self.back_btn.setFixedSize(100, 45)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF; color: #1E293B; border: 1px solid #E2E8F0; border-radius: 8px; font-weight: bold;
            }
            QPushButton:hover { background-color: #F8FAFF; }
        """)
        self.back_btn.clicked.connect(self.back_clicked.emit)
        
        title_label = QLabel("🛡️ System Administration & Settings")
        title_label.setStyleSheet("color: #1E293B; font-size: 24px; font-weight: 800; font-family: 'Segoe UI';")
        
        header_layout.addWidget(self.back_btn)
        header_layout.addSpacing(20)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        self.main_layout.addLayout(header_layout)
        
        # --- TABS CONTAINER ---
        content_frame = QFrame()
        content_frame.setObjectName("MainContainer")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E2E8F0; background: #FFFFFF; border-radius: 8px; }
            QTabBar::tab { background: #F0F4F8; color: #64748B; padding: 12px 24px; border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: bold; font-size: 13px; }
            QTabBar::tab:selected { background: #FFFFFF; color: #1B4D89; border: 1px solid #E2E8F0; border-bottom: none; }
        """)
        
        self.setup_general_tab()
        self.setup_security_tab()
        self.setup_whatsapp_tab()
        
        content_layout.addWidget(self.tabs)
        self.main_layout.addWidget(content_frame)
        
        # --- FOOTER BUTTONS ---
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        self.save_btn = QPushButton("💾 APPLY CHANGES & REFRESH SYSTEM")
        self.save_btn.setFixedSize(320, 55)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1B4D89; color: white; border-radius: 10px; font-weight: 700; font-size: 14px;
            }
            QPushButton:hover { background-color: #153A68; }
        """)
        self.save_btn.clicked.connect(self.save_all_settings)
        
        footer_layout.addWidget(self.save_btn)
        self.main_layout.addLayout(footer_layout)
        
        self.load_current_settings()

    def setup_general_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: #FFFFFF;")
        layout = QFormLayout(tab)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(25)
        
        self.shop_name = QLineEdit()
        self.shop_address = QLineEdit()
        
        input_style = "background-color: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; font-size: 13px; color: #1E293B;"
        for field in [self.shop_name, self.shop_address]:
            field.setStyleSheet(input_style)
            
        layout.addRow(self.create_label("Shop Title Display:"), self.shop_name)
        layout.addRow(self.create_label("Business Address:"), self.shop_address)
        self.tabs.addTab(tab, "General Info")

    def setup_security_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: #FFFFFF;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(35)
        
        token_frame = QFrame()
        token_frame.setStyleSheet("background-color: #F8FAFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px;")
        token_layout = QVBoxLayout(token_frame)
        
        token_title = QLabel("🔑 MASTER RECOVERY TOKEN")
        token_title.setStyleSheet("font-weight: bold; color: #1E293B; font-size: 16px; border: none; background: transparent;")
        
        desc = QLabel("Keep this token safe. It is required for account recovery if security questions are disabled.")
        desc.setStyleSheet("color: #64748B; font-size: 12px; border: none; background: transparent;")
        
        token_h = QHBoxLayout()
        self.token_display = QLineEdit()
        self.token_display.setPlaceholderText("No Token Generated")
        self.token_display.setReadOnly(True)
        self.token_display.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                background-color: #FFFFFF;
                border: 2px dashed #1B4D89;
                border-radius: 8px;
                font-weight: bold;
                font-size: 18px;
                color: #1E293B;
                letter-spacing: 2px;
            }
        """)
        
        self.gen_btn = QPushButton("GENERATE NEW KEY")
        self.gen_btn.setFixedSize(180, 52)
        self.gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gen_btn.setStyleSheet("""
            QPushButton {
                background-color: #1B4D89; color: white; border-radius: 8px; font-weight: 700; font-size: 12px; border: none;
            }
            QPushButton:hover { background-color: #153A68; }
        """)
        self.gen_btn.clicked.connect(self.generate_new_key)
        
        token_h.addWidget(self.token_display)
        token_h.addWidget(self.gen_btn)
        
        token_layout.addWidget(token_title)
        token_layout.addWidget(desc)
        token_layout.addLayout(token_h)
        
        layout.addWidget(token_frame)
        
        # Passwords section
        pass_form = QFormLayout()
        pass_form.setSpacing(20)
        
        self.cur_pass = QLineEdit()
        self.new_pass = QLineEdit()
        
        input_style = "background-color: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; font-size: 13px; color: #1E293B;"
        for f in [self.cur_pass, self.new_pass]:
            f.setEchoMode(QLineEdit.EchoMode.Password)
            f.setStyleSheet(input_style)
            
        pass_form.addRow(self.create_label("Current Admin Password:"), self.cur_pass)
        pass_form.addRow(self.create_label("New Master Password:"), self.new_pass)
        
        layout.addLayout(pass_form)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Security & Recovery")

    def setup_whatsapp_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: #FFFFFF;")
        layout = QFormLayout(tab)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(25)
        
        input_style = "background-color: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; font-size: 13px; color: #1E293B;"
        combo_style = "background-color: white; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; font-size: 13px; color: #1E293B; QTimeEdit::up-button { width: 0px; height: 0px; border: none; } QTimeEdit::down-button { width: 0px; height: 0px; border: none; }"
        
        self.wa_num = QLineEdit()
        self.wa_num.setPlaceholderText("+92 300 0000000")
        self.wa_num.setStyleSheet(input_style)
        
        self.report_time = QTimeEdit()
        self.report_time.setFixedHeight(50)
        self.report_time.setStyleSheet(combo_style)
        
        layout.addRow(self.create_label("Admin WhatsApp Number:"), self.wa_num)
        layout.addRow(self.create_label("Daily Auto-Report Time:"), self.report_time)
        self.tabs.addTab(tab, "WhatsApp Integration")

    def create_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight: bold; color: #1E293B; font-size: 14px; background: transparent;")
        return lbl

    def load_current_settings(self):
        s = get_app_settings()
        self.shop_name.setText(s.get("shop_name", ""))
        self.shop_address.setText(s.get("shop_address", ""))
        self.wa_num.setText(s.get("whatsapp_number", ""))
        self.token_display.setText(s.get("recovery_token", ""))
        
        t_str = s.get("report_time", "21:00")
        h, m = map(int, t_str.split(":"))
        self.report_time.setTime(QTime(h, m))

    def show_toast(self, message):
        toast = QLabel(message, self)
        toast.setStyleSheet("""
            background-color: #3B82F6;
            color: white;
            padding: 15px 30px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        """)
        toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toast.adjustSize()
        
        # Position at bottom-middle
        x = (self.width() - toast.width()) // 2
        y = self.height() - 150
        toast.move(x, y)
        toast.show()
        toast.raise_()
        
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, toast.deleteLater)

    def generate_new_key(self):
        new_token = generate_recovery_token()
        self.token_display.setText(new_token)

    def save_all_settings(self):
        # 1. Validation
        wa = self.wa_num.text().strip()
        if not wa.startswith("+92"):
            QMessageBox.warning(self, "Invalid WhatsApp", "WhatsApp number must start with +92 (e.g., +923000000000)")
            return
            
        if len(self.shop_name.text().strip()) < 3:
            QMessageBox.warning(self, "Invalid Shop Name", "Shop name must be at least 3 characters long.")
            return

        # 2. Collect Data
        s = {
            "shop_name": self.shop_name.text().strip(),
            "shop_address": self.shop_address.text().strip(),
            "whatsapp_number": wa,
            "recovery_token": self.token_display.text(),
            "report_time": self.report_time.time().toString("HH:mm")
        }
        
        # 3. Save JSON
        if save_app_settings(s):
            # 4. Success Notification (Premium Toast)
            self.show_toast("✅ Settings Saved Successfully!")
            
            # 5. Global UI Update
            self.settings_saved.emit()
        else:
            QMessageBox.critical(self, "Error ❌", "Failed to save settings.")

# Legacy support for main_window import if it expects QMainWindow
from PyQt6.QtWidgets import QMainWindow
class AdminSettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.view = AdminSettingsView()
        self.setCentralWidget(self.view)
        self.setWindowTitle("System Settings")
        self.showMaximized()
        self.view.back_clicked.connect(self.close)
