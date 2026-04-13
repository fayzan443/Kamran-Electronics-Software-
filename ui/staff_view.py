from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QLineEdit, QTableWidget, 
                              QTableWidgetItem, QHeaderView, QFrame, 
                              QGraphicsDropShadowEffect, QMessageBox,
                              QGridLayout, QDialog, QComboBox, QDateEdit, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QColor, QFont, QDoubleValidator
from database.db_handler import (get_all_staff, get_staff_by_id, 
                                 add_salary_payment, add_advance_payment, settle_advance,
                                 add_staff, update_staff, get_staff_salary_history,
                                 get_last_salary_payment_date, get_salary_raise_history,
                                 add_salary_raise_record, update_staff_salary, check_salary_already_paid)
from datetime import datetime

class StaffView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # 1. Main Layout Setup
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(25, 25, 25, 25)
        self.main_layout.setSpacing(16)
        
        # Set Background Color
        self.setStyleSheet("background-color: #F0F4F8;")

        # 2. Top Stats Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        self.lbl_total_staff = QLabel("0")
        self.lbl_total_salary = QLabel("Rs. 0")
        self.lbl_last_salary = QLabel("Not paid yet")
        
        card1 = self.create_stat_card("Total Staff", self.lbl_total_staff, "👥", "#DBEAFE", "#3A8DFF")
        card2 = self.create_stat_card("Total Monthly Salary", self.lbl_total_salary, "💰", "#D1FAE5", "#10B981")
        card3 = self.create_stat_card("Last Salary Paid", self.lbl_last_salary, "📋", "#DBEAFE", "#3A8DFF")
        
        stats_layout.addWidget(card1, 1)
        stats_layout.addWidget(card2, 1)
        stats_layout.addWidget(card3, 1)
        self.main_layout.addLayout(stats_layout)

        # 3. Main Content Area (60/40 Split)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # --- LEFT COLUMN (Staff Table) ---
        left_column = QVBoxLayout()
        table_card = QFrame()
        table_card.setObjectName("tableCard")
        table_card.setStyleSheet("""
            QFrame#tableCard {
                background-color: white;
                border-radius: 16px;
            }
        """)
        self.add_shadow(table_card)
        
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(20, 20, 20, 20)
        table_layout.setSpacing(15)
        
        # Table Header Row
        title_row = QHBoxLayout()
        title_lbl = QLabel("👥 Staff Members")
        title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E293B;")
        
        pay_all_btn = QPushButton("💸 Pay All Staff")
        pay_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pay_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981; color: white; border-radius: 10px;
                padding: 8px 18px; font-size: 12px; font-weight: 700; border: none;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        pay_all_btn.clicked.connect(self.open_pay_all_dialog)
        
        add_btn = QPushButton("➕ Add Staff")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #1B4D89; color: white; border-radius: 10px;
                padding: 8px 18px; font-size: 12px; font-weight: 700;
            }
            QPushButton:hover { background-color: #153A68; }
        """)
        add_btn.clicked.connect(self.on_add_staff_clicked)
        
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        title_row.addWidget(pay_all_btn)
        title_row.addWidget(add_btn)
        table_layout.addLayout(title_row)
        
        # Search Field
        self.staff_search = QLineEdit()
        self.staff_search.setPlaceholderText("Search by name or role...")
        self.staff_search.setStyleSheet("""
            QLineEdit {
                background-color: #F8FAFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 13px;
                color: #1E293B;
            }
            QLineEdit:focus {
                border: 1px solid #3A8DFF;
            }
        """)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.load_staff_data)
        self.staff_search.textChanged.connect(lambda: self.search_timer.start(300))
        table_layout.addWidget(self.staff_search)
        
        # QTableWidget
        self.staff_table = QTableWidget()
        self.staff_table.setColumnCount(7)
        self.staff_table.setHorizontalHeaderLabels(["ID", "Name", "Role", "Phone", "Salary", "Advance", "Status"])
        self.staff_table.verticalHeader().setVisible(False)
        self.staff_table.setShowGrid(False)
        self.staff_table.setAlternatingRowColors(True)
        self.staff_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.staff_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.staff_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #FAFBFF;
                border: none;
            }
            QHeaderView::section {
                background-color: white;
                font-weight: bold;
                color: #1E293B;
                border: none;
                border-bottom: 2px solid #F0F2F5;
                padding: 12px;
            }
        """)
        self.staff_table.verticalHeader().setDefaultSectionSize(44)
        for i in range(7):
            self.staff_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        self.staff_table.itemClicked.connect(self.on_staff_row_clicked)
        table_layout.addWidget(self.staff_table)
        
        left_column.addWidget(table_card)
        content_layout.addLayout(left_column, 7)
        
        # --- RIGHT COLUMN (Staff Details) ---
        right_column = QVBoxLayout()
        self.detail_card = QFrame()
        self.detail_card.setObjectName("detailCard")
        self.detail_card.setStyleSheet("""
            QFrame#detailCard {
                background-color: white;
                border-radius: 16px;
            }
        """)
        self.add_shadow(self.detail_card)
        
        detail_layout = QVBoxLayout(self.detail_card)
        detail_layout.setContentsMargins(20, 20, 20, 20)
        detail_layout.setSpacing(15)
        
        self.detail_title_lbl = QLabel("👤 Staff Detail")
        self.detail_title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E293B;")
        detail_layout.addWidget(self.detail_title_lbl)
        
        self.detail_placeholder = QLabel("Select a staff member to view details")
        self.detail_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_placeholder.setStyleSheet("color: #94A3B8; font-size: 13px; margin-top: 50px;")
        detail_layout.addWidget(self.detail_placeholder)
        
        self.detail_area = QWidget()
        self.detail_area_layout = QVBoxLayout(self.detail_area)
        self.detail_area.hide()
        detail_layout.addWidget(self.detail_area)
        
        detail_layout.addStretch()
        right_column.addWidget(self.detail_card)
        content_layout.addLayout(right_column, 3)
        
        self.main_layout.addLayout(content_layout)
        
        # 4. Final Load
        self.load_staff_data()

    def create_stat_card(self, title, val_lbl, icon, icon_bg, accent):
        card = QFrame()
        card.setFixedHeight(85)
        # Apply specific left border and ensure no other borders are visible
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 16px;
                border-left: 4px solid {accent};
                border-top: none;
                border-right: none;
                border-bottom: none;
            }}
        """)
        self.add_shadow(card)
        
        main_layout = QVBoxLayout(card)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(4)
        
        # Top row: Title and Icon
        top_row = QHBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 600;")
        
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setFixedSize(32, 32)
        icon_lbl.setStyleSheet(f"background-color: {icon_bg}; border-radius: 16px; font-size: 14px;")
        
        top_row.addWidget(title_lbl)
        top_row.addStretch()
        top_row.addWidget(icon_lbl)
        main_layout.addLayout(top_row)
        
        # Bottom: Value label
        val_lbl_color = "#3A8DFF" if title == "Last Salary Paid" else "#1E293B"
        val_lbl.setStyleSheet(f"color: {val_lbl_color}; font-size: 22px; font-weight: 900;")
        main_layout.addWidget(val_lbl)
        
        return card

    def add_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 18))
        widget.setGraphicsEffect(shadow)

    def load_staff_data(self):
        search = self.staff_search.text().lower().strip()
        staff = get_all_staff()
        
        total_salary = 0
        total_advance = 0
        
        filtered = []
        for s in staff:
            # Index Mapping: 0:ID, 1:Name, 2:Role, 3:Date, 4:Phone, 5:Port, 6:Salary, 7:Advance, 8:Status
            name = str(s[1]).lower()
            role = str(s[2]).lower()
            status = str(s[8])
            salary = float(s[6] or 0)
            advance = float(s[7] or 0)
            
            if status == "Active":
                total_salary += salary
            total_advance += advance
            
            if not search or search in name or search in role:
                filtered.append(s)
        
        # Update Stats Cards
        self.lbl_total_staff.setText(str(len(staff)))
        self.lbl_total_salary.setText(f"Rs. {int(total_salary):,}")
        
        last_date = get_last_salary_payment_date()
        if last_date:
            if hasattr(last_date, 'strftime'):
                d_str = last_date.strftime("%d %b %Y")
            else:
                d_str = str(last_date)
            self.lbl_last_salary.setText(d_str)
        else:
            self.lbl_last_salary.setText("Not paid yet")
        
        # Populate Table
        self.staff_table.setRowCount(0)
        for i, s in enumerate(filtered):
            self.staff_table.insertRow(i)
            # Basic Columns
            id_item = QTableWidgetItem(str(s[0]))
            name_item = QTableWidgetItem(str(s[1]))
            role_item = QTableWidgetItem(str(s[2]))
            phone_item = QTableWidgetItem(str(s[4]))
            salary_item = QTableWidgetItem(f"Rs. {int(s[6] or 0):,}")
            advance_item = QTableWidgetItem(f"Rs. {int(s[7] or 0):,}")
            
            # Center alignments and styling
            for col, item in enumerate([id_item, name_item, role_item, phone_item, salary_item, advance_item]):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setForeground(QColor("#44474B"))
                item.setFont(QFont("Segoe UI", 10))
                self.staff_table.setItem(i, col, item)
            
            # Status Badge Column
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(4, 4, 4, 4)
            status_lbl = QLabel(f" ● {s[8]}")
            status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_lbl.setFixedHeight(24)
            
            if s[8] == "Active":
                status_lbl.setStyleSheet("background-color: #D1FAE5; color: #065F46; border-radius: 6px; font-weight: bold; font-size: 10px; padding: 0 8px;")
            elif s[8] == "On Leave":
                status_lbl.setStyleSheet("background-color: #FEF3C7; color: #92400E; border-radius: 6px; font-weight: bold; font-size: 10px; padding: 0 8px;")
            else: # Resigned
                status_lbl.setStyleSheet("background-color: #FEE2E2; color: #991B1B; border-radius: 6px; font-weight: bold; font-size: 10px; padding: 0 8px;")
            
            status_layout.addWidget(status_lbl)
            self.staff_table.setCellWidget(i, 6, status_widget)

    def on_add_staff_clicked(self):
        QMessageBox.information(self, "Add Staff", "Add Staff form coming in next step")

    def on_staff_row_clicked(self, item):
        row = item.row()
        id_val = self.staff_table.item(row, 0).text()
        
        full_data = get_staff_by_id(id_val)
        if not full_data:
            return
            
        # Employee_ID, Name, Role, Join_Date, Phone, Assigned_Port, Monthly_Salary, Advance_Amount, Status
        self.selected_staff = {
            "id": full_data[0],
            "name": full_data[1],
            "role": full_data[2],
            "join_date": full_data[3],
            "phone": full_data[4],
            "counter": full_data[5],
            "salary": float(full_data[6] or 0),
            "advance": float(full_data[7] or 0),
            "status": full_data[8]
        }
        self.show_staff_detail()

    def show_staff_detail(self):
        # 1. Clear existing Detail Area (All widgets and layouts)
        if hasattr(self, 'detail_area_layout'):
            while self.detail_area_layout.count():
                item = self.detail_area_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
                else:
                    layout = item.layout()
                    if layout:
                        while layout.count():
                            li = layout.takeAt(0)
                            w = li.widget()
                            if w:
                                w.setParent(None)
                                w.deleteLater()
                                
        self.detail_placeholder.hide()
        self.detail_area.show()
        
        staff = self.selected_staff
        if hasattr(self, 'detail_title_lbl'): self.detail_title_lbl.hide()
        
        # --- Section 1: Compact Profile ---
        profile_box = QWidget()
        profile_layout = QHBoxLayout(profile_box)
        profile_layout.setContentsMargins(0, 5, 0, 10)
        profile_layout.setSpacing(12)
        
        avatar = QLabel(staff['name'][0].upper() if staff['name'] else "?")
        avatar.setFixedSize(50, 50)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("background-color: #1B4D89; color: white; border-radius: 25px; font-size: 20px; font-weight: bold;")
        profile_layout.addWidget(avatar)
        
        txt_box = QVBoxLayout()
        txt_box.setSpacing(2)
        name_lbl = QLabel(staff['name'])
        name_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B;")
        txt_box.addWidget(name_lbl)
        
        badge_row = QHBoxLayout()
        badge_row.setSpacing(8)
        role_sm = QLabel(staff['role'])
        role_sm.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 600;")
        badge_row.addWidget(role_sm)
        
        status_txt = "Active" if staff['status'] == "Active" else staff['status']
        status_dot = QLabel(f" ● {status_txt}")
        if staff['status'] == "Active":
            status_dot.setStyleSheet("color: #059669; font-weight: bold; font-size: 10px;")
        else:
            status_dot.setStyleSheet("color: #DC2626; font-weight: bold; font-size: 10px;")
        badge_row.addWidget(status_dot)
        badge_row.addStretch()
        txt_box.addLayout(badge_row)
        
        profile_layout.addLayout(txt_box)
        self.detail_area_layout.addWidget(profile_box)
        
        def add_separator():
            line = QFrame()
            line.setFixedHeight(1)
            line.setStyleSheet("background-color: #E2E8F0;")
            self.detail_area_layout.addWidget(line)
        
        # --- Section 2: Basic Info ---
        add_separator()
        info_v = QVBoxLayout()
        info_v.setSpacing(6)
        info_v.setContentsMargins(0, 10, 0, 10)
        
        def add_info_mini(label, value):
            row = QHBoxLayout()
            l = QLabel(label)
            l.setStyleSheet("font-size: 10px; font-weight: bold; color: #94A3B8;")
            v = QLabel(str(value))
            v.setStyleSheet("font-size: 12px; color: #1E293B; font-weight: 500;")
            row.addWidget(l)
            row.addStretch()
            row.addWidget(v)
            info_v.addLayout(row)

        join_d = staff['join_date']
        if hasattr(join_d, 'strftime'): join_d = join_d.strftime("%d %b %Y")
        
        add_info_mini("PHONE", staff['phone'] or "-")
        add_info_mini("JOIN DATE", join_d)
        self.detail_area_layout.addLayout(info_v)
        
        # --- Section 3: Salary Info ---
        add_separator()
        sal_v = QVBoxLayout()
        sal_v.setSpacing(6)
        sal_v.setContentsMargins(0, 10, 0, 10)
        
        row1 = QHBoxLayout()
        l1 = QLabel("Monthly Salary")
        l1.setStyleSheet("font-size: 11px; color: #64748B;")
        v1 = QLabel(f"Rs. {int(staff['salary']):,}")
        v1.setStyleSheet("font-size: 14px; font-weight: bold; color: #10B981;")
        row1.addWidget(l1)
        row1.addStretch()
        row1.addWidget(v1)
        sal_v.addLayout(row1)
        
        history = get_staff_salary_history(staff['id'])
        last_text = "Not paid yet"
        if history:
            h_date = history[0][8]
            last_text = h_date.strftime("%d %b %Y") if hasattr(h_date, 'strftime') else str(h_date)
        
        row2 = QHBoxLayout()
        l2 = QLabel("Last Paid")
        l2.setStyleSheet("font-size: 11px; color: #64748B;")
        v2 = QLabel(last_text)
        v2.setStyleSheet("font-size: 12px; color: #1E293B; font-weight: 500;")
        row2.addWidget(l2)
        row2.addStretch()
        row2.addWidget(v2)
        sal_v.addLayout(row2)
        
        self.detail_area_layout.addLayout(sal_v)
        
        # --- Section 4: Action Buttons ---
        add_separator()
        btn_v = QVBoxLayout()
        btn_v.setSpacing(6)
        btn_v.setContentsMargins(0, 10, 0, 0)
        
        def create_action_btn(text, style, callback):
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            full_style = f"QPushButton {{ {style} border-radius: 10px; padding: 9px; font-weight: 700; font-size: 12px; }}"
            btn.setStyleSheet(full_style)
            btn.clicked.connect(callback)
            return btn

        pay_btn = create_action_btn("💰 Pay Salary", "background-color: #1B4D89; color: white; border: none;", self.open_pay_salary_dialog)
        edit_btn = create_action_btn("✏️ Edit Staff", "background-color: #F0F4F8; color: #1E293B; border: 1px solid #E2E8F0;", self.open_edit_dialog)
        hist_btn = create_action_btn("📋 Salary History", "background-color: #F0F4F8; color: #3A8DFF; border: 1px solid #3A8DFF;", 
                                     lambda: self.open_salary_history_dialog(staff['id'], staff['name']))
        
        btn_v.addWidget(pay_btn)
        btn_v.addWidget(edit_btn)
        btn_v.addWidget(hist_btn)
        self.detail_area_layout.addLayout(btn_v)
        
        self.detail_area_layout.addStretch()

    def open_pay_salary_dialog(self):
        staff = self.selected_staff
        dialog = QDialog(self)
        dialog.setWindowTitle(f"💰 Pay Salary — {staff['name']}")
        dialog.setFixedSize(400, 500)
        dialog.setStyleSheet("background-color: #F8FAFF;")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(14)
        
        # Header Card
        header = QFrame()
        header.setStyleSheet("background-color: #F0FDF4; border: 1px solid #DCFCE7; border-radius: 12px;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(14, 14, 14, 14)
        header_layout.setSpacing(8)
        
        def add_header_row(label, value, value_style):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 600;")
            val = QLabel(value)
            val.setStyleSheet(value_style)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            header_layout.addLayout(row)
            return val

        add_header_row("Monthly Salary", f"Rs. {int(staff['salary']):,}", "color: #10B981; font-size: 18px; font-weight: bold;")
        
        sep1 = QFrame()
        sep1.setFixedSize(header.width(), 1)
        sep1.setStyleSheet("background-color: #E2E8F0;")
        header_layout.addWidget(sep1)
        
        add_header_row("Current Advance", f"Rs. {int(staff['advance']):,}", "color: #EF4444; font-size: 13px; font-weight: bold;")

        sep2 = QFrame()
        sep2.setFixedSize(header.width(), 1)
        sep2.setStyleSheet("background-color: #E2E8F0;")
        header_layout.addWidget(sep2)
        
        net_receivable = int(staff['salary'] - staff['advance'])
        self.dlg_net_lbl = add_header_row("Net Payable", f"Rs. {max(0, net_receivable):,}", "color: #1B4D89; font-size: 15px; font-weight: bold;")
        
        layout.addWidget(header)
        
        # Form
        input_style = "background-color: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px; font-size: 13px;"
        label_style = "font-size: 12px; font-weight: bold; color: #1E293B;"
        
        # Month
        layout.addWidget(QLabel("Month"))
        layout.itemAt(layout.count()-1).widget().setStyleSheet(label_style)
        month_combo = QComboBox()
        months = ["January", "February", "March", "April", "May", "June", 
                  "July", "August", "September", "October", "November", "December"]
        month_combo.addItems(months)
        month_combo.setCurrentIndex(datetime.now().month - 1)
        month_combo.setStyleSheet(input_style)
        layout.addWidget(month_combo)
        
        # Year
        layout.addWidget(QLabel("Year"))
        layout.itemAt(layout.count()-1).widget().setStyleSheet(label_style)
        year_input = QLineEdit(str(datetime.now().year))
        year_input.setStyleSheet(input_style)
        layout.addWidget(year_input)
        
        # Advance to Deduct
        layout.addWidget(QLabel("Advance to Deduct (Rs.)"))
        layout.itemAt(layout.count()-1).widget().setStyleSheet(label_style)
        deduct_input = QLineEdit(str(int(staff['advance'])))
        deduct_input.setValidator(QDoubleValidator(0.0, 9999999.0, 2))
        deduct_input.setStyleSheet(input_style)
        layout.addWidget(deduct_input)
        
        # Notes
        layout.addWidget(QLabel("Notes"))
        layout.itemAt(layout.count()-1).widget().setStyleSheet(label_style)
        notes_input = QLineEdit()
        notes_input.setPlaceholderText("Optional notes...")
        notes_input.setStyleSheet(input_style)
        layout.addWidget(notes_input)
        
        def update_net():
            try:
                deducted = float(deduct_input.text() or 0)
                net = int(staff['salary'] - deducted)
                self.dlg_net_lbl.setText(f"Rs. {max(0, net):,}")
            except:
                pass
        
        deduct_input.textChanged.connect(update_net)
        
        layout.addStretch()
        
        # Buttons
        pay_btn = QPushButton("💾 Confirm Payment")
        pay_btn.setStyleSheet("""
            QPushButton {
                background-color: #1B4D89; color: white; border-radius: 10px;
                padding: 12px; font-weight: 700;
            }
            QPushButton:hover { background-color: #153A68; }
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F0F4F8; color: #64748B; border-radius: 10px;
                padding: 12px; font-weight: 600;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        
        def do_pay():
            try:
                mon = month_combo.currentText()
                yr = int(year_input.text() or 0)
                deducted = float(deduct_input.text() or 0)
                notes = notes_input.text()
                net = staff['salary'] - deducted
                today = QDate.currentDate().toString("yyyy-MM-dd")
                
                if yr < 2020:
                    raise ValueError("Invalid year")
                    
                # Duplicate check
                from database.db_handler import check_salary_already_paid
                if check_salary_already_paid(staff['id'], mon, yr):
                    reply = QMessageBox.warning(dialog, "⚠️ Salary Already Paid", 
                                                f"Salary for {mon} {yr} has already been paid to {staff['name']}. Are you sure you want to pay again?",
                                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.No:
                        return
                    
                add_salary_payment(staff['id'], mon, yr, staff['salary'], deducted, net, today, notes)
                
                if deducted > 0:
                    settle_advance(staff['id'], deducted)
                    
                QMessageBox.information(dialog, "Success", "Salary paid successfully!")
                dialog.accept()
                self.load_staff_data()
                # Reload detail
                self.selected_staff = {**self.selected_staff, "advance": max(0, self.selected_staff['advance'] - deducted)}
                self.show_staff_detail()
            except Exception as e:
                QMessageBox.warning(dialog, "Error", str(e))
                
        pay_btn.clicked.connect(do_pay)
        
        layout.addWidget(pay_btn)
        layout.addWidget(cancel_btn)
        
        dialog.exec()
        
    def open_advance_dialog(self):
        staff = self.selected_staff
        dialog = QDialog(self)
        dialog.setWindowTitle(f"➕ Give Advance — {staff['name']}")
        dialog.setFixedSize(380, 350)
        dialog.setStyleSheet("background-color: #F8FAFF;")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(14)
        
        current_adv = QLabel(f"Current advance dues: Rs. {int(staff['advance']):,}")
        current_adv.setStyleSheet("color: #F59E0B; font-size: 14px; font-weight: bold;")
        layout.addWidget(current_adv)
        
        input_style = "background-color: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px; font-size: 13px;"
        label_style = "font-size: 12px; font-weight: bold; color: #1E293B;"
        
        # Amount
        layout.addWidget(QLabel("Advance Amount (Rs.)"))
        layout.itemAt(layout.count()-1).widget().setStyleSheet(label_style)
        amt_input = QLineEdit()
        amt_input.setPlaceholderText("Enter amount")
        amt_input.setValidator(QDoubleValidator(0.0, 9999999.0, 2))
        amt_input.setStyleSheet(input_style)
        layout.addWidget(amt_input)
        
        # Date
        layout.addWidget(QLabel("Date"))
        layout.itemAt(layout.count()-1).widget().setStyleSheet(label_style)
        date_input = QDateEdit()
        date_input.setCalendarPopup(True)
        date_input.setDate(QDate.currentDate())
        date_input.setStyleSheet(input_style)
        layout.addWidget(date_input)
        
        # Notes
        layout.addWidget(QLabel("Reason / Notes"))
        layout.itemAt(layout.count()-1).widget().setStyleSheet(label_style)
        notes_input = QLineEdit()
        notes_input.setPlaceholderText("Optional notes...")
        notes_input.setStyleSheet(input_style)
        layout.addWidget(notes_input)
        
        layout.addStretch()
        
        # Buttons
        give_btn = QPushButton("💾 Give Advance")
        give_btn.setStyleSheet("""
            QPushButton {
                background-color: #F59E0B; color: white; border-radius: 10px;
                padding: 12px; font-weight: 700;
            }
            QPushButton:hover { background-color: #D97706; }
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F0F4F8; color: #64748B; border-radius: 10px;
                padding: 12px; font-weight: 600;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        
        def do_give():
            try:
                amt = float(amt_input.text() or 0)
                if amt <= 0:
                    raise ValueError("Amount must be greater than 0")
                    
                dt = date_input.date().toString("yyyy-MM-dd")
                notes = notes_input.text()
                
                add_advance_payment(staff['id'], amt, dt, notes)
                
                QMessageBox.information(dialog, "Success", "Advance recorded successfully!")
                dialog.accept()
                self.load_staff_data()
                # Reload detail
                self.selected_staff = {**self.selected_staff, "advance": self.selected_staff['advance'] + amt}
                self.show_staff_detail()
            except Exception as e:
                QMessageBox.warning(dialog, "Error", str(e))
                
        give_btn.clicked.connect(do_give)
        
        layout.addWidget(give_btn)
        layout.addWidget(cancel_btn)
        
        dialog.exec()

    def on_add_staff_clicked(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("➕ Add New Staff Member")
        dialog.setFixedSize(440, 600)
        dialog.setStyleSheet("background-color: #F8FAFF;")
        
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(14)
        
        input_style = "background-color: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 16px; font-size: 13px; min-height: 44px; color: #1E293B; QComboBox::drop-down { border: none; width: 0px; } QComboBox::down-arrow { image: none; width: 0px; height: 0px; }"
        label_style = "font-size: 12px; font-weight: bold; color: #1E293B; margin-bottom: 4px;"
        
        def create_field(label, placeholder=None, widget_type=QLineEdit):
            lbl = QLabel(label)
            lbl.setStyleSheet(label_style)
            layout.addWidget(lbl)
            
            w = widget_type()
            if placeholder: w.setPlaceholderText(placeholder)
            w.setStyleSheet(input_style)
            layout.addWidget(w)
            return w

        name_input = create_field("Full Name", "Enter full name")
        role_input = create_field("Role", widget_type=QComboBox)
        role_input.setEditable(True)
        role_input.lineEdit().setPlaceholderText("Select or type custom role...")
        role_input.addItems(["Technician", "Cashier", "Manager", "Helper", "Cleaner", "Guard", "Other"])
        
        layout.addWidget(QLabel("Join Date"))
        layout.itemAt(layout.count()-1).widget().setStyleSheet(label_style)
        
        date_layout = QHBoxLayout()
        date_layout.setSpacing(10)
        
        combos_style = "background-color: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 8px; font-size: 13px; min-height: 40px; color: #1E293B;"
        
        day_input = QComboBox()
        day_input.addItems([str(i) for i in range(1, 32)])
        day_input.setCurrentText(str(QDate.currentDate().day()))
        day_input.setStyleSheet(combos_style)
        
        month_input = QComboBox()
        month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        month_input.addItems(month_names)
        month_input.setCurrentIndex(QDate.currentDate().month() - 1)
        month_input.setStyleSheet(combos_style)
        
        year_input = QComboBox()
        year_input.addItems([str(i) for i in range(2020, 2031)])
        year_input.setCurrentText(str(QDate.currentDate().year()))
        year_input.setStyleSheet(combos_style)
        
        date_layout.addWidget(day_input, 1)
        date_layout.addWidget(month_input, 2)
        date_layout.addWidget(year_input, 1)
        layout.addLayout(date_layout)
        
        phone_input = create_field("Phone Number", "03XX-XXXXXXX")
        salary_input = create_field("Monthly Salary (Rs.)", "Enter monthly salary Rs.")
        salary_input.setValidator(QDoubleValidator(0.0, 9999999.0, 2))
        
        error_lbl = QLabel("")
        error_lbl.setStyleSheet("font-size: 11px; color: #EF4444;")
        error_lbl.hide()
        layout.addWidget(error_lbl)
        
        layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        # Bottom Buttons
        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(25, 10, 25, 25)
        btn_layout.setSpacing(10)
        
        add_btn = QPushButton("💾 Add Staff Member")
        add_btn.setFixedHeight(48)
        add_btn.setStyleSheet("""
            QPushButton {
                 background-color: #1B4D89; color: white; border-radius: 12px;
                 font-weight: 700; font-size: 14px;
            }
            QPushButton:hover { background-color: #153A68; }
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F0F4F8; color: #64748B; border-radius: 10px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        
        def do_add():
            name = name_input.text().strip()
            phone = phone_input.text().strip()
            role = role_input.currentText() or "Other"
            
            # Construct date from combos
            m_num = month_input.currentIndex() + 1
            d_val = int(day_input.currentText())
            join_date = f"{year_input.currentText()}-{m_num:02d}-{d_val:02d}"
            
            salary = float(salary_input.text() or 0)
            counter = ""
            status = "Active"
            
            if not name or not phone:
                error_lbl.setText("Name and Phone are required!")
                error_lbl.show()
                return
                
            try:
                add_staff(name, role, join_date, phone, counter, salary, status)
                QMessageBox.information(dialog, "Success", "Staff member added successfully!")
                dialog.accept()
                self.load_staff_data()
            except Exception as e:
                error_lbl.setText(f"Error: {str(e)}")
                error_lbl.show()

        add_btn.clicked.connect(do_add)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addWidget(btn_container)
        
        dialog.exec()

    def open_edit_dialog(self):
        staff = self.selected_staff
        dialog = QDialog(self)
        dialog.setWindowTitle(f"✏️ Edit Staff — {staff['name']}")
        dialog.setFixedSize(420, 540)
        dialog.setStyleSheet("background-color: #F8FAFF;")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(16)
        
        input_style = "background-color: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px 14px; font-size: 13px; min-height: 42px; QComboBox::drop-down { border: none; width: 0px; } QComboBox::down-arrow { image: none; width: 0px; height: 0px; }"
        label_style = "font-size: 12px; font-weight: bold; color: #1E293B;"
        
        def create_input(label, value, widget_type=QLineEdit):
            layout.addWidget(QLabel(label))
            layout.itemAt(layout.count()-1).widget().setStyleSheet(label_style)
            w = widget_type()
            w.setStyleSheet(input_style)
            if widget_type == QLineEdit:
                w.setText(str(value))
            layout.addWidget(w)
            return w

        name_input = create_input("Full Name", staff['name'])
        role_input = create_input("Role", None, QComboBox)
        role_input.setEditable(True)
        role_input.lineEdit().setPlaceholderText("Select or type custom role...")
        role_input.addItems(["Technician", "Cashier", "Manager", "Helper", "Cleaner", "Guard", "Other"])
        role_input.setCurrentText(staff['role'])
        
        phone_input = create_input("Phone Number", staff['phone'])
        salary_input = create_input("Monthly Salary (Rs.)", staff['salary'])
        salary_input.setValidator(QDoubleValidator(0.0, 9999999.0, 2))
        
        # Join Date Dropdowns for Edit
        layout.addWidget(QLabel("Join Date"))
        layout.itemAt(layout.count()-1).widget().setStyleSheet(label_style)
        edit_date_layout = QHBoxLayout()
        edit_date_layout.setSpacing(10)
        
        combos_style = "background-color: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 8px; font-size: 13px; min-height: 40px; color: #1E293B;"
        
        day_edit = QComboBox()
        day_edit.addItems([str(i) for i in range(1, 32)])
        day_edit.setStyleSheet(combos_style)
        
        month_edit = QComboBox()
        month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        month_edit.addItems(month_names)
        month_edit.setStyleSheet(combos_style)
        
        year_edit = QComboBox()
        year_edit.addItems([str(i) for i in range(2020, 2031)])
        year_edit.setStyleSheet(combos_style)
        
        # Pre-fill from staff data
        j_date = staff['join_date'] # QDate or datetime
        if hasattr(j_date, 'year'):
            day_edit.setCurrentText(str(j_date.day))
            month_edit.setCurrentIndex(j_date.month - 1)
            year_edit.setCurrentText(str(j_date.year))
        
        edit_date_layout.addWidget(day_edit, 1)
        edit_date_layout.addWidget(month_edit, 2)
        edit_date_layout.addWidget(year_edit, 1)
        layout.addLayout(edit_date_layout)
        
        status_input = create_input("Status", None, QComboBox)
        status_input.addItems(["Active", "On Leave", "Resigned"])
        status_input.setCurrentText(staff['status'])
        
        error_lbl = QLabel("")
        error_lbl.setStyleSheet("font-size: 11px; color: #EF4444;")
        error_lbl.hide()
        layout.addWidget(error_lbl)
        
        layout.addStretch()
        
        # Buttons
        save_btn = QPushButton("💾 Save Changes")
        save_btn.setStyleSheet("""
            QPushButton {
                 background-color: #1B4D89; color: white; border-radius: 10px;
                 padding: 12px; font-weight: 700;
            }
            QPushButton:hover { background-color: #153A68; }
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F0F4F8; color: #64748B; border-radius: 10px;
                padding: 12px; font-weight: 600;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        
        def do_save():
            name = name_input.text().strip()
            phone = phone_input.text().strip()
            role = role_input.currentText() or "Other"
            salary = float(salary_input.text() or 0)
            counter = ""
            status = status_input.currentText()
            
            if not name or not phone:
                error_lbl.setText("Name and Phone are required!")
                error_lbl.show()
                return
                
            try:
                # Construct join date from combos
                m_num = month_edit.currentIndex() + 1
                d_val = int(day_edit.currentText())
                join_date = f"{year_edit.currentText()}-{m_num:02d}-{d_val:02d}"
                
                update_staff(staff['id'], name, role, join_date, phone, counter, salary, status)
                QMessageBox.information(dialog, "Success", "Staff updated successfully!")
                dialog.accept()
                self.load_staff_data()
                # Refresh Detail Panel
                full_data = get_staff_by_id(staff['id'])
                if full_data:
                    self.selected_staff = {
                        "id": full_data[0],
                        "name": full_data[1],
                        "role": full_data[2],
                        "join_date": full_data[3],
                        "phone": full_data[4],
                        "counter": full_data[5],
                        "salary": float(full_data[6] or 0),
                        "advance": float(full_data[7] or 0),
                        "status": full_data[8]
                    }
                    self.show_staff_detail()
            except Exception as e:
                error_lbl.setText(f"Error: {str(e)}")
                error_lbl.show()

        save_btn.clicked.connect(do_save)
        layout.addWidget(save_btn)
        layout.addWidget(cancel_btn)
        
        dialog.exec()

    def open_salary_history_dialog(self, employee_id, staff_name):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Salary History — {staff_name}")
        dialog.setFixedSize(750, 420)
        dialog.setStyleSheet("background-color: #F8FAFF;")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        
        table = QTableWidget()
        cols = ["Month", "Year", "Base Salary", "Advance Ded.", "Net Paid", "Notes"]
        table.setColumnCount(len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.setWordWrap(True)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #FAFBFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
            QHeaderView::section {
                background-color: white;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #F0F2F5;
            }
        """)
        
        history = get_staff_salary_history(employee_id)
        table.setRowCount(len(history))
        
        for i, rec in enumerate(history):
            # rec: History_ID, Shop_ID, Employee_ID, Month, Year, Base_Salary, Advance_Deducted, Net_Paid, Payment_Date, Notes
            table.setItem(i, 0, QTableWidgetItem(str(rec[3])))
            # Year value fix - ensure full year string
            table.setItem(i, 1, QTableWidgetItem(str(rec[4])))
            table.setItem(i, 2, QTableWidgetItem(f"Rs. {int(rec[5]):,}"))
            table.setItem(i, 3, QTableWidgetItem(f"Rs. {int(rec[6]):,}"))
            table.setItem(i, 4, QTableWidgetItem(f"Rs. {int(rec[7]):,}"))
            table.setItem(i, 5, QTableWidgetItem(str(rec[9] or "-")))
            
            for j in range(len(cols)):
                item = table.item(i, j)
                if item:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Set specific column widths
        table.setColumnWidth(0, 90)
        table.setColumnWidth(1, 80)
        table.setColumnWidth(2, 120)
        table.setColumnWidth(3, 120)
        table.setColumnWidth(4, 120)
        # Notes column stretches to fill
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(table)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #1B4D89; color: white; border-radius: 8px; padding: 10px; font-weight: bold;")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()

    def open_raise_salary_dialog(self):
        staff = self.selected_staff
        dialog = QDialog(self)
        dialog.setWindowTitle(f"📈 Raise Salary — {staff['name']}")
        dialog.setFixedSize(360, 280)
        dialog.setStyleSheet("background-color: #F8FAFF;")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(12)
        
        curr_lbl = QLabel(f"Current Salary: Rs. {int(staff['salary']):,}")
        curr_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B; margin-bottom: 5px;")
        layout.addWidget(curr_lbl)
        
        input_style = "background-color: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 10px; font-size: 13px;"
        label_style = "font-size: 11px; font-weight: bold; color: #64748B;"
        
        layout.addWidget(QLabel("New Monthly Salary (Rs.)"))
        layout.itemAt(layout.count()-1).widget().setStyleSheet(label_style)
        new_sal_input = QLineEdit()
        new_sal_input.setPlaceholderText("Enter new salary amount")
        new_sal_input.setValidator(QDoubleValidator(0.0, 9999999.0, 2))
        new_sal_input.setStyleSheet(input_style)
        layout.addWidget(new_sal_input)
        
        layout.addWidget(QLabel("Reason (Optional)"))
        layout.itemAt(layout.count()-1).widget().setStyleSheet(label_style)
        reason_input = QLineEdit()
        reason_input.setPlaceholderText("e.g. Annual raise, Promotion")
        reason_input.setStyleSheet(input_style)
        layout.addWidget(reason_input)
        
        error_lbl = QLabel("")
        error_lbl.setStyleSheet("font-size: 11px; color: #EF4444;")
        error_lbl.hide()
        layout.addWidget(error_lbl)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        confirm_btn = QPushButton("Confirm Raise")
        confirm_btn.setStyleSheet("""
            QPushButton { 
                background-color: #10B981; color: white; border-radius: 8px; 
                padding: 10px; font-weight: 700; 
            }
            QPushButton:hover { background-color: #059669; }
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton { 
                background-color: #F0F4F8; color: #64748B; border-radius: 8px; 
                padding: 10px; font-weight: 600; 
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        
        def do_confirm():
            try:
                new_sal = float(new_sal_input.text() or 0)
                if new_sal <= staff['salary']:
                    error_lbl.setText("New salary must be greater than current!")
                    error_lbl.show()
                    return
                
                reason = reason_input.text().strip()
                
                update_staff_salary(staff['id'], new_sal)
                add_salary_raise_record(staff['id'], staff['salary'], new_sal, reason)
                
                # Refresh UI
                dialog.accept() # Close dialog first
                self.load_staff_data()
                # Update selected staff local dict to refresh detail
                self.selected_staff['salary'] = new_sal
                self.show_staff_detail()
                
            except Exception as e:
                error_lbl.setText(f"Error: {str(e)}")
                error_lbl.show()
                
        confirm_btn.clicked.connect(do_confirm)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(confirm_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec()

    def open_pay_all_dialog(self):
        all_staff = get_all_staff()
        active_staff = [s for s in all_staff if s[8] == 'Active']
        if not active_staff:
            QMessageBox.information(self, "Info", "No active staff found for payment.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("💸 Pay All Active Staff")
        dialog.setFixedSize(420, 320)
        dialog.setStyleSheet("background-color: #F8FAFF;")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        table = QTableWidget()
        cols = ["Name", "Salary", "Advance", "Net"]
        table.setColumnCount(len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setStyleSheet("background-color: white; border: 1px solid #E2E8F0; border-radius: 8px;")
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        total_payout = 0
        table.setRowCount(len(active_staff))
        for i, s in enumerate(active_staff):
            # s: Employee_ID, Name, Role, Join_Date, Phone, Assigned_Port, Monthly_Salary, Advance_Amount, Status
            name = s[1]
            sal = float(s[6] or 0)
            adv = float(s[7] or 0)
            net = sal - adv
            total_payout += net
            
            table.setItem(i, 0, QTableWidgetItem(name))
            table.setItem(i, 1, QTableWidgetItem(f"Rs. {int(sal):,}"))
            table.setItem(i, 2, QTableWidgetItem(f"Rs. {int(adv):,}"))
            table.setItem(i, 3, QTableWidgetItem(f"Rs. {int(net):,}"))
            
            for j in range(4):
                table.item(i, j).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(table)
        
        total_lbl = QLabel(f"Total Payout: Rs. {int(total_payout):,}")
        total_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #1B4D89; margin: 5px 0;")
        layout.addWidget(total_lbl)
        
        # Buttons
        confirm_btn = QPushButton("Confirm Pay All")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981; color: white; border-radius: 10px;
                padding: 12px; font-weight: 700;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #F0F4F8; color: #64748B; border-radius: 10px;
                padding: 12px; font-weight: 700;
            }
            QPushButton:hover { background-color: #E2E8F0; }
        """)
        cancel_btn.clicked.connect(dialog.reject)
        
        def do_pay_all():
            mon = datetime.now().strftime("%B")
            yr = datetime.now().year
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Check for duplicates first
            already_paid_names = []
            for s in active_staff:
                if check_salary_already_paid(s[0], mon, yr):
                    already_paid_names.append(s[1])
            
            final_payout_list = active_staff
            if already_paid_names:
                msg = f"Following {len(already_paid_names)} staff members already received salary this month:\n\n"
                msg += "\n".join(already_paid_names)
                msg += "\n\nDo you want to skip them or pay everyone again?"
                
                msg_box = QMessageBox(dialog)
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setWindowTitle("⚠️ Duplicate Salary Warning")
                msg_box.setText(msg)
                
                skip_btn = msg_box.addButton("Skip Already Paid", QMessageBox.ButtonRole.ActionRole)
                pay_all_btn = msg_box.addButton("Pay Everyone", QMessageBox.ButtonRole.ActionRole)
                cancel_btn = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                
                msg_box.exec()
                
                if msg_box.clickedButton() == cancel_btn:
                    return
                elif msg_box.clickedButton() == skip_btn:
                    final_payout_list = [s for s in active_staff if s[1] not in already_paid_names]
            
            if not final_payout_list:
                QMessageBox.information(dialog, "Info", "No new salaries to process.")
                dialog.accept()
                return

            for s in final_payout_list:
                eid = s[0]
                sal = float(s[6] or 0)
                adv = float(s[7] or 0)
                net = sal - adv
                
                add_salary_payment(eid, mon, yr, sal, adv, net, today, "Bulk payment")
                if adv > 0:
                    settle_advance(eid, adv)
            
            QMessageBox.information(dialog, "Success", f"Salaries for {len(final_payout_list)} staff members processed successfully.")
            dialog.accept()
            self.load_staff_data()

        confirm_btn.clicked.connect(do_pay_all)
        layout.addWidget(confirm_btn)
        layout.addWidget(cancel_btn)
        
        dialog.exec()
