import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                             QLabel, QFrame, QApplication, QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

# database folder se import karein
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_handler import get_notifications, get_low_stock_products

class NotificationPopup(QWidget):
    # Signals to communicate with MainWindow
    open_products = pyqtSignal()
    open_repairs = pyqtSignal()
    open_stock_item = pyqtSignal(int)
    
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
            try:
                low_stock_map = {row[1]: row[0] for row in get_low_stock_products()}
            except:
                low_stock_map = {}
                
            for alert in alerts:
                item = QListWidgetItem()
                self.list_widget.addItem(item)
                
                widget = QWidget()
                h_layout = QHBoxLayout(widget)
                h_layout.setContentsMargins(10, 5, 10, 5)
                
                if "Low Stock" in alert:
                    icon = "📦"
                    color = "#d63031" # Red
                else:
                    icon = "🛠️"
                    color = "#0984e3" # Blue
                    
                lbl = QLabel(f"{icon} {alert}")
                lbl.setStyleSheet(f"color: {color}; font-family: 'Segoe UI'; font-size: 13px; font-weight: bold;")
                h_layout.addWidget(lbl)
                
                if "Low Stock" in alert:
                    btn = QPushButton("View →")
                    btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #3A8DFF;
                            color: white;
                            border-radius: 10px;
                            padding: 4px 12px;
                            font-size: 12px;
                            font-weight: bold;
                            border: none;
                        }
                        QPushButton:hover { background-color: #245fa8; }
                    """)
                    try:
                        name_part = alert.split("Low Stock: ")[1].rsplit(" (", 1)[0]
                        p_id = low_stock_map.get(name_part)
                        if p_id is not None:
                            btn.clicked.connect(lambda checked, pid=p_id: self._on_view_clicked(pid))
                        else:
                            btn.hide()
                    except:
                        btn.hide()
                        
                    h_layout.addStretch()
                    h_layout.addWidget(btn)
                    
                item.setSizeHint(widget.sizeHint())
                self.list_widget.setItemWidget(item, widget)

    def _on_view_clicked(self, pid):
        self.open_stock_item.emit(pid)
        self.close()

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
