import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLineEdit, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QLabel, QHBoxLayout, QHeaderView, QFrame, 
                             QGraphicsDropShadowEffect, QApplication, QMessageBox,
                             QDialog, QListWidget)
from PyQt6.QtCore import Qt, QDateTime, pyqtSignal, QTimer, QRect, QRectF, QThread
from PyQt6.QtGui import QColor, QFont, QPainter, QPageSize
from PyQt6.QtPrintSupport import QPrintPreviewDialog, QPrinter
try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False
from PyQt6.QtWidgets import QToolTip

# database folder se import karein
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_handler import (get_product_by_id, get_repair_by_id, save_bill, 
                             search_completed_repairs, search_products_advanced,
                             get_all_product_names, fetch_item_by_barcode)
from ui.styles import STYLE_SHEET

class SearchWorker(QThread):
    results_found = pyqtSignal(list, str) # results, search_context
    
    def __init__(self):
        super().__init__()
        self.query = ""
        self.context = ""
        
    def set_params(self, query, context):
        self.query = query
        self.context = context
        
    def run(self):
        if self.context == 'product':
            results = search_products_advanced(self.query)
        else:
            results = search_completed_repairs(self.query)
        self.results_found.emit(results, self.context)

class NewBillWindow(QMainWindow):
    bill_printed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Professional Billing System")
        self.setGeometry(100, 100, 900, 800)
        self.setStyleSheet(STYLE_SHEET)
        
        self.bill_items = [] # Store list of (desc, type, price)
        
        # Debounce setup for search
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_debounced_search)
        
        self.repair_search_timer = QTimer()
        self.repair_search_timer.setSingleShot(True)
        self.repair_search_timer.timeout.connect(self.perform_debounced_repair_search)
        
        # Async Search Worker
        self.search_worker = SearchWorker()
        self.search_worker.results_found.connect(self.handle_async_results)
        
        # Barcode Scanner State
        self.barcode_buffer = ""
        self.last_barcode_time = 0
        self.focus_timer = QTimer(self)
        self.focus_timer.setInterval(500) # Check focus every 500ms
        self.focus_timer.timeout.connect(self.ensure_focus)
        self.focus_timer.start()
        
        # Main Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)
        
        # --- HEADER SECTION ---
        header_frame = QFrame()
        header_frame.setObjectName("Navbar")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        title_label = QLabel("📝 POINT OF SALE")
        title_label.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        self.time_label = QLabel(QDateTime.currentDateTime().toString("dd MMM yyyy - hh:mm AP"))
        self.time_label.setStyleSheet("color: #00a3af; font-weight: bold; font-size: 14px;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.time_label)
        self.main_layout.addWidget(header_frame)
        
        # --- SCAN AREA ---
        scan_card = QFrame()
        scan_card.setObjectName("MainContainer")
        scan_layout = QVBoxLayout(scan_card)
        scan_layout.setContentsMargins(20, 20, 20, 20)
        
        scan_title = QLabel("🔍 SEARCH ITEM (NAME / CATEGORY / ID)")
        scan_title.setStyleSheet("font-weight: bold; color: #60A5FA; font-size: 13px;")
        
        scan_h_layout = QHBoxLayout()
        
        self.scan_input = QLineEdit()
        self.scan_input.setPlaceholderText("Enter Product Name, Company Name, or Scan Barcode...")
        
        # Setup Custom Search Popup
        self.search_popup = SearchPopup(self)
        self.scan_input.textChanged.connect(self.on_search)
        self.scan_input.installEventFilter(self) # For arrow keys
        
        self.scan_input.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                border: 2px solid #dfe6e9;
                border-radius: 10px;
                font-size: 16px;
                
            }
            QLineEdit:focus { border: 2px solid #00a3af;  }
        """)
        self.scan_input.returnPressed.connect(self.handle_search_and_add)
        
        # Quantity Input
        self.qty_input = QLineEdit()
        self.qty_input.setText("1")
        self.qty_input.setPlaceholderText("Qty")
        self.qty_input.setFixedWidth(100)
        self.qty_input.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                border: 2px solid #dfe6e9;
                border-radius: 10px;
                font-size: 16px;
                
                font-weight: bold;
                text-align: center;
            }
            QLineEdit:focus { border: 2px solid #00a3af;  }
        """)
        self.qty_input.returnPressed.connect(self.add_item_from_qty)
        
        # Add Button
        self.add_btn = QPushButton("➕ ADD")
        self.add_btn.setFixedSize(120, 52)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #245fa8; }
        """)
        self.add_btn.clicked.connect(self.handle_search_and_add)

        scan_h_layout.addWidget(self.scan_input, 4)
        scan_h_layout.addWidget(self.qty_input, 1)
        scan_h_layout.addWidget(self.add_btn)
        
        scan_layout.addWidget(scan_title)
        scan_layout.addLayout(scan_h_layout)
        
        # --- REPAIR SEARCH AREA ---
        repair_title = QLabel("SEARCH COMPLETED REPAIRS")
        repair_title.setStyleSheet("font-weight: bold; color: #636e72; font-size: 13px; margin-top: 10px;")
        
        self.repair_input = QLineEdit()
        self.repair_input.setPlaceholderText("Enter Customer Name... (Completed Repairs Only)")
        
        # Setup Repair Search Popup
        self.repair_popup = RepairSearchPopup(self)
        self.repair_input.textChanged.connect(self.debounce_repair_search)
        self.repair_input.installEventFilter(self) # Re-use same for arrow keys
        
        self.repair_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #dfe6e9;
                border-radius: 10px;
                font-size: 15px;
                
            }
            QLineEdit:focus { border: 1px solid #3B82F6;  }
        """)
        self.repair_input.returnPressed.connect(self.search_repairs)
        
        scan_layout.addWidget(repair_title)
        scan_layout.addWidget(self.repair_input)
        
        self.main_layout.addWidget(scan_card)
        
        # --- BILL TABLE ---
        table_card = QFrame()
        table_card.setObjectName("MainContainer")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(10, 10, 10, 10)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Item Description", "Item Type", "Price", "Qty"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setStyleSheet("")
        table_layout.addWidget(self.table)
        self.main_layout.addWidget(table_card)
        
        # --- TOTAL & ACTIONS ---
        bottom_layout = QHBoxLayout()
        
        self.total_label = QLabel("Total: Rs. 0.00")
        self.total_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #60A5FA;")
        
        self.print_btn = QPushButton("🖨️ PRINT BILL")
        self.print_btn.setFixedHeight(60)
        self.print_btn.setFixedWidth(250)
        self.print_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                font-weight: bold;
                font-size: 18px;
                border-radius: 12px;
            }
            QPushButton:hover { background-color: #00818d; }
        """)
        self.print_btn.clicked.connect(self.print_bill)
        
        bottom_layout.addWidget(self.total_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.print_btn)
        self.main_layout.addLayout(bottom_layout)
        
        # Customer Name Input for Bill
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Customer Name (Optional)")
        self.customer_input.setStyleSheet("padding: 10px; border-radius: 8px; border: 1px solid #dfe6e9;")
        bottom_layout.insertWidget(1, self.customer_input)

    def eventFilter(self, obj, event):
        if (obj == self.scan_input or obj == self.repair_input) and event.type() == event.Type.KeyPress:
            popup = self.search_popup if obj == self.scan_input else self.repair_popup
            
            if event.key() == Qt.Key.Key_Down:
                if popup.isVisible():
                    popup.move_selection(1)
                    return True
            elif event.key() == Qt.Key.Key_Up:
                if popup.isVisible():
                    popup.move_selection(-1)
                    return True
            elif event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
                if popup.isVisible():
                    popup.select_current()
                    return True
                else:
                    if obj == self.repair_input:
                        self.search_repairs()
                        return True
        return super().eventFilter(obj, event)

    def ensure_focus(self):
        """Focus Management: Redirects focus to scan_input if no other meaningful input is active."""
        focused = QApplication.focusWidget()
        if not focused or focused not in [self.scan_input, self.qty_input, self.customer_input, self.repair_input]:
            if self.isVisible() and self.isActiveWindow():
                self.scan_input.setFocus()

    def keyPressEvent(self, event):
        """Global Barcode Intercept: Detects rapid number entry ending with Enter."""
        now = QDateTime.currentMSecsSinceEpoch()
        text = event.text()

        # Detect if this is a potential rapid barcode entry
        if text.isdigit():
            # If delay between keys is < 50ms, it's likely a scanner
            if now - self.last_barcode_time < 50:
                self.barcode_buffer += text
            else:
                self.barcode_buffer = text
            self.last_barcode_time = now

        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # If we have a buffered sequence of numbers and it ends with Enter
            if len(self.barcode_buffer) >= 3: # Reasonable minimum for a barcode/ID
                self.handle_barcode_scan(self.barcode_buffer)
                self.barcode_buffer = ""
                event.accept()
                return

        super().keyPressEvent(event)

    def on_search(self, text):
        self.search_timer.start(300) # 300ms delay as requested

    def perform_debounced_search(self):
        text = self.scan_input.text().strip()
        if not text:
            self.search_popup.hide()
            return
        
        if self.search_worker.isRunning():
            self.search_worker.terminate() # Cancel ongoing
            self.search_worker.wait()
            
        self.search_worker.set_params(text, 'product')
        self.search_worker.start()

    def debounce_repair_search(self, text):
        self.repair_search_timer.start(300) # 300ms delay

    def perform_debounced_repair_search(self):
        text = self.repair_input.text().strip()
        if not text:
            self.repair_popup.hide()
            return
            
        if self.search_worker.isRunning():
            self.search_worker.terminate()
            self.search_worker.wait()
            
        self.search_worker.set_params(text, 'repair')
        self.search_worker.start()

    def handle_async_results(self, results, context):
        if context == 'product':
            if results:
                self.search_popup.update_results(results)
                pos = self.scan_input.mapToGlobal(self.scan_input.rect().bottomLeft())
                self.search_popup.setGeometry(pos.x(), pos.y() + 2, self.scan_input.width(), 300)
                self.search_popup.show()
                # Focus Lock: Ensure scan_input remains focused
                self.scan_input.setFocus()
            else:
                self.search_popup.hide()
        else:
            if results:
                self.repair_popup.update_results(results)
                pos = self.repair_input.mapToGlobal(self.repair_input.rect().bottomLeft())
                self.repair_popup.setGeometry(pos.x(), pos.y() + 2, self.repair_input.width(), 300)
                self.repair_popup.show()
                self.repair_input.setFocus()
            else:
                self.repair_popup.hide()


    def handle_search_and_add(self):
        """Intelligent search: Fetches product and moves focus to Qty field."""
        if self.search_popup.isVisible():
            self.search_popup.select_current()
            return
            
        query = self.scan_input.text().strip()
        if not query: return
        
        # Special Case: Repair Job ID
        if query.startswith("JOB_ID:"):
            self.perform_lookup(query, 1) # Auto add repair
            self.scan_input.clear()
            return

        # Perform Search
        results = search_products_advanced(query)
        if not results:
            QMessageBox.warning(self, "No Results", f"No products found matching '{query}'.")
            return
            
        if len(results) == 1:
            # Auto-save product to a temporary buffer and focus Qty
            self.pending_product = results[0]
            self.qty_input.setFocus()
            self.qty_input.selectAll()
        else:
            # Show selection dialog for multiple results
            self.show_selection_dialog(results)

    def select_product_from_popup(self, product):
        # product: (ID, Shop_ID, Barcode, Name, Cat, PPrice, SPrice, Qty, Limit)
        self.pending_product = product
        self.scan_input.setText(product[3]) # Show selected name
        self.search_popup.hide()
        
        # Move focus to Quantity, set default 1, and highlight
        self.qty_input.setText("1")
        self.qty_input.setFocus()
        self.qty_input.selectAll()

    def show_selection_dialog(self, results):
        dialog = ProductSelectionDialog(results, self)
        if dialog.exec():
            self.pending_product = dialog.selected_product
            if self.pending_product:
                self.qty_input.setFocus()
                self.qty_input.selectAll()

    def add_item_from_qty(self):
        """Finalize and add item to bill when Enter is pressed in Qty field."""
        if not hasattr(self, 'pending_product') or not self.pending_product:
            return
            
        try:
            qty = int(self.qty_input.text() or "1")
            if qty <= 0: qty = 1
        except:
            qty = 1
            
        p = self.pending_product
        self.add_item_to_table(p[3], "Product", float(p[6]), source_id=p[0], qty=qty)
        
        # Reset for next entry
        self.pending_product = None
        self.scan_input.clear()
        self.qty_input.setText("1")
        self.scan_input.setFocus()

    def handle_barcode_scan(self, barcode):
        """Auto-Add to Cart: Queries the DB and adds item instantly with Qty 1."""
        product = fetch_item_by_barcode(barcode)
        
        if product:
            # product format from DB: (ID, Shop_ID, Barcode, Name, Cat, PPrice, SPrice, Qty, Limit)
            # Update: SPrice is at index 6 now because we added Barcode column at index 2
            self.add_item_to_table(product[3], "Product", float(product[6]), source_id=product[0], qty=1)
            
            # Clear scan input and visual feedback
            self.scan_input.clear()
            self.barcode_buffer = "" 
        else:
            # Play Beep and show tooltip
            if WINSOUND_AVAILABLE:
                winsound.Beep(1000, 300)
            QToolTip.showText(self.scan_input.mapToGlobal(self.scan_input.rect().center()), 
                             "❌ Item Not Found!", self.scan_input, QRect(), 2000)
            self.scan_input.clear()
            self.barcode_buffer = ""

    def process_scan(self):
        """Manual 'ADD' click: respects the Qty input field."""
        data = self.scan_input.text().strip()
        try:
            qty = int(self.qty_input.text() or "1")
            if qty <= 0: qty = 1
        except:
            qty = 1

        self.scan_input.clear()
        self.qty_input.setText("1") # Reset for next scan
        
        if data:
            self.perform_lookup(data, qty)

    def perform_lookup(self, data, qty):
        """Unified lookup logic for both barcode scans and manual additions."""
        try:
            # 1. Check if it's a Repair QR (Starts with JOB_ID:)
            if data.startswith("JOB_ID:"):
                try:
                    job_id = int(data.split("|")[0].split(":")[1])
                    repair = get_repair_by_id(job_id)
                    if repair:
                        if repair[8] == 'Completed':
                            desc = f"Repair: {repair[3]} ({repair[2]})"
                            price = float(repair[6]) if repair[6] is not None else float(repair[5])
                            self.add_item_to_table(desc, "Repair", price, source_id=job_id, qty=qty)
                            return
                        else:
                            QMessageBox.warning(self, "Not Completed", f"Repair Job must be marked 'Completed'. Current status: {repair[8]}")
                            return
                except:
                    pass
            
            # 2. Check for standard Barcode format (id|name|cat|price)
            if "|" in data:
                try:
                    parts = data.split("|")
                    p_id = int(parts[0])
                    product = get_product_by_id(p_id)
                    if product:
                        self.add_item_to_table(product[3], "Product", float(product[6]), source_id=p_id, qty=qty)
                        return
                except:
                    pass
            
            # 3. Fallback: Search by numeric Product ID
            if data.isdigit():
                p_id = int(data)
                product = get_product_by_id(p_id)
                if product:
                    self.add_item_to_table(product[3], "Product", float(product[6]), source_id=p_id, qty=qty)
                else:
                    QMessageBox.warning(self, "Not Found", f"No product found with ID: {data}")
            else:
                QMessageBox.warning(self, "Scan Error", f"Unrecognized barcode or ID: {data}")
                
        except Exception as e:
            QMessageBox.critical(self, "System Error", f"Fatal error during lookup: {str(e)}")


    def select_repair_from_popup(self, repair):
        # repair: (id, customer_name, item_name, Issue, est_cost, final_cost)
        self.pending_repair = repair
        self.repair_input.setText(f"{repair[1]} - {repair[2]}")
        self.repair_popup.hide()
        
        # Add to table logic
        qty = 1 # Default
        desc = f"Repair: {repair[2]} ({repair[1]})"
        price = float(repair[5]) if repair[5] is not None else float(repair[4])
        self.add_item_to_table(desc, "Repair", price, source_id=repair[0], qty=qty)
        self.repair_input.clear()
        self.repair_input.setFocus()

    def search_repairs(self):
        if self.repair_popup.isVisible():
            self.repair_popup.select_current()
            return
        
        data = self.repair_input.text().strip()
        if not data: return
        
        try:
            results = search_completed_repairs(data)
            if results:
                self.select_repair_from_popup(results[0])
            else:
                QMessageBox.information(self, "No Results", f"No completed repairs found for '{data}'.")
        except Exception:
            self.repair_input.clear()

    def add_item_to_table(self, desc, i_type, price, source_id=None, qty=1):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(desc))
        self.table.setItem(row, 1, QTableWidgetItem(i_type))
        self.table.setItem(row, 2, QTableWidgetItem(f"{price:.2f}"))
        self.table.setItem(row, 3, QTableWidgetItem(str(qty)))
        
        # Center text
        for i in range(4):
            self.table.item(row, i).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
        # desc, type, price, qty, source_id
        self.bill_items.append([desc, i_type, price, qty, source_id])
        self.update_total()

    def update_total(self):
        total = sum(item[2] * item[3] for item in self.bill_items)
        self.total_label.setText(f"Total: Rs. {total:.2f}")

    def print_bill(self):
        if not self.bill_items:
            QMessageBox.warning(self, "Empty Bill", "Please add items before printing.")
            return
            
        try:
            name = self.customer_input.text() or "Walk-in Customer"
            total = sum(item[2] * item[3] for item in self.bill_items)
            
            # Open Print Preview
            printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
            preview = QPrintPreviewDialog(printer, self)
            preview.paintRequested.connect(self.generate_thermal_receipt)
            
            # Use DialogCode.Accepted (or 1) to check if print was clicked
            if preview.exec() == QPrintPreviewDialog.DialogCode.Accepted:
                save_bill(name, total, self.bill_items)
                self.table.setRowCount(0)
                self.bill_items = []
                self.customer_input.clear()
                self.update_total()
                
                # Emit signal to refresh main dashboard
                self.bill_printed.emit()
            
        except Exception as e:
            print(f"PRINT ERROR: {e}")

    def generate_thermal_receipt(self, printer):
        # 1. Page & Painter Setup
        printer.setFullPage(True)
        painter = QPainter(printer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 2. Scaling to MM for Consistent Layout
        scale_x = printer.logicalDpiX() / 25.4
        scale_y = printer.logicalDpiY() / 25.4
        painter.scale(scale_x, scale_y)
        
        # 3. Design Tokens
        y = 10 
        PAGE_WIDTH = 72 # Printable area for 80mm paper
        
        font_header = QFont('Arial', 12, QFont.Weight.Bold)
        font_subheader = QFont('Arial', 9)
        font_table_head = QFont('Courier', 9, QFont.Weight.Bold)
        font_body = QFont('Courier', 9)
        font_total = QFont('Arial', 11, QFont.Weight.Bold)
        font_footer = QFont('Arial', 8)
        
        # --- HEADER (Centered & Bold) ---
        painter.setFont(font_header)
        painter.drawText(QRectF(0, y, PAGE_WIDTH, 7), Qt.AlignmentFlag.AlignCenter, "KAMRAN & SOHAIL")
        y += 8
        painter.setFont(font_subheader)
        painter.drawText(QRectF(0, y, PAGE_WIDTH, 4), Qt.AlignmentFlag.AlignCenter, "ELECTRICAL & REPAIRING LAB")
        y += 4
        painter.drawText(QRectF(0, y, PAGE_WIDTH, 4), Qt.AlignmentFlag.AlignCenter, "Main St, Hub | Ph: 0300-1234567")
        y += 7
        
        # Separator Line
        painter.setFont(font_body)
        painter.drawText(QRectF(0, y, PAGE_WIDTH, 4), Qt.AlignmentFlag.AlignCenter, "--------------------------------")
        y += 6
        
        # --- TABLE HEADER (Item, Qty, Price, Total) ---
        painter.setFont(font_table_head)
        painter.drawText(QRectF(2, y, 32, 5), Qt.AlignmentFlag.AlignLeft, "ITEM")
        painter.drawText(QRectF(34, y, 8, 5), Qt.AlignmentFlag.AlignCenter, "QTY")
        painter.drawText(QRectF(42, y, 14, 5), Qt.AlignmentFlag.AlignRight, "PRICE")
        painter.drawText(QRectF(56, y, 14, 5), Qt.AlignmentFlag.AlignRight, "TOTAL")
        y += 5
        painter.drawText(QRectF(0, y, PAGE_WIDTH, 4), Qt.AlignmentFlag.AlignCenter, "--------------------------------")
        y += 6
        
        # --- ITEMS LOOP ---
        painter.setFont(font_body)
        total_amount = 0.0
        for item in self.bill_items:
            desc = str(item[0])[:16] # Truncate for spacing
            price = float(item[2])
            qty = int(item[3])
            line_total = price * qty
            total_amount += line_total
            
            painter.drawText(QRectF(2, y, 32, 5), Qt.AlignmentFlag.AlignLeft, desc)
            painter.drawText(QRectF(34, y, 8, 5), Qt.AlignmentFlag.AlignCenter, str(qty))
            painter.drawText(QRectF(42, y, 14, 5), Qt.AlignmentFlag.AlignRight, f"{price:,.0f}")
            painter.drawText(QRectF(56, y, 14, 5), Qt.AlignmentFlag.AlignRight, f"{line_total:,.0f}")
            y += 6 
            
        y += 2
        painter.drawText(QRectF(0, y, PAGE_WIDTH, 4), Qt.AlignmentFlag.AlignCenter, "--------------------------------")
        y += 6
        
        # --- SUMMARY ---
        painter.setFont(font_total)
        painter.drawText(QRectF(2, y, 40, 7), Qt.AlignmentFlag.AlignLeft, "GRAND TOTAL:")
        painter.drawText(QRectF(42, y, 28, 7), Qt.AlignmentFlag.AlignRight, f"Rs. {total_amount:,.0f}")
        y += 12
        
        # --- FOOTER ---
        painter.setFont(font_footer)
        painter.drawText(QRectF(0, y, PAGE_WIDTH, 4), Qt.AlignmentFlag.AlignCenter, "No Return without Receipt")
        y += 5
        painter.drawText(QRectF(0, y, PAGE_WIDTH, 4), Qt.AlignmentFlag.AlignCenter, "*** THANK YOU FOR YOUR VISIT ***")
        y += 5
        painter.setFont(QFont('Arial', 7, QFont.Weight.Bold))
        painter.drawText(QRectF(0, y, PAGE_WIDTH, 4), Qt.AlignmentFlag.AlignCenter, "Software by FANGS Devs")
        y += 20 # Paper Cutting Space (approx 4 empty lines)
        painter.drawText(QRectF(0, y, PAGE_WIDTH, 4), Qt.AlignmentFlag.AlignCenter, " ") # Draw a blank space to advance internal y
        
        painter.end()




class SearchPopup(QFrame):
    def __init__(self, parent=None):
        # Changed Popup to ToolTip to prevent focus grabbing
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_window = parent
        self.results = []
        
        # Premium Styling
        self.setStyleSheet("""
            QFrame {
                
                border: 1px solid #dfe6e9;
                border-radius: 12px;
            }
        """)
        
        # Shadow Effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(20)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(10)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(self.shadow)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Company Name", "Price", "Stock"])
        
        # Header Styling
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)          # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Category
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Price
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Stock
        
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus) # Don't take focus from main input
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                
                font-size: 14px;
                alternate-
                selection-background-color: #3B82F6;
                selection-color: white;
                border-radius: 8px;
            }
            QHeaderView::section {
                
                padding: 8px;
                font-weight: bold;
                border: none;
                color: #2d3436;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f3f5;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #dfe6e9;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #b2bec3;
            }
        """)
        layout.addWidget(self.table)
        self.table.itemClicked.connect(self.select_current)
        self.table.itemDoubleClicked.connect(self.select_current)

    def update_results(self, results):
        self.results = results
        self.table.setRowCount(0)
        # Block signals to prevent infinite selection loops
        self.table.blockSignals(True)
        for row, p in enumerate(results):
            # p: (ID, Shop_ID, Barcode, Name, Cat, PPrice, SPrice, Qty, Limit)
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(p[0])))
            self.table.setItem(row, 1, QTableWidgetItem(p[3]))
            self.table.setItem(row, 2, QTableWidgetItem(p[4]))
            self.table.setItem(row, 3, QTableWidgetItem(f"Rs. {p[6]:,.0f}"))
            self.table.setItem(row, 4, QTableWidgetItem(str(p[7])))
            
            for i in range(5):
                self.table.item(row, i).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # if results:
        #     self.table.selectRow(0)
        self.table.blockSignals(False)

    def move_selection(self, delta):
        curr = self.table.currentRow()
        new_row = max(0, min(self.table.rowCount() - 1, curr + delta))
        self.table.selectRow(new_row)
        # Scroll logic stays same
        item = self.table.item(new_row, 0)
        if item: self.table.scrollToItem(item)

    def select_current(self):
        # Triggered by Enter or Click
        idx = self.table.currentRow()
        if idx >= 0:
            product = self.results[idx]
            self.main_window.select_product_from_popup(product)

class RepairSearchPopup(QFrame):
    def __init__(self, parent=None):
        # Changed Popup to ToolTip to prevent focus grabbing
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.main_window = parent
        self.results = []
        
        self.setStyleSheet("""
            QFrame {  border: 1px solid #3B82F6; border-radius: 12px; }
        """)
        
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(20)
        self.shadow.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(self.shadow)
        
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Customer", "Item", "Final Cost"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget { border: none; font-size: 14px; }
            QHeaderView::section {  font-weight: bold; border: none; }
        """)
        
        layout.addWidget(self.table)
        self.table.itemClicked.connect(self.select_current)
        self.table.itemDoubleClicked.connect(self.select_current)

    def update_results(self, results):
        self.results = results
        self.table.setRowCount(0)
        for row, r in enumerate(results):
            # r: (id, customer_name, item_name, Issue, est_cost, final_cost)
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(r[0])))
            self.table.setItem(row, 1, QTableWidgetItem(r[1]))
            self.table.setItem(row, 2, QTableWidgetItem(r[2]))
            cost = r[5] if r[5] is not None else r[4]
            self.table.setItem(row, 3, QTableWidgetItem(f"Rs. {cost:,.0f}"))
            
            for i in range(4):
                self.table.item(row, i).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # if results:
        #     self.table.selectRow(0)

    def move_selection(self, delta):
        curr = self.table.currentRow()
        new_row = max(0, min(self.table.rowCount() - 1, curr + delta))
        self.table.selectRow(new_row)
        item = self.table.item(new_row, 0)
        if item: self.table.scrollToItem(item)

    def select_current(self):
        idx = self.table.currentRow()
        if idx >= 0:
            repair = self.results[idx]
            self.main_window.select_repair_from_popup(repair)

class ProductSelectionDialog(QDialog):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Product")
        self.setFixedSize(600, 400)
        self.selected_product = None
        
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        for p in items:
            item_text = f"ID: {p[0]} | {p[3]} | {p[4]} | Rs. {p[6]:,.0f}"
            self.list_widget.addItem(item_text)
            
        layout.addWidget(QLabel("Multiple matches found. Please select correct item:"))
        layout.addWidget(self.list_widget)
        self.list_widget.itemDoubleClicked.connect(self.accept_selection)
        self.items = items

    def accept_selection(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.selected_product = self.items[row]
            self.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = NewBillWindow()
    win.show()
    sys.exit(app.exec())
