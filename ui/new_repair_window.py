import sys
import os
import qrcode
from io import BytesIO
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLineEdit, 
                             QPushButton, QLabel, QHBoxLayout, QFrame, 
                             QDateEdit, QGraphicsDropShadowEffect, QApplication, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPixmap, QImage, QPainter
from PyQt6.QtPrintSupport import QPrintPreviewDialog, QPrinter

# database folder se import karein
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_handler import (insert_repair, get_all_customer_names, 
                             get_last_repair_by_customer, search_repair_customers)

class NewRepairWindow(QMainWindow):
    repair_saved = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add New Repair Job")
        self.setFixedSize(600, 850)
        self.setStyleSheet("background-color: #f4f7f6;")
        
        # Main Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        
        # --- FORM CARD ---
        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
            }
        """)
        
        # Shadow Effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.card.setGraphicsEffect(shadow)
        
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(30, 30, 30, 30)
        self.card_layout.setSpacing(15)
        
        # Title
        title = QLabel("🛠️ Register New Repair")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1b4d89; margin-bottom: 10px;")
        self.card_layout.addWidget(title)
        
        # Styles for Inputs
        input_style = """
            QLineEdit, QDateEdit {
                padding: 12px;
                border: 2px solid #dfe6e9;
                border-radius: 10px;
                background-color: #fafbfc;
                font-size: 14px;
            }
            QLineEdit:focus, QDateEdit:focus {
                border: 2px solid #00a3af;
                background-color: white;
            }
        """
        
        # Inputs
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Customer Name")
        self.name_input.setStyleSheet(input_style)
        
        # Setup Custom Repair Search Popup
        self.search_popup = RepairSearchPopup(self)
        self.name_input.textChanged.connect(self.update_search_results)
        self.name_input.installEventFilter(self)
        
        self.article_input = QLineEdit()
        self.article_input.setPlaceholderText("Article Name (e.g. Samsung AC)")
        self.article_input.setStyleSheet(input_style)
        
        self.issue_input = QLineEdit()
        self.issue_input.setPlaceholderText("Describe the Issue")
        self.issue_input.setStyleSheet(input_style)
        
        self.cost_input = QLineEdit()
        self.cost_input.setPlaceholderText("Estimated Cost (REAL)")
        self.cost_input.setStyleSheet(input_style)
        
        date_label = QLabel("Expected Completion Date:")
        date_label.setStyleSheet("color: #636e72; font-weight: bold; font-size: 12px;")
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate().addDays(3))
        self.date_input.setStyleSheet(input_style)
        
        self.card_layout.addWidget(self.name_input)
        self.card_layout.addWidget(self.article_input)
        self.card_layout.addWidget(self.issue_input)
        self.card_layout.addWidget(self.cost_input)
        self.card_layout.addWidget(date_label)
        self.card_layout.addWidget(self.date_input)
        
        # Save Button
        self.save_btn = QPushButton("Save Repair & Generate QR")
        self.save_btn.setFixedHeight(50)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1b4d89;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 10px;
                margin-top: 10px;
            }
            QPushButton:hover { background-color: #00a3af; }
        """)
        self.save_btn.clicked.connect(self.save_repair)
        self.card_layout.addWidget(self.save_btn)
        
        # --- QR CODE AREA ---
        self.qr_frame = QFrame()
        self.qr_frame.setFixedHeight(220)
        self.qr_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 10px; border: 1px dashed #b2bec3;")
        qr_layout = QVBoxLayout(self.qr_frame)
        
        self.qr_label = QLabel("QR Code Preview")
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setStyleSheet("color: #b2bec3; font-style: italic;")
        qr_layout.addWidget(self.qr_label)
        
        self.card_layout.addWidget(self.qr_frame)
        
        # Print Button
        self.print_btn = QPushButton("🖨️ Print Ticket")
        self.print_btn.setFixedHeight(45)
        self.print_btn.setEnabled(False) # Initially disabled
        self.print_btn.setStyleSheet("""
            QPushButton {
                background-color: #00b894;
                color: white;
                font-weight: bold;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #009e7f; }
            QPushButton:disabled { background-color: #b2bec3; }
        """)
        self.print_btn.clicked.connect(self.open_print_preview)
        self.card_layout.addWidget(self.print_btn)
        
        self.main_layout.addWidget(self.card)
        self.main_layout.addStretch()
        
        # To store the QR pixmap for printing
        self.generated_qr_pixmap = None

    def eventFilter(self, obj, event):
        if obj == self.name_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Down:
                if self.search_popup.isVisible():
                    self.search_popup.move_selection(1)
                    return True
            elif event.key() == Qt.Key.Key_Up:
                if self.search_popup.isVisible():
                    self.search_popup.move_selection(-1)
                    return True
            elif event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
                if self.search_popup.isVisible():
                    self.search_popup.select_current()
                    return True
        return super().eventFilter(obj, event)

    def update_search_results(self, text):
        if not text:
            self.search_popup.hide()
            return
            
        results = search_repair_customers(text)
        if results:
            self.search_popup.update_results(results)
            # Position below name_input
            pos = self.name_input.mapToGlobal(self.name_input.rect().bottomLeft())
            self.search_popup.setGeometry(pos.x(), pos.y() + 5, self.name_input.width(), 200)
            self.search_popup.show()
        else:
            self.search_popup.hide()

    def select_customer_from_popup(self, customer_row):
        # customer_row: (customer_name, item_name, last_visit_date)
        name = customer_row[0]
        self.name_input.setText(name)
        self.search_popup.hide()
        self.handle_customer_selection(name)

    def handle_customer_selection(self, name):
        """Pre-fill fields if customer has historical records."""
        history = get_last_repair_by_customer(name)
        if history:
            # history: (item_name, Issue, estimated_cost)
            self.article_input.setText(history[0])
            self.issue_input.setText(history[1])
            self.cost_input.setText(str(history[2]))
            # Visual feedback
            self.article_input.setStyleSheet(self.article_input.styleSheet() + "border-color: #00b894;")
            self.issue_input.setStyleSheet(self.issue_input.styleSheet() + "border-color: #00b894;")

    def save_repair(self):
        name = self.name_input.text()
        article = self.article_input.text()
        issue = self.issue_input.text()
        cost = self.cost_input.text()
        date_str = self.date_input.date().toString("yyyy-MM-dd")
        
        if not name or not article or not cost:
            QMessageBox.warning(self, "Invalid Input", "Please fill Name, Article and Cost fields.")
            return
            
        try:
            # Database mein save karein aur ID lein
            job_id = insert_repair(name, article, issue, float(cost), date_str, "Pending")
            
            # QR Code Generate Karein (Including Job ID for Billing Scan)
            qr_data = f"JOB_ID:{job_id}|CUSTOMER:{name}|ARTICLE:{article}|COST:{cost}"
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Convert PIL image to QPixmap
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            qimage = QImage.fromData(buffer.getvalue())
            self.generated_qr_pixmap = QPixmap.fromImage(qimage)
            
            # Display QR
            self.qr_label.setPixmap(self.generated_qr_pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))
            self.qr_label.setStyleSheet("border: none;")
            
            # Enable Print
            self.print_btn.setEnabled(True)
            
            QMessageBox.information(self, "Success", "Repair Job Saved and QR Generated!")
            self.repair_saved.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save: {str(e)}")

    def open_print_preview(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(self.handle_print)
        preview.exec()

    def handle_print(self, printer):
        painter = QPainter(printer)
        
        # Sample Printing Content
        painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        painter.drawText(100, 100, "REPAIR JOB TICKET")
        
        painter.setFont(QFont("Arial", 12))
        painter.drawText(100, 150, f"Customer: {self.name_input.text()}")
        painter.drawText(100, 180, f"Article: {self.article_input.text()}")
        painter.drawText(100, 210, f"Est. Cost: {self.cost_input.text()}")
        
        if self.generated_qr_pixmap:
            painter.drawPixmap(100, 250, self.generated_qr_pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio))
            
        painter.end()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

class RepairSearchPopup(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.main_window = parent
        self.results = []
        
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #1b4d89;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Customer Name", "Item Name", "Last Visit"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                background-color: white;
                font-size: 13px;
            }
            QTableWidget::item:selected {
                background-color: #1b4d89;
                color: white;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                font-weight: bold;
                border-bottom: 1px solid #dfe6e9;
            }
        """)
        
        layout.addWidget(self.table)
        self.table.itemDoubleClicked.connect(self.select_current)

    def update_results(self, results):
        self.results = results
        self.table.setRowCount(0)
        for row, r in enumerate(results):
            # r: (customer_name, item_name, exp_date)
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r[0]))
            self.table.setItem(row, 1, QTableWidgetItem(r[1]))
            self.table.setItem(row, 2, QTableWidgetItem(str(r[2])))
            
            for i in range(3):
                self.table.item(row, i).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if results:
            self.table.selectRow(0)

    def move_selection(self, delta):
        curr = self.table.currentRow()
        new_row = max(0, min(self.table.rowCount() - 1, curr + delta))
        self.table.selectRow(new_row)

    def select_current(self):
        idx = self.table.currentRow()
        if idx >= 0:
            customer_row = self.results[idx]
            self.main_window.select_customer_from_popup(customer_row)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NewRepairWindow()
    window.show()
    sys.exit(app.exec())
