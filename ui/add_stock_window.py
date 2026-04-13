import sys
import os
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLineEdit, 
                             QPushButton, QLabel, QHBoxLayout, QFrame, 
                             QGraphicsDropShadowEffect, QApplication, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPixmap, QImage, QPainter
from PyQt6.QtPrintSupport import QPrintPreviewDialog, QPrinter

# database folder se import karein
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_handler import add_product

class AddStockWindow(QMainWindow):
    stock_added = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add New Stock")
        self.setFixedSize(600, 850)
        self.setStyleSheet("")
        
        # Main Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        
        # --- FORM CARD ---
        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame {
                
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
        title = QLabel("📦 Add New Product Stock")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #60A5FA; margin-bottom: 10px;")
        self.card_layout.addWidget(title)
        
        # Styles for Inputs
        input_style = """
            QLineEdit {
                padding: 12px;
                border: 2px solid #dfe6e9;
                border-radius: 10px;
                
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #00a3af;
                
            }
        """
        
        # Inputs
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product Name (e.g. AC Remote, Washing Machine Motor, LED Bulb)")
        self.name_input.setStyleSheet(input_style)
        
        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Company Name (e.g. Samsung, Orient, Haier, PEL)")
        self.category_input.setStyleSheet(input_style)
        
        self.p_price_input = QLineEdit()
        self.p_price_input.setPlaceholderText("Purchase Price")
        self.p_price_input.setStyleSheet(input_style)
        
        self.s_price_input = QLineEdit()
        self.s_price_input.setPlaceholderText("Selling Price")
        self.s_price_input.setStyleSheet(input_style)
        
        self.qty_input = QLineEdit()
        self.qty_input.setPlaceholderText("Initial Stock Quantity")
        self.qty_input.setStyleSheet(input_style)
        
        self.min_limit_input = QLineEdit()
        self.min_limit_input.setPlaceholderText("Min Warning Limit")
        self.min_limit_input.setStyleSheet(input_style)
        
        self.card_layout.addWidget(self.name_input)
        self.card_layout.addWidget(self.category_input)
        self.card_layout.addWidget(self.p_price_input)
        self.card_layout.addWidget(self.s_price_input)
        self.card_layout.addWidget(self.qty_input)
        self.card_layout.addWidget(self.min_limit_input)
        
        # Save Button
        self.save_btn = QPushButton("Save Product & Generate Barcode")
        self.save_btn.setFixedHeight(50)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 10px;
                margin-top: 10px;
            }
            QPushButton:hover { background-color: #10B981; }
        """)
        self.save_btn.clicked.connect(self.save_product)
        self.card_layout.addWidget(self.save_btn)
        
        # --- BARCODE AREA ---
        self.barcode_frame = QFrame()
        self.barcode_frame.setFixedHeight(180)
        self.barcode_frame.setStyleSheet(" border-radius: 10px; border: 1px dashed #b2bec3;")
        barcode_layout = QVBoxLayout(self.barcode_frame)
        
        self.barcode_label = QLabel("Barcode Preview")
        self.barcode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.barcode_label.setStyleSheet("color: #b2bec3; font-style: italic;")
        barcode_layout.addWidget(self.barcode_label)
        
        self.card_layout.addWidget(self.barcode_frame)
        
        # Print Button
        self.print_btn = QPushButton("🖨️ Print Barcode")
        self.print_btn.setFixedHeight(45)
        self.print_btn.setEnabled(False)
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
        
        # To store the barcode pixmap for printing
        self.generated_barcode_pixmap = None

    def save_product(self):
        name = self.name_input.text()
        category = self.category_input.text()
        p_price = self.p_price_input.text()
        s_price = self.s_price_input.text()
        qty = self.qty_input.text()
        min_limit = self.min_limit_input.text()
        
        if not all([name, category, p_price, s_price, qty, min_limit]):
            QMessageBox.warning(self, "Invalid Input", "Please fill all fields.")
            return
            
        try:
            # Type Conversion
            p_price = float(p_price)
            s_price = float(s_price)
            qty = int(qty)
            min_limit = int(min_limit)
            
            # Database mein save karein aur ID lein
            product_id = add_product(name, category, p_price, s_price, qty, min_limit)
            
            # Barcode Content (ID, Name, Cat, SellPrice)
            # Use Code128 for alphanumeric support
            barcode_data = f"{product_id}|{name[:8]}|{category[:5]}|{s_price}"
            # Standard barcodes have character limits, truncating name/cat for fit
            
            # Generate Barcode
            CODE128 = barcode.get_barcode_class('code128')
            writer = ImageWriter()
            # Disable text in barcode to keep it clean, we'll draw text in print if needed
            my_barcode = CODE128(barcode_data, writer=writer)
            
            buffer = BytesIO()
            my_barcode.write(buffer, options={"module_height": 15, "module_width": 0.4, "font_size": 10, "text_distance": 5})
            
            qimage = QImage.fromData(buffer.getvalue())
            self.generated_barcode_pixmap = QPixmap.fromImage(qimage)
            
            # Display Barcode
            self.barcode_label.setPixmap(self.generated_barcode_pixmap.scaled(self.barcode_frame.width()-40, 140, Qt.AspectRatioMode.KeepAspectRatio))
            self.barcode_label.setStyleSheet("border: none;  padding: 10px;")
            
            # Enable Print
            self.print_btn.setEnabled(True)
            
            # Signal emit karein taake list update ho jaye
            self.stock_added.emit()
            
            QMessageBox.information(self, "Success", f"Product '{name}' added successfully! Barcode generated.")
            
        except ValueError:
            QMessageBox.warning(self, "Type Error", "Price and Quantity must be numbers.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save: {str(e)}")

    def open_print_preview(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(self.handle_print)
        preview.exec()

    def handle_print(self, printer):
        painter = QPainter(printer)
        
        # Professional Label Layout
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(50, 50, f"PRODUCT: {self.name_input.text().upper()}")
        
        painter.setFont(QFont("Arial", 10))
        painter.drawText(50, 80, f"COMPANY NAME: {self.category_input.text()}")
        painter.drawText(300, 80, f"PRICE: Rs. {self.s_price_input.text()}")
        
        if self.generated_barcode_pixmap:
            # Standard barcode label size
            painter.drawPixmap(50, 100, self.generated_barcode_pixmap.scaled(500, 200, Qt.AspectRatioMode.KeepAspectRatio))
            
        painter.end()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AddStockWindow()
    window.show()
    sys.exit(app.exec())
