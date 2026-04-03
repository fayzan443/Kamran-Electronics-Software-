from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QFrame, QLineEdit, QComboBox, QMessageBox, QDateEdit, QGridLayout)
from PyQt6.QtCore import Qt, QDate
from database.db_handler import get_all_staff, add_staff

class StaffView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(30)
        
        # --- Top Section: Staff List ---
        top_card = QFrame()
        top_card.setObjectName("MainContainer")
        top_layout = QVBoxLayout(top_card)
        top_layout.setContentsMargins(25, 25, 25, 25)
        
        title_lbl = QLabel("👥 Current Staff Record")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #1E293B;")
        top_layout.addWidget(title_lbl)
        
        self.staff_table = QTableWidget()
        self.staff_table.setColumnCount(6)
        self.staff_table.setHorizontalHeaderLabels(["Employee ID", "Name", "Role", "Join Date", "Phone Number", "Assigned Port/Counter"])
        self.staff_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.staff_table.verticalHeader().setVisible(False)
        self.staff_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        top_layout.addWidget(self.staff_table)
        
        main_layout.addWidget(top_card, 2)
        
        # --- Bottom Section: Add Staff Form ---
        bottom_card = QFrame()
        bottom_card.setObjectName("MainContainer")
        bot_layout = QVBoxLayout(bottom_card)
        bot_layout.setContentsMargins(25, 25, 25, 25)
        
        form_title = QLabel("➕ Add New Worker")
        form_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B; margin-bottom: 10px;")
        bot_layout.addWidget(form_title)
        
        form_grid = QGridLayout()
        form_grid.setSpacing(15)
        
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Full Name")
        
        self.inp_role = QComboBox()
        self.inp_role.addItems(["Salesman", "Manager", "Cleaner", "Technician", "Other"])
        
        self.inp_phone = QLineEdit()
        self.inp_phone.setPlaceholderText("Phone Number")
        
        self.inp_port = QLineEdit()
        self.inp_port.setPlaceholderText("e.g. Counter 1, Front Desk, Back Office")
        
        self.inp_date = QDateEdit()
        self.inp_date.setCalendarPopup(True)
        self.inp_date.setDate(QDate.currentDate())
        self.inp_date.setDisplayFormat("yyyy-MM-dd")
        self.inp_date.setStyleSheet("padding: 12px; border: 1px solid #D1D9E6; border-radius: 22px; background-color: #E6E9EE;")
        
        form_grid.addWidget(QLabel("Name:"), 0, 0)
        form_grid.addWidget(self.inp_name, 0, 1)
        
        form_grid.addWidget(QLabel("Role:"), 0, 2)
        form_grid.addWidget(self.inp_role, 0, 3)
        
        form_grid.addWidget(QLabel("Join Date:"), 1, 0)
        form_grid.addWidget(self.inp_date, 1, 1)
        
        form_grid.addWidget(QLabel("Phone:"), 1, 2)
        form_grid.addWidget(self.inp_phone, 1, 3)
        
        form_grid.addWidget(QLabel("Assigned Port/Counter:"), 2, 0)
        form_grid.addWidget(self.inp_port, 2, 1, 1, 3)
        
        bot_layout.addLayout(form_grid)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_add = QPushButton("Add Worker")
        self.btn_add.setFixedSize(180, 45)
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border-radius: 22px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        self.btn_add.clicked.connect(self.save_staff)
        btn_layout.addWidget(self.btn_add)
        
        bot_layout.addLayout(btn_layout)
        
        main_layout.addWidget(bottom_card, 1)
        
        self.refresh_table()

    def refresh_table(self):
        self.staff_table.setRowCount(0)
        records = get_all_staff()
        for row_data in records:
            row_idx = self.staff_table.rowCount()
            self.staff_table.insertRow(row_idx)
            
            for col_idx, item in enumerate(row_data):
                self.staff_table.setItem(row_idx, col_idx, QTableWidgetItem(str(item) if item is not None else ""))

    def save_staff(self):
        name = self.inp_name.text().strip()
        role = self.inp_role.currentText()
        date = self.inp_date.date().toString("yyyy-MM-dd")
        phone = self.inp_phone.text().strip()
        port = self.inp_port.text().strip()
        
        if not name or not phone:
            QMessageBox.warning(self, "Invalid Input", "Name and Phone Number are required fields.")
            return
            
        try:
            add_staff(name, role, date, phone, port)
            QMessageBox.information(self, "Success", "Worker added successfully.")
            self.inp_name.clear()
            self.inp_phone.clear()
            self.inp_port.clear()
            self.inp_date.setDate(QDate.currentDate())
            self.refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save staff record: {e}")
