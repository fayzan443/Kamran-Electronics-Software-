import sys
import os
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QPushButton, 
                             QLabel, QHBoxLayout, QFrame, QGridLayout, QTableWidget, 
                             QHeaderView, QGraphicsDropShadowEffect, QApplication, 
                             QTableWidgetItem, QStyledItemDelegate, QStyle, QAbstractItemView, QLineEdit)
from PyQt6.QtCore import Qt, QSize, QTimer
from ui.products_window import ProductsWindow
from ui.repairs_window import RepairsWindow
from ui.new_repair_window import NewRepairWindow
from ui.add_stock_window import AddStockWindow
from ui.new_bill_window import NewBillWindow
from ui.notification_window import NotificationPopup
from ui.login_form import LoginForm
from ui.admin_dashboard import AdminDashboard
from database.db_handler import get_notifications, get_bill_history, sync_alerts_to_table, get_app_settings
from ui.styles import STYLE_SHEET

class RowHoverDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hovered_row = -1

    def paint(self, painter, option, index):
        # Full row hover effect
        if index.row() == self.hovered_row and not (option.state & QStyle.StateFlag.State_Selected):
            painter.fillRect(option.rect, QColor("#dfe6e9")) # Metal light grey
        super().paint(painter, option, index)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 1. Load Settings First
        self.app_settings = self.load_settings()
        
        # 2. Setup Session State
        self.admin_logged_in = False
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        # 3. Initialize UI
        self.init_ui()
        
        # 4. Apply Global Styles
        self.setStyleSheet(STYLE_SHEET)
        self.showMaximized()
        
        # Load Data
        QTimer.singleShot(500, self.load_initial_data)

    def init_ui(self):
        # Move all UI setup here
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.outer_layout = QVBoxLayout(self.central_widget)
        self.outer_layout.setContentsMargins(40, 40, 40, 40)
        
        # MAIN CARD CONTAINER
        self.main_container = QFrame()
        self.main_container.setObjectName("MainContainer")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.main_container.setGraphicsEffect(shadow)
        
        self.outer_layout.addWidget(self.main_container)
        
        self.container_layout = QVBoxLayout(self.main_container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        
        self.setup_navbar()
        self.setup_actions()
        self.setup_activity()

    def apply_styles(self):
        self.setStyleSheet(STYLE_SHEET)
        self.showMaximized()

    def setup_navbar(self):
        self.navbar = QFrame()
        self.navbar.setObjectName("Navbar")
        self.navbar.setFixedHeight(95)
        self.navbar_layout = QHBoxLayout(self.navbar)
        self.navbar_layout.setContentsMargins(35, 0, 35, 0)
        
        self.logo_label = QLabel("⚡")
        self.logo_label.setStyleSheet("font-size: 32px; color: white;")
        
        self.shop_label = QLabel(self.app_settings.get("shop_name", "Kamran Electronics"))
        self.shop_label.setObjectName("ShopName")
        
        # Bell & Badge
        self.bell_icon = QPushButton("🔔")
        self.bell_icon.setFixedSize(45, 45)
        self.bell_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bell_icon.setStyleSheet("background: rgba(255,255,255,0.1); border-radius: 22px; font-size: 18px; color: white;")
        self.bell_icon.clicked.connect(self.show_notifications)
        
        # Initialize Badge
        self.badge = QLabel("0", self)
        self.badge.setFixedSize(22, 22)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setStyleSheet("background-color: #ff4757; color: white; border-radius: 11px; font-weight: bold; border: 2px solid white; font-size: 10px;")
        self.badge.hide()
        
        # Removed 'New Bill' as requested to keep navbar clean
        
        self.btn_admin = QPushButton("🛡️ ADMIN")
        self.btn_admin.setFixedWidth(130)
        self.btn_admin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_admin.clicked.connect(self.open_login)
        
        self.navbar_layout.addWidget(self.logo_label)
        self.navbar_layout.addWidget(self.shop_label)
        self.navbar_layout.addStretch()
        self.navbar_layout.addWidget(self.bell_icon)
        self.navbar_layout.addSpacing(15)
        self.navbar_layout.addWidget(self.btn_admin)
        
        self.container_layout.addWidget(self.navbar)

    def setup_actions(self):
        self.actions_area = QWidget()
        actions_layout = QVBoxLayout(self.actions_area)
        actions_layout.setContentsMargins(40, 40, 40, 30)
        
        self.grid = QGridLayout()
        self.grid.setSpacing(25)
        
        # Row 1: 3 Buttons
        row1 = [("🔧 New Repair", self.open_new_repair), 
                ("💰 New Bill", self.open_new_bill), 
                ("📦 Add Stock", self.manage_products)]
        for i, (text, func) in enumerate(row1):
            btn = QPushButton(text)
            btn.setFixedHeight(115)
            btn.setObjectName("BlueButton") # Apply object name for styling
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(func)
            self.grid.addWidget(btn, 0, i)
        
        # Row 2: 2 Manager Buttons
        btn_stock = QPushButton("📊 Product Stock Manager")
        btn_stock.setFixedHeight(135)
        btn_stock.setObjectName("TealBorderButton") # Apply object name for styling
        btn_stock.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_stock.clicked.connect(self.open_product_manager)
        
        btn_repair = QPushButton("🛠 Repairing Manager")
        btn_repair.setFixedHeight(135)
        btn_repair.setObjectName("TealBorderButton") # Apply object name for styling
        btn_repair.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_repair.clicked.connect(self.manage_repairs)
        
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(25)
        row2_layout.addWidget(btn_stock)
        row2_layout.addWidget(btn_repair)
        
        actions_layout.addLayout(self.grid)
        actions_layout.addLayout(row2_layout)
        self.container_layout.addWidget(self.actions_area)

    def setup_activity(self):
        self.activity_container = QFrame()
        self.activity_container.setObjectName("ActivityContainer") # Consistent object name
        activity_main_layout = QVBoxLayout(self.activity_container)
        activity_main_layout.setContentsMargins(40, 10, 40, 40)
        activity_main_layout.setSpacing(0)

        # Activity Content Card
        self.history_card = QFrame()
        self.history_card.setObjectName("MainContainer")
        history_layout = QVBoxLayout(self.history_card)
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_layout.setSpacing(0)

        # Header Title
        title_header = QFrame()
        title_header.setFixedHeight(70)
        title_header.setObjectName("Navbar") # Standardize header as Navbar
        title_layout = QHBoxLayout(title_header)
        title_layout.setContentsMargins(25, 0, 25, 0)
        
        icon_lbl = QLabel("🕒")
        icon_lbl.setStyleSheet("font-size: 24px; color: white;")
        text_lbl = QLabel("Recent System Activity")
        text_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: white;")
        
        title_layout.addWidget(icon_lbl)
        title_layout.addWidget(text_lbl)
        title_layout.addStretch()
        # Search Bar for Recent Activity
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search History...")
        self.search_bar.setFixedWidth(280)
        self.search_bar.setObjectName("SearchBar") # Matches Sunken capsule in Image 2
        self.search_bar.textChanged.connect(self.on_search)
        title_layout.addWidget(self.search_bar)
        history_layout.addWidget(title_header)

        # Table Implementation
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Module", "Operation", "User", "Status"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Row Hover Support
        self.delegate = RowHoverDelegate(self.table)
        self.table.setItemDelegate(self.delegate)
        self.table.setMouseTracking(True)
        self.table.cellEntered.connect(self.handle_hover)

        self.table.setRowCount(0)
        self.table.setFixedHeight(280)
        history_layout.addWidget(self.table)

        activity_main_layout.addWidget(self.history_card)
        self.container_layout.addWidget(self.activity_container)
        self.container_layout.addStretch()

    def load_initial_data(self):
        self.load_history_data()
        self.update_notification_badge()

    def load_history_data(self, query=None):
        try:
            history = get_bill_history(query)
            # Limit displayed results for performance and clean UI
            display_rows = history if query else history[:5]
            self.table.setRowCount(0)
            for r, row in enumerate(display_rows):
                self.table.insertRow(r)
                # row format: (Timestamp, Customer, Desc, Type, Total)
                for c, val in enumerate(row):
                    item = QTableWidgetItem(str(val))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(r, c, item)
        except Exception:
            pass

    def on_search(self, text):
        """Trigger timer for debounced search."""
        self.search_timer.start(300) # 300ms delay to prevent database overload

    def perform_search(self):
        """Execute the actual search logic after timer timeout."""
        search_query = self.search_bar.text().strip()
        self.load_history_data(search_query)
    def update_notification_badge(self):
        if not hasattr(self, 'badge'): return
        
        sync_alerts_to_table()
        notes = get_notifications()
        count = len(notes)
        if count > 0:
            self.badge.setText(str(count))
            self.badge.show()
            self.badge.raise_()
            self.reposition_badge()
        else:
            self.badge.hide()

    def reposition_badge(self):
        # Calculate position relative to bell_icon
        if hasattr(self, 'bell_icon') and hasattr(self, 'badge'):
            icon_pos = self.bell_icon.mapTo(self, self.bell_icon.rect().topRight())
            # Shift badge to sit on top-right corner
            self.badge.move(icon_pos.x() - 15, icon_pos.y() - 5)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reposition_badge()

    def event(self, event):
        # Auto-Refresh: Catch WindowActivate (when window gets focus)
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.WindowActivate:
            self.update_notification_badge()
        return super().event(event)

    def show_notifications(self):
        # New Interactive Notification Popup
        self.note_win = NotificationPopup()
        
        # Connect signals for interactivity
        self.note_win.open_products.connect(self.open_product_manager)
        self.note_win.open_repairs.connect(self.manage_repairs)
        
        # Position logic
        icon_pos = self.bell_icon.mapToGlobal(self.bell_icon.rect().bottomLeft())
        final_pos = icon_pos
        # Aligned with new width (380)
        final_pos.setX(final_pos.x() - 345) 
        final_pos.setY(final_pos.y() + 10)
        
        self.note_win.move(final_pos)
        self.note_win.show()
        self.update_notification_badge()

    def handle_hover(self, row, column):
        self.delegate.hovered_row = row
        self.table.viewport().update()

    def leaveEvent(self, event):
        self.delegate.hovered_row = -1
        self.table.viewport().update()
        super().leaveEvent(event)

    def manage_products(self):
        # As requested: manage_products now opens the Form (AddStockWindow)
        self.as_win = AddStockWindow()
        # Connect signals for auto-refresh
        self.as_win.stock_added.connect(self.refresh_product_list)
        self.as_win.stock_added.connect(self.update_notification_badge)
        self.as_win.show()

    def open_product_manager(self):
        # This function now handles the List View (ProductsWindow)
        self.p_win = ProductsWindow()
        self.p_win.show()

    def refresh_product_list(self):
        # Refresh ProductsWindow data IF it is currently open
        if hasattr(self, 'p_win') and self.p_win.isVisible():
            self.p_win.load_data()

    def manage_repairs(self):
        # Yahan RepairsWindow (Manager List) open ho rahi hai
        self.r_win = RepairsWindow()
        self.r_win.show()

    def open_new_bill(self):
        # Yahan NewBillWindow (POS) open ho rahi hai
        self.nb_win = NewBillWindow()
        # Connect signal to refresh dashboard history
        self.nb_win.bill_printed.connect(self.refresh_dashboard_data)
        self.nb_win.show()

    def refresh_dashboard_data(self):
        sync_alerts_to_table() # Table update karein dashboard refresh par
        self.load_history_data()
        self.update_notification_badge()

    def open_new_repair(self):
        # Yahan NewRepairWindow (Form) open ho rahi hai
        self.nr_win = NewRepairWindow()
        # Connect signal for auto-refresh
        self.nr_win.repair_saved.connect(self.refresh_dashboard_data)
        self.nr_win.show()

    def open_login(self):
        if self.admin_logged_in:
            self.launch_admin_dashboard()
            return

        self.login_win = LoginForm(self)
        if self.login_win.exec():
            # Login Successful
            self.admin_logged_in = True
            self.launch_admin_dashboard()

    def launch_admin_dashboard(self):
        self.admin_dash = AdminDashboard()
        self.admin_dash.setStyleSheet(STYLE_SHEET)
        # Connect signals
        self.admin_dash.logout_clicked.connect(self.handle_logout)
        self.admin_dash.settings_updated.connect(self.load_settings)
        self.admin_dash.show()
        self.hide() # Hide instead of close to keep the app process alive

    def handle_logout(self):
        self.admin_logged_in = False
        self.show()

    def load_settings(self):
        settings = {}
        try:
            settings = get_app_settings()
            shop_name = settings.get("shop_name", "Kamran Electronics")
            if hasattr(self, 'shop_label'):
                self.shop_label.setText(shop_name)
            self.setWindowTitle(shop_name)
        except:
            pass
        return settings

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())