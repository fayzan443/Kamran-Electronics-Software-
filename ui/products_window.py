import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_handler import connect_db
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QStyledItemDelegate, QStyle, QLineEdit, QHBoxLayout, QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class RowHoverDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hovered_row = -1

    def paint(self, painter, option, index):
        if index.row() == self.hovered_row and not (option.state & QStyle.StateFlag.State_Selected):
            painter.fillRect(option.rect, QColor("#dfe6e9")) # Metal light grey
        super().paint(painter, option, index)

class ProductsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Product Stock List")
        self.setGeometry(150, 150, 1000, 600)
        
        # Professional CSS Styling
        self.setStyleSheet("""
            QMainWindow {
                
            }
            QWidget#MainContainer {
                
                border-radius: 12px;
            }
            QTableWidget {
                border: 1px solid #dfe6e9;
                
                font-family: 'Segoe UI';
                font-size: 14px;
                color: #2d3436;
                gridline-color: #f1f2f6;
                border-radius: 8px;
                outline: none;
            }
            QTableWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f1f2f6;
            }
            QTableWidget::item:selected {
                background-color: #10B981;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #dfe6e9;
                color: #2d3436;
            }
            QHeaderView::section {
                background-color: #3B82F6;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 13px;
                color: white;
                text-align: center;
            }
            QLineEdit#SearchBar {
                padding: 12px;
                border: 2px solid #dfe6e9;
                border-radius: 10px;
                
                font-size: 14px;
                color: #2d3436;
                margin-bottom: 10px;
            }
            QLineEdit#SearchBar:focus {
                border: 2px solid #00a3af;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.container = QWidget()
        self.container.setObjectName("MainContainer")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        
        # --- Search Bar Area ---
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("SearchBar")
        self.search_bar.setPlaceholderText("🔍 Search Product Name or Category...")
        self.search_bar.textChanged.connect(self.load_data)
        container_layout.addWidget(self.search_bar)
        
        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Category", "Pur. Price", "Sell Price", "Stock", "Min Limit"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setShowGrid(False)
        
        # Row Hover Support
        self.delegate = RowHoverDelegate(self.table)
        self.table.setItemDelegate(self.delegate)
        self.table.setMouseTracking(True)
        self.table.cellEntered.connect(self.handle_hover)
        
        container_layout.addWidget(self.table)
        layout.addWidget(self.container)
        
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        self.load_data()

    def handle_hover(self, row, column):
        self.delegate.hovered_row = row
        self.table.viewport().update()

    def load_data(self):
        query = self.search_bar.text()
        try:
            conn = connect_db()
            cursor = conn.cursor()
            
            if query:
                cursor.execute('SELECT Product_ID, Name, Category, Purchase_Price, Selling_Price, Stock_Qty, Min_Limit FROM Products WHERE (Name LIKE %s OR Category LIKE %s) AND Shop_ID = %s', (f'%{query}%', f'%{query}%', __import__('database.db_handler', fromlist=['CURRENT_SHOP_ID']).CURRENT_SHOP_ID))
            else:
                cursor.execute('SELECT Product_ID, Name, Category, Purchase_Price, Selling_Price, Stock_Qty, Min_Limit FROM Products WHERE Shop_ID = %s', (__import__('database.db_handler', fromlist=['CURRENT_SHOP_ID']).CURRENT_SHOP_ID,))
                
            rows = cursor.fetchall()
            conn.close()
            
            self.table.setRowCount(0)
            for row_data in rows:
                row = self.table.rowCount()
                self.table.insertRow(row)
                for i, data in enumerate(row_data):
                    item = QTableWidgetItem(str(data))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row, i, item)
        except Exception:
            pass