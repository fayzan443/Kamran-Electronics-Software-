import json
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QFormLayout)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db_config.json")

class DBSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Configuration")
        self.setFixedSize(350, 200)
        self.setStyleSheet("""
            QDialog {  font-family: 'Segoe UI'; }
            QLineEdit { padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
            QPushButton { background-color: #3B82F6; color: white; padding: 10px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #10B981; }
        """)
        
        layout = QVBoxLayout(self)
        
        lbl = QLabel("Please configure your MySQL connection:")
        lbl.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(lbl)
        
        form = QFormLayout()
        
        self.user_input = QLineEdit()
        self.user_input.setText("root")
        
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        form.addRow("Username:", self.user_input)
        form.addRow("Password:", self.pwd_input)
        
        layout.addLayout(form)
        
        self.save_btn = QPushButton("Save & Connect")
        self.save_btn.clicked.connect(self.save_config)
        layout.addWidget(self.save_btn)
        
    def save_config(self):
        config = {
            "host": "localhost",
            "user": self.user_input.text(),
            "password": self.pwd_input.text()
        }
        
        # Test connection before saving
        try:
            import mysql.connector
            conn = mysql.connector.connect(**config)
            conn.close()
            
            # If successful, save and accept
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f)
            self.accept()
            
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Connection Failed", 
                                f"Could not connect to MySQL:\n{err}\n\nPlease check your credentials.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

def get_db_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"host": "localhost", "user": "root", "password": ""}
