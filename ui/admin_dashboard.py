import sys
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel, QHBoxLayout, 
                             QFrame, QGraphicsDropShadowEffect, QApplication, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QComboBox, QPushButton, QDialog,
                             QLineEdit, QFormLayout, QMessageBox, QFileDialog, QAbstractItemView, QScrollArea,
                             QStackedWidget)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon
from database.db_handler import (get_consolidated_stats, get_recent_transactions, 
                                 get_top_items, add_expense, get_analytics_data, 
                                 CURRENT_SHOP_ID, set_shop_id, export_to_excel,
                                 get_history_data, get_dashboard_insights)
import pandas as pd
from ui.admin_settings_window import AdminSettingsView
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from ui.styles import STYLE_SHEET
from utils.report_generator import generate_daily_report
class ExpenseDialog(QDialog):
    data_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Shop Expense")
        self.setFixedSize(400, 350)
        self.setStyleSheet("""
            QDialog { background-color: #F8F9FA; font-family: 'Segoe UI'; }
            QLabel { color: #2D3436; font-weight: bold; }
            QLineEdit, QComboBox {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px;
                color: #2D3436;
            }
            QPushButton {
                background-color: #1b4d89;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover { background-color: #245fa8; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30,30,30,30)
        
        title = QLabel("Add New Expense")
        title.setStyleSheet("font-size: 20px; margin-bottom: 20px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(15)
        
        self.cat_input = QComboBox()
        self.cat_input.addItems(["Utility Bills", "Rent", "Staff Salary", "Maintenance", "Others"])
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter amount (Rs.)")
        
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Short description")
        
        form.addRow("Category:", self.cat_input)
        form.addRow("Amount:", self.amount_input)
        form.addRow("Description:", self.desc_input)
        
        layout.addLayout(form)
        layout.addSpacing(20)
        
        self.save_btn = QPushButton("Save Expense")
        self.save_btn.clicked.connect(self.handle_save)
        layout.addWidget(self.save_btn)

    def handle_save(self):
        cat = self.cat_input.currentText()
        amt = self.amount_input.text()
        desc = self.desc_input.text()
        if not amt or not desc:
            QMessageBox.warning(self, "Missing Info", "Please fill all fields.")
            return
        try:
            amount_val = float(amt)
            add_expense(cat, amount_val, desc)
            self.data_updated.emit()
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid numeric value for the amount.")

class AdminDashboard(QMainWindow):
    logout_clicked = pyqtSignal()
    settings_updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Control Panel")
        self.showMaximized()
        
        # --- GLOBAL UI STYLE ---
        self.setStyleSheet(STYLE_SHEET)
        
        # --- SCROLL AREA WRAPPER ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setObjectName("DashboardScroll")
        self.scroll.setStyleSheet("QScrollArea#DashboardScroll { background-color: #F0F2F5; border: none; }")
        
        self.central_widget = QWidget()
        self.central_widget.setObjectName("AdminMain")
        self.central_widget.setStyleSheet("QWidget#AdminMain { background-color: #F0F2F5; }")
        self.setCentralWidget(self.central_widget)
        
        # Horizontal layout to split Sidebar and Content
        self.root_layout = QHBoxLayout(self.central_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        
        # --- 1. SIDEBAR ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setObjectName("AdminSidebar")
        self.sidebar.setStyleSheet("""
            QFrame#AdminSidebar { 
                background-color: #FFFFFF; 
                border-right: 1px solid #E0E0E0;
            }
            QPushButton {
                text-align: left;
                padding: 15px 25px;
                border: none;
                border-radius: 12px;
                background-color: transparent;
                color: #636E72;
                font-weight: 600;
                font-size: 14px;
                margin: 5px 15px;
            }
            QPushButton:hover { background-color: #F8F9FA; color: #3A8DFF; }
            QPushButton#ActiveNav { 
                background-color: #3A8DFF10; 
                color: #3A8DFF; 
                border: 1px solid #3A8DFF30;
            }
        """)
        
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(10, 40, 10, 40)
        side_layout.setSpacing(5)
        
        side_title = QLabel("🛡️ ADMIN")
        side_title.setStyleSheet("font-size: 20px; font-weight: 900; color: #1E293B; margin-bottom: 30px; margin-left: 20px;")
        side_layout.addWidget(side_title)
        
        self.nav_home = QPushButton("🏠 Home")
        self.nav_home.setObjectName("ActiveNav")
        self.nav_home.clicked.connect(lambda: self.switch_view(0, self.nav_home))
        
        self.nav_history = QPushButton("📜 History")
        self.nav_history.clicked.connect(lambda: self.switch_view(3, self.nav_history))
        self.nav_report = QPushButton("📊 Report")
        self.nav_report.clicked.connect(self.handle_export)
        
        self.nav_staff = QPushButton("👥 Staff Record")
        self.nav_staff.clicked.connect(lambda: self.switch_view(1, self.nav_staff))
        
        self.nav_settings = QPushButton("⚙️ Settings")
        self.nav_settings.clicked.connect(lambda: self.switch_view(2, self.nav_settings))
        
        side_layout.addWidget(self.nav_home)
        side_layout.addWidget(self.nav_history)
        side_layout.addWidget(self.nav_report)
        side_layout.addWidget(self.nav_staff)
        side_layout.addWidget(self.nav_settings)
        side_layout.addStretch()
        
        self.nav_logout = QPushButton("🚪 Logout")
        self.nav_logout.clicked.connect(self.logout)
        side_layout.addWidget(self.nav_logout)
        
        self.root_layout.addWidget(self.sidebar)
        
        # --- 2. MAIN CONTENT AREA ---
        self.content_area = QWidget()
        self.main_layout = QVBoxLayout(self.content_area)
        self.main_layout.setContentsMargins(40, 30, 40, 40)
        self.main_layout.setSpacing(30)
        
        # --- GLOBAL SHARED NAVBAR (Persistent) ---
        self.setup_shared_navbar()
        
        # --- STACKED WIDGET FOR VIEWS ---
        self.stack = QStackedWidget()
        self.dashboard_container = QWidget()
        self.dash_layout = QVBoxLayout(self.dashboard_container)
        self.dash_layout.setContentsMargins(0, 0, 0, 0)
        self.dash_layout.setSpacing(30)
        
        self.stat_widgets = {} 
        
        # Remove top bar from here, it's global now
        self.setup_stats_cards()
        self.setup_center_section()
        self.setup_bottom_bar()
        
        self.stack.addWidget(self.dashboard_container) # Index 0
        
        # Staff View
        from ui.staff_view import StaffView
        self.staff_container = StaffView()
        self.stack.addWidget(self.staff_container) # Index 1
        
        # Settings View Placeholder setup for stack
        from ui.admin_settings_window import AdminSettingsView
        self.settings_view = AdminSettingsView()
        self.settings_view.back_clicked.connect(lambda: self.switch_view(0, self.nav_home))
        self.settings_view.settings_saved.connect(self.settings_updated.emit)
        self.stack.addWidget(self.settings_view) # Index 2
        
        # History View Placeholder
        self.history_view = QWidget()
        history_layout = QVBoxLayout(self.history_view)
        history_layout.addWidget(QLabel("History View - Coming Soon", alignment=Qt.AlignmentFlag.AlignCenter))
        self.stack.addWidget(self.history_view) # Index 3
        
        self.main_layout.addWidget(self.stack)
        
        self.root_layout.addWidget(self.content_area)
        
        # Track buttons for ActiveNav style
        self.nav_buttons = [self.nav_home, self.nav_history, self.nav_report, self.nav_staff, self.nav_settings]
        
        # Refresh now only AFTER UI is fully built
        self.refresh_dashboard()

    def switch_view(self, index, active_btn):
        """Switches the QStackedWidget index and handles ActiveNav button highlighting."""
        # Remove ActiveNav object name from all buttons
        for btn in self.nav_buttons:
            btn.setObjectName("")
            
        # Set ActiveNav to the clicked button
        active_btn.setObjectName("ActiveNav")
        
        # Force stylesheet update
        for btn in self.nav_buttons:
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            
        self.stack.setCurrentIndex(index)
        
        if index == 0:
            self.refresh_dashboard()
        elif index == 1:
            self.staff_container.refresh_table()


    def refresh_dashboard(self):
        """Live refresh of all data and charts."""
        data = get_dashboard_insights()
        
        # 1. Update Cards
        self.sales_val.setText(f"Rs. {data['today_sales']:,.0f}")
        self.repairs_val.setText(f"{data['today_repairs_count']}")
        self.profit_val.setText(f"Rs. {data['monthly_profit']:,.0f}")
        self.stock_val.setText(f"Low: {len(data['low_stock_list'])}")
        
        # 2. Update Chart
        self.update_chart(data['weekly_trend'])
        
        # 3. Update Alerts (Right Side)
        self.update_alerts(data['low_stock_list'])
        
        # 4. Refresh existing tables if period selected
        self.refresh_all_dashboard_data(self.filter_combo.currentText())

    def update_chart(self, trend_data):
        self.ax.clear()
        
        # Set Stone/Marble solid background for chart
        self.ax.set_facecolor('#F4F1EA')
        self.figure.patch.set_facecolor('#FFFFFF')
        
        labels = trend_data['labels']
        values = trend_data['values']
        
        if not values or all(v == 0 for v in values):
            # Zero State Handling
            self.ax.text(0.5, 0.5, "No Data Available", horizontalalignment='center', verticalalignment='center', transform=self.ax.transAxes, fontsize=14, color='#94A3B8')
            self.ax.set_ylim(0, 100)
            
        # Professional Wood-Colored Line Chart (matching Image 2)
        self.ax.plot(labels, values, color='#8B4513', linewidth=4, marker='o', 
                    markerfacecolor='#D2B48C', markeredgecolor='white', markersize=10)

        
        # Styling
        self.ax.tick_params(axis='x', colors='#636E72', labelsize=10)
        self.ax.tick_params(axis='y', colors='#636E72', labelsize=10)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color('#E0E0E0')
        self.ax.spines['left'].set_color('#E0E0E0')
        
        # Smooth line shadow (Subtle effect)
        self.ax.fill_between(labels, values, color='#8B4513', alpha=0.1)
        
        self.canvas.draw()

    def update_alerts(self, stock_items):
        self.alert_list.clear()
        
        # Fetch Top items for activity list
        from database.db_handler import get_top_items
        top_sold = get_top_items("Today", 5)
        
        for name, qty in top_sold:
            self.alert_list.addItem(f"✅ SOLD: {name} (x{qty})")
            
        for name, qty in stock_items:
            self.alert_list.addItem(f"⚠️ LOW STOCK: {name} ({qty} left)")
        
        if self.alert_list.count() == 0:
            self.alert_list.addItem("✅ System Idle - No alerts")

    def refresh_all_dashboard_data(self, period):
        """Master function to refresh stats, top items, and transaction history."""
        try:
            self.refresh_financials(period)
            self.refresh_top_selling_items(period)
            self.refresh_history_table(period)
        except Exception as e:
            print(f"Safety Check: Dashboard Refresh Failed Triggered: {e}")

    def event(self, event):
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.WindowActivate:
            # Refresh using currently selected filter for FULL DATA (Charts + Tables)
            self.refresh_dashboard()
        return super().event(event)


    def setup_shared_navbar(self):
        nav_frame = QFrame()
        nav_frame.setFixedHeight(80)
        nav_frame.setObjectName("Navbar") # Inherits Neumorphic White Card style
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(20, 0, 20, 0)
        
        # Left: Search or Title (Optional, keeping it clean)
        title_lbl = QLabel("Dashboard Overview")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #1E293B;")
        nav_layout.addWidget(title_lbl)
        
        nav_layout.addStretch()
        
        # Middle-Right: Period Dropdown
        p_lbl = QLabel("Period:")
        p_lbl.setStyleSheet("color: #636E72; font-weight: bold; font-size: 13px;")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Last Week", "Month", "Last 6 Months", "All Time"])
        self.filter_combo.setFixedWidth(160)
        self.filter_combo.currentTextChanged.connect(self.refresh_all_dashboard_data)
        
        nav_layout.addWidget(p_lbl)
        nav_layout.addWidget(self.filter_combo)
        nav_layout.addSpacing(25)
        
        # Right: Settings & Logout Icons
        self.quick_settings = QPushButton("⚙️")
        self.quick_settings.setFixedSize(45, 45)
        self.quick_settings.setObjectName("NavbarIcon")
        self.quick_settings.setStyleSheet("QPushButton { background-color: #F8F9FA; border-radius: 22px; font-size: 18px; border: 1px solid #E0E0E0; }")
        self.quick_settings.clicked.connect(self.open_settings)
        
        self.quick_logout = QPushButton("🚪")
        self.quick_logout.setFixedSize(45, 45)
        self.quick_logout.setStyleSheet("QPushButton { background-color: #FFF5F5; border-radius: 22px; font-size: 18px; border: 1px solid #FFEBEB; }")
        self.quick_logout.clicked.connect(self.logout)
        
        nav_layout.addWidget(self.quick_settings)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(self.quick_logout)
        nav_layout.addSpacing(25)
        
        # Far Right: Profile Section
        profile_layout = QVBoxLayout()
        profile_layout.setSpacing(0)
        profile_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        name_lbl = QLabel("Faizan Khan")
        name_lbl.setStyleSheet("font-weight: 800; font-size: 14px; color: #1E293B;")
        role_lbl = QLabel("System Admin")
        role_lbl.setStyleSheet("font-size: 11px; color: #94A3B8; font-weight: bold;")
        
        profile_layout.addWidget(name_lbl)
        profile_layout.addWidget(role_lbl)
        
        self.avatar = QLabel()
        self.avatar.setFixedSize(45, 45)
        self.avatar.setStyleSheet("background-color: #E6E9EE; border-radius: 22px; border: 2px solid #FFFFFF;")
        # Note: Set pixmap here if an image exists
        
        nav_layout.addLayout(profile_layout)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(self.avatar)
        
        self.main_layout.addWidget(nav_frame)

    def setup_stats_cards(self):
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(25)
        
        self.sales_val = self.create_stat_card("Today's Sales", "#10B981", "💰")
        self.repairs_val = self.create_stat_card("Total Repairs", "#3B82F6", "🔧")
        self.profit_val = self.create_stat_card("Profit (Month)", "#F59E0B", "✨")
        self.stock_val = self.create_stat_card("Available Stock", "#EF4444", "📦")
        
        self.dash_layout.addLayout(self.cards_layout)

    def create_stat_card(self, title, color, icon):
        card = QFrame()
        card.setFixedHeight(140)
        card.setObjectName("StatCard")
        # Premium Styling: Thick left border for distinction
        card.setStyleSheet(f"""
            QFrame#StatCard {{ 
                background-color: #FFFFFF; 
                border-radius: 20px; 
                border: 1px solid #E0E0E0;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setYOffset(10)
        card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(25, 20, 25, 25)
        card_layout.setSpacing(10)
        
        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: 800; letter-spacing: 1px;")
        
        value_layout = QHBoxLayout()
        v_lbl = QLabel("...")
        v_lbl.setStyleSheet("font-size: 28px; font-weight: 800; color: #1E293B;")
        
        i_lbl = QLabel(icon)
        i_lbl.setFixedSize(50, 50)
        i_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        i_lbl.setStyleSheet(f"""
            QLabel {{ 
                background-color: #F0F4F8; 
                color: {color}; 
                font-size: 24px; 
                border-radius: 25px;
            }}
        """)
        
        value_layout.addWidget(v_lbl)
        value_layout.addWidget(i_lbl)
        value_layout.addStretch()
        
        card_layout.addWidget(title_lbl)
        card_layout.addLayout(value_layout)
        
        self.cards_layout.addWidget(card)
        
        # Store for programmatic updates
        if not hasattr(self, 'stat_widgets'):
            self.stat_widgets = {}
        self.stat_widgets[title] = v_lbl
        
        return v_lbl

    def setup_center_section(self):
        center_layout = QHBoxLayout()
        center_layout.setSpacing(25)
        
        # --- LEFT SIDE: Weekly Sales Trend Chart ---
        chart_frame = QFrame()
        chart_frame.setObjectName("MainContainer") # Apply White Card styling
        chart_frame.setStyleSheet("QFrame#MainContainer { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 20px; }")
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(25, 25, 25, 25)
        
        c_title = QLabel("📊 Weekly Sales Trend")
        c_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B; margin-bottom: 10px;")
        chart_layout.addWidget(c_title)
        
        self.figure = Figure(figsize=(5, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        chart_layout.addWidget(self.canvas)
        
        center_layout.addWidget(chart_frame, 2)
        
        # --- RIGHT SIDE: Alerts ---
        alert_frame = QFrame()
        alert_frame.setFixedWidth(380)
        alert_frame.setObjectName("MainContainer")
        alert_frame.setStyleSheet("QFrame#MainContainer { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 25px; }")
        al_layout = QVBoxLayout(alert_frame)
        al_layout.setContentsMargins(25, 25, 25, 25)
        
        al_title = QLabel("📢 Recent Alerts")
        al_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B; margin-bottom: 10px;")
        al_layout.addWidget(al_title)
        
        from PyQt6.QtWidgets import QListWidget
        self.alert_list = QListWidget()
        self.alert_list.setStyleSheet("""
            QListWidget { border: none; font-size: 14px; background: transparent; }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #F0F2F5; color: #44474B; }
        """)
        al_layout.addWidget(self.alert_list)
        
        center_layout.addWidget(alert_frame, 1)
        self.dash_layout.addLayout(center_layout)
        
        # --- BOTTOM SECTION: DATA TABLES ---
        self.analytics_card = QFrame()
        self.analytics_card.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 15px; }")
        ana_layout = QVBoxLayout(self.analytics_card)
        ana_layout.setContentsMargins(25, 25, 25, 25)
        
        ana_title = QLabel("📜 Transaction & Expense History")
        ana_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2D3436; margin-bottom: 10px;")
        ana_layout.addWidget(ana_title)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Date", "Type", "Description", "Amount"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setShowGrid(False)
        self.history_table.setFixedHeight(250)
        self.history_table.setStyleSheet("""
            QTableWidget { border: none; background-color: transparent; font-size: 14px; color: #2D3436; }
            QHeaderView::section { background-color: #F8F9FA; color: #636E72; padding: 10px; border: none; font-weight: bold; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #F1F2F6; }
        """)
        ana_layout.addWidget(self.history_table)
        self.dash_layout.addWidget(self.analytics_card)

    def setup_bottom_bar(self):
        bottom_row = QHBoxLayout()
        
        self.expense_btn = QPushButton("➕ Add Shop Expense")
        self.expense_btn.setFixedSize(260, 50)
        self.expense_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.expense_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover { background-color: #DC2626; }
        """)
        self.expense_btn.clicked.connect(self.open_expense_popup)
        
        bottom_row.addStretch()
        bottom_row.addWidget(self.expense_btn)
        self.dash_layout.addLayout(bottom_row)

    def open_expense_popup(self):
        diag = ExpenseDialog(self)
        diag.data_updated.connect(lambda: self.refresh_all_dashboard_data(self.filter_combo.currentText()))
        diag.exec()

    def handle_shop_change(self, index):
        new_id = index + 1
        set_shop_id(new_id)
        self.refresh_all_dashboard_data(self.filter_combo.currentText())
        


    def refresh_financials(self, period):
        """Data update with key validation safety."""
        stats = get_consolidated_stats(CURRENT_SHOP_ID, period)
        
        # Update Main High-Level Stats
        mapping = {
            "Total Sales": "Total Sales",
            "Net Profit": "Net Profit",
            "Total Expenses": "Total Expenses"
        }
        
        for ui_key, stat_key in mapping.items():
            if ui_key in self.stat_widgets:
                val = stats.get(stat_key.lower().replace(' ', '_'), 0)
                self.stat_widgets[ui_key].setText(f"Rs. {val:,.0f}")
        
        # Additional Split Stats with safety checks
        if hasattr(self, 'pending_val'):
            self.pending_val.setText(str(stats.get('pending_repairs', 0)))
        if hasattr(self, 'completed_val'):
            self.completed_val.setText(str(stats.get('completed_repairs', 0)))
        
        # Sidebar Breakdown Stats
        if hasattr(self, 'op_stock_val'):
            self.op_stock_val.setText(f"Rs. {stats.get('stock_expense', 0):,.0f}")
        if hasattr(self, 'op_repair_exp_val'):
            self.op_repair_exp_val.setText(f"Rs. {stats.get('repair_expense', 0):,.0f}")
        if hasattr(self, 'op_repair_rev_val'):
            self.op_repair_rev_val.setText(f"Rs. {stats.get('repair_revenue', 0):,.0f}")

    def refresh_top_selling_items(self, period):
        # Clear top items list
        while self.items_list_layout.count():
            item = self.items_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        top_items = get_top_items(period, 12)
        for name, qty in top_items:
            item_frame = QFrame()
            item_frame.setFixedHeight(45)
            item_frame.setStyleSheet("""
                QFrame { background-color: #F8F9FA; border-radius: 8px; border: 1px solid #E0E0E0; }
            """)
            if_layout = QHBoxLayout(item_frame)
            if_layout.setContentsMargins(15, 5, 15, 5)
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet("font-weight: bold; color: #2D3436; font-size: 12px;")
            qty_lbl = QLabel(f"{qty} SOLD")
            qty_lbl.setStyleSheet("color: #10B981; font-weight: 800; font-size: 11px;")
            if_layout.addWidget(name_lbl)
            if_layout.addStretch()
            if_layout.addWidget(qty_lbl)
            self.items_list_layout.addWidget(item_frame)
        self.items_list_layout.addStretch()

    def refresh_history_table(self, period):
        self.history_table.setRowCount(0)
        data = get_history_data(period)
        
        for row_data in data:
            row_idx = self.history_table.rowCount()
            self.history_table.insertRow(row_idx)
            
            date_str = str(row_data[0]) if row_data[0] else ""
            type_str = str(row_data[1])
            desc_str = str(row_data[2])
            amt_val = float(row_data[3] or 0)
            
            self.history_table.setItem(row_idx, 0, QTableWidgetItem(date_str))
            
            type_item = QTableWidgetItem(type_str)
            if type_str == 'Sale': type_item.setForeground(QColor("#3B82F6"))
            elif type_str == 'Repair': type_item.setForeground(QColor("#F59E0B"))
            elif type_str == 'Expense': type_item.setForeground(QColor("#EF4444"))
            self.history_table.setItem(row_idx, 1, type_item)
            
            self.history_table.setItem(row_idx, 2, QTableWidgetItem(desc_str))
            
            amt_item = QTableWidgetItem(f"Rs. {amt_val:,.0f}")
            if type_str == 'Expense': amt_item.setForeground(QColor("#EF4444"))
            else: amt_item.setForeground(QColor("#10B981"))
            self.history_table.setItem(row_idx, 3, amt_item)

    def clear_dashboard(self):
        self.history_table.setRowCount(0)
        self.op_stock_val.setText("Rs. 0")
        self.op_repair_exp_val.setText("Rs. 0")
        self.op_repair_rev_val.setText("Rs. 0")
        for label in self.stat_widgets.values():
            label.setText("Rs. 0")
            
        while self.items_list_layout.count():
            item = self.items_list_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def load_report_data(self):
        """Prepares monthly trend data for Export purposes."""
        try:
            sales_df, expense_df, cost_df = get_analytics_data(12) # Global 12 months for report
            
            sales_df['Timestamp'] = pd.to_datetime(sales_df['Timestamp'])
            expense_df['Timestamp'] = pd.to_datetime(expense_df['Timestamp'])
            cost_df['Timestamp'] = pd.to_datetime(cost_df['Timestamp'])
            
            monthly_sales = sales_df.set_index('Timestamp')['Total_Amount'].resample('ME').sum()
            monthly_shop_exp = expense_df.set_index('Timestamp')['Amount'].resample('ME').sum()
            monthly_prod_costs = cost_df.set_index('Timestamp')['Purchase_Price'].resample('ME').sum()
            
            analytics_df = pd.DataFrame(index=monthly_sales.index)
            analytics_df['Month'] = analytics_df.index.strftime('%B %Y')
            analytics_df['Total Sales'] = monthly_sales
            analytics_df['Expenses'] = monthly_shop_exp.add(monthly_prod_costs, fill_value=0)
            analytics_df['Net Profit'] = analytics_df['Total Sales'] - analytics_df['Expenses']
            
            return analytics_df[['Month', 'Total Sales', 'Expenses', 'Net Profit']].iloc[::-1].fillna(0)
        except Exception:
            return pd.DataFrame()

    def handle_export(self):
        report_df = self.load_report_data()
        if report_df.empty:
            QMessageBox.warning(self, "No Data", "There is no performance data available to export.")
            return
            
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Performance Report", "Monthly_Security_Report.xlsx", "Excel Files (*.xlsx)"
        )
        
        if filename:
            try:
                self.export_data_to_excel(report_df, filename)
                QMessageBox.information(self, "Export Successful", f"Report saved to:\n{filename}")
                
                try:
                    from datetime import datetime
                    pdf_path = generate_daily_report(datetime.now().strftime("%Y-%m-%d"))
                    QMessageBox.information(self, "PDF Report", f"PDF Report also saved to: {pdf_path}")
                except Exception as e:
                    print(f"PDF Gen failed: {e}")
                    
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Error saving report: {e}")


    def export_data_to_excel(self, data_frame, filename):
        date_now_str = __import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        from openpyxl.styles import Font, PatternFill, Alignment
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            data_frame.to_excel(writer, index=False, sheet_name='Performance Report', startrow=3)
            
            worksheet = writer.sheets['Performance Report']
            
            # --- 1. Headers ---
            worksheet['A1'] = f"Shop ID: {CURRENT_SHOP_ID} - Performance Report"
            worksheet['A1'].font = Font(size=14, bold=True, color="1B4D89")
            worksheet['A2'] = f"Generated On: {date_now_str}"
            worksheet['A2'].font = Font(size=10, italic=True)
            
            # --- 2. Styling Data Headers ---
            header_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
            for cell in worksheet[4]:
                cell.fill = header_fill
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")
                
            # --- 3. Total Row ---
            num_rows = len(data_frame)
            if num_rows > 0:
                last_row = 4 + num_rows + 1
                worksheet.cell(row=last_row, column=1, value="TOTAL:")
                worksheet.cell(row=last_row, column=1).font = Font(bold=True)
                
                # Sum columns (excluding Month which is index 0)
                # Sales is column 2, Expenses 3, Net Profit 4
                for col_idx in [2, 3, 4]:
                    col_name = data_frame.columns[col_idx-1]
                    total_val = data_frame[col_name].sum()
                    cell = worksheet.cell(row=last_row, column=col_idx, value=total_val)
                    cell.font = Font(bold=True)
                    cell.number_format = '#,##0.00'
            
            # --- 4. Auto-width ---
            for i, col in enumerate(data_frame.columns):
                max_len = data_frame[col].astype(str).map(len).max() if not data_frame.empty else 0
                header_len = len(str(col))
                final_len = max(max_len, header_len) + 5
                worksheet.column_dimensions[chr(65 + i)].width = final_len

    def logout(self):
        self.logout_clicked.emit()
        self.close()

    def auto_logout(self):
        self.logout()

    def reset_timer(self):
        pass

    # Event overrides to detect activity
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

    def open_settings(self):
        self.switch_view(2, self.nav_settings)

    def show_dashboard(self):
        self.stack.setCurrentIndex(0)
        self.refresh_all_dashboard_data(self.filter_combo.currentText())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AdminDashboard()
    win.show()
    sys.exit(app.exec())
