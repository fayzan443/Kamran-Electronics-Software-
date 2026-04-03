import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                             QLabel, QFrame, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

# database folder se import karein
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_handler import get_notifications

class NotificationPopup(QWidget):
    # Signals to communicate with MainWindow
    open_products = pyqtSignal()
    open_repairs = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Popup Window Settings
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(380, 480)
        
        self.setStyleSheet("""
            QWidget#PopupContainer {
                background-color: #fdfdfd;
                border: 1px solid #dfe6e9;
                border-radius: 15px;
            }
        """)
        
        self.container = QFrame(self)
        self.container.setObjectName("PopupContainer")
        self.container.setFixedSize(self.size())
        
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # --- HEADER ---
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            background-color: #f1f2f6;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
            border-bottom: 3px solid #00a3af;
        """)
        header_layout = QVBoxLayout(header)
        title = QLabel("🔔 SYSTEM ALERTS")
        title.setStyleSheet("font-weight: bold; color: #2d3436; font-size: 14px; letter-spacing: 1px;")
        header_layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(header)
        
        # --- LIST WIDGET ---
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
                padding: 5px;
            }
            QListWidget::item {
                padding: 18px;
                border-radius: 10px;
                margin: 4px 8px;
                font-family: 'Segoe UI';
                font-size: 13px;
                background-color: white;
                border: 1px solid #f1f2f6;
            }
            QListWidget::item:hover {
                background-color: #f7f9fa;
                border: 1px solid #dfe6e9;
            }
            QListWidget::item:selected {
                background-color: #00a3af;
                color: white;
            }
        """)
        self.list_widget.itemClicked.connect(self.handle_click)
        self.main_layout.addWidget(self.list_widget)
        
        self.load_alerts()

    def load_alerts(self):
        self.list_widget.clear()
        alerts = get_notifications()
        
        if not alerts:
            item = QListWidgetItem("✅ No new alerts. All clear!")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_widget.addItem(item)
        else:
            for alert in alerts:
                if "Low Stock" in alert:
                    icon = "📦"
                    color = QColor("#d63031") # Red
                else:
                    icon = "🛠️"
                    color = QColor("#0984e3") # Blue
                    
                item = QListWidgetItem(f"{icon} {alert}")
                item.setForeground(color)
                # Font weight for alerts
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                self.list_widget.addItem(item)

    def handle_click(self, item):
        text = item.text()
        if "Low Stock" in text:
            self.open_products.emit()
            self.close()
        elif "Pending Repair" in text:
            self.open_repairs.emit()
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = NotificationPopup()
    win.show()
    sys.exit(app.exec())
