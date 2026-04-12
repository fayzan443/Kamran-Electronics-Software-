import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_handler import connect_db, update_repair_status, get_all_repairs
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLineEdit, QInputDialog, QDialog, QFormLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QComboBox, QHBoxLayout, QHeaderView, QLabel, QApplication, QStyledItemDelegate, QStyle, QMessageBox, QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from utils.shared import RowHoverDelegate

class StatusUpdateDialog(QDialog):
    def __init__(self, repair_id, current_status, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Update Repair ID: {repair_id}")
        self.setFixedSize(350, 200)
        self.setStyleSheet("""
            QDialog {  font-family: 'Segoe UI'; }
            QLineEdit, QComboBox { padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
            QPushButton { background-color: #3B82F6; color: white; padding: 10px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #10B981; }
        """)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.status_dropdown = QComboBox()
        self.status_dropdown.addItems(["Pending", "Completed"])
        self.status_dropdown.setCurrentText(current_status)
        
        self.cost_input = QLineEdit()
        self.cost_input.setPlaceholderText("Final Price (Customer)")
        
        self.spent_input = QLineEdit()
        self.spent_input.setPlaceholderText("Actual Repair Cost (Spending)")
        
        form.addRow("New Status:", self.status_dropdown)
        form.addRow("Final Price:", self.cost_input)
        form.addRow("Spent Cost:", self.spent_input)
        
        layout.addLayout(form)
        
        self.update_btn = QPushButton("Update Status")
        self.update_btn.clicked.connect(self.validate_and_accept)
        layout.addWidget(self.update_btn)
        
    def validate_and_accept(self):
        status = self.status_dropdown.currentText()
        cost = self.cost_input.text().strip()
        spent = self.spent_input.text().strip()
        
        if status == "Completed":
            try:
                val_cost = float(cost) if cost else 0
                val_spent = float(spent) if spent else 0
                if val_cost <= 0 or val_spent <= 0:
                    QMessageBox.warning(self, "Validation Error", "Costs are mandatory for completion")
                    return
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Costs are mandatory for completion")
                return
        
        self.accept()

    def get_values(self):
        return (self.status_dropdown.currentText(), 
                self.cost_input.text().strip(), 
                self.spent_input.text().strip())

class RepairsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Repair Jobs Filter")
        self.setGeometry(200, 200, 1000, 650)
        
        # Professional CSS Styling
        self.setStyleSheet("""
            QMainWindow {
                
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #dfe6e9;
                border-radius: 8px;
                
                font-size: 14px;
                color: #2d3436;
            }
            QLineEdit:focus {
                border: 2px solid #00a3af;
            }
            QComboBox {
                padding: 10px;
                border: 2px solid #dfe6e9;
                border-radius: 8px;
                
                min-width: 150px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 2px solid #00a3af;
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
            QHeaderView::section {
                background-color: #3B82F6;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 13px;
                color: white;
                text-align: center;
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
        """)
        
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Search & Filter Area
        filter_container = QWidget()
        filter_layout = QHBoxLayout(filter_container)
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(15)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search Customer Name or Article...")
        self.search_input.textChanged.connect(self.apply_filter)
        
        self.filter_box = QComboBox()
        self.filter_box.addItems(["All Status", "Pending", "Completed"])
        self.filter_box.currentIndexChanged.connect(self.apply_filter)
        
        filter_layout.addWidget(self.search_input, 4)
        filter_layout.addWidget(self.filter_box, 1)
        main_layout.addWidget(filter_container)

        # Table Area
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["ID", "Customer Name", "Article", "Issue Description", "Est. Cost", "Final Cost", "Exp. Date", "Status"])
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
        self.table.itemDoubleClicked.connect(self.on_cell_double_clicked)
        
        main_layout.addWidget(self.table)
        
        self.setCentralWidget(main_widget)
        self.load_repairs()

    def handle_hover(self, row, column):
        self.delegate.hovered_row = row
        self.table.viewport().update()
        
    def on_cell_double_clicked(self, item):
        row = item.row()
        repair_id_item = self.table.item(row, 0)
        if not repair_id_item: return
        repair_id = repair_id_item.text()
        current_status = self.table.item(row, 7).text()
        self.on_update_status(repair_id, current_status, row)

    def on_update_status(self, repair_id, current_status, row_index):
        dialog = StatusUpdateDialog(repair_id, current_status, self)
        if dialog.exec():
            new_status, cost_str, spent_str = dialog.get_values()
            final_cost = float(cost_str) if cost_str else None
            spent_cost = float(spent_str) if spent_str else None
            
            try:
                update_repair_status(repair_id, new_status, final_cost, spent_cost)
                QMessageBox.information(self, "Success", f"Repair {repair_id} updated to {new_status}!")
                # Refresh data instead of removing row, as per instructions
                self.load_repairs()
            except Exception as e:
                QMessageBox.critical(self, "Update Failed", str(e))

    def apply_filter(self):
        status_text = self.filter_box.currentText()
        if status_text == "All Status":
            status_text = "All"
        self.load_repairs(self.search_input.text(), status_text)

    def load_repairs(self, query="", status="All"):
        try:
            rows = get_all_repairs(query, status)
            
            self.table.setRowCount(0)
            for row_data in rows:
                row = self.table.rowCount()
                self.table.insertRow(row)
                for i, data in enumerate(row_data):
                    item = QTableWidgetItem(str(data))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    # Status coloring logic can be added here if needed
                    self.table.setItem(row, i, item)
        except Exception:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = RepairsWindow()
    win.show()
    sys.exit(app.exec())