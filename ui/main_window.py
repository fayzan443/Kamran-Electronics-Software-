import sys
import os
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QPushButton, 
                             QLabel, QHBoxLayout, QFrame, QGridLayout, QTableWidget, 
                             QHeaderView, QGraphicsDropShadowEffect, QApplication, 
                             QTableWidgetItem, QStyledItemDelegate, QStyle, QAbstractItemView, QLineEdit)
from PyQt6.QtCore import Qt, QSize, QTimer, QByteArray
from PyQt6.QtSvg import QSvgRenderer
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
from utils.shared import RowHoverDelegate
# --- PROFESSIONAL SVG ICON LIBRARY ---
ICONS = {
    "repair": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>',
    "bill": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/><path d="M21 11.5L19 9.5L14 14.5L10 10.5L13 7.5L21 15.5"/><path d="M12 11h4"/><path d="M12 15h4"/><path d="M12 19h4"/><path d="M8 11h.01"/><path d="M8 15h.01"/><path d="M8 19h.01"/></svg>',
    "stock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>',
    "manager": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/><path d="M15 10a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z"/></svg>',
    "bolt": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg>',
    "bell": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
    "admin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/></svg>',
    "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'
}

def get_svg_icon(svg_str, color="white", size=QSize(32, 32)):
    from PyQt6.QtGui import QIcon, QPixmap
    svg_data = svg_str.replace('currentColor', color)
    renderer = QSvgRenderer(QByteArray(svg_data.encode('utf-8')))
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

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

    def setup_navbar(self):
        self.navbar = QFrame()
        self.navbar.setObjectName("Navbar")
        self.navbar.setFixedHeight(105) 
        self.navbar.setStyleSheet("""
            #Navbar { 
                background-color: #2563EB; 
                border-bottom-left-radius: 35px; 
                border-bottom-right-radius: 35px;
                border: none;
            }
        """)
        self.navbar_layout = QHBoxLayout(self.navbar)
        self.navbar_layout.setContentsMargins(45, 0, 45, 0)
        
        self.logo_label = QLabel()
        self.logo_label.setPixmap(get_svg_icon(ICONS["bolt"], color="white", size=QSize(40, 40)).pixmap(40, 40))
        self.logo_label.setStyleSheet("padding: 5px;")
        
        self.shop_label = QLabel(self.app_settings.get("shop_name", "Kamran Electronics"))
        self.shop_label.setObjectName("ShopName")
        self.shop_label.setStyleSheet("font-size: 30px; font-weight: 800; color: white;")
        
        # Bell & Badge
        self.bell_icon = QPushButton()
        self.bell_icon.setIcon(get_svg_icon(ICONS["bell"], color="white", size=QSize(24, 24)))
        self.bell_icon.setIconSize(QSize(24, 24))
        self.bell_icon.setFixedSize(55, 55)
        self.bell_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bell_icon.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.18); 
                border-radius: 27px; 
                border: 1px solid rgba(255, 255, 255, 0.25);
            }
            QPushButton:hover { background: rgba(255, 255, 255, 0.3); border: 2px solid white; }
        """)
        self.bell_icon.clicked.connect(self.show_notifications)
        
        # Initialize Badge
        self.badge = QLabel("0", self)
        self.badge.setFixedSize(22, 22)
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setStyleSheet("background-color: #ff4757; color: white; border-radius: 11px; font-weight: bold; border: 2px solid white; font-size: 10px;")
        self.badge.hide()
        
        # Removed 'New Bill' as requested to keep navbar clean
        
        self.btn_admin = QPushButton()
        self.btn_admin.setToolTip("Admin Panel Access")
        self.btn_admin.setIcon(get_svg_icon(ICONS["admin"], color="white", size=QSize(28, 28)))
        self.btn_admin.setIconSize(QSize(28, 28))
        self.btn_admin.setFixedSize(55, 55)
        self.btn_admin.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_admin.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.18); 
                border-radius: 27px; # Perfect circle
                border: 1.5px solid rgba(255, 255, 255, 0.25);
            }
            QPushButton:hover { 
                background-color: white; 
                border: 2px solid white;
            }
        """)
        # Specific hover icon color change is slightly harder without sub-classing, 
        # so I'll use a sophisticated style that works well.
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
        actions_layout.setContentsMargins(45, 45, 45, 25)
        
        self.grid = QGridLayout()
        self.grid.setSpacing(30)
        
        # Consistent Card Style Template
        card_qss = """
            QPushButton {{
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #E2E8F0;
                border-radius: 20px;
                font-size: 20px;
                font-weight: 800;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                border: 2px solid {primary};
                color: {primary};
            }}
        """

        # Row 1: 3 Main Cards (Each spans 2 of 6 columns)
        row1 = [(" New Repair", "repair", self.open_new_repair), 
                (" New Bill", "bill", self.open_new_bill), 
                (" Add Stock", "stock", self.manage_products)]
        for i, (text, icon_key, func) in enumerate(row1):
            btn = QPushButton(text)
            btn.setIcon(get_svg_icon(ICONS[icon_key], color="#2563EB", size=QSize(30, 30)))
            btn.setIconSize(QSize(30, 30))
            btn.setFixedHeight(135)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(card_qss.format(hover_bg="#EFF6FF", primary="#2563EB"))
            btn.clicked.connect(func)
            self.grid.addWidget(btn, 0, i * 2, 1, 2)
        
        # Row 2: 2 Manager Cards (Each spans 3 of 6 columns)
        btn_stock = QPushButton(" Product Stock Manager")
        btn_stock.setIcon(get_svg_icon(ICONS["manager"], color="#0F766E", size=QSize(30, 30)))
        btn_stock.setIconSize(QSize(30, 30))
        btn_stock.setFixedHeight(135)
        btn_stock.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_stock.setStyleSheet(card_qss.format(hover_bg="#F0FDFA", primary="#0F766E"))
        btn_stock.clicked.connect(self.open_product_manager)
        
        btn_repair = QPushButton(" Repairing Manager")
        btn_repair.setIcon(get_svg_icon(ICONS["repair"], color="#0F766E", size=QSize(30, 30)))
        btn_repair.setIconSize(QSize(30, 30))
        btn_repair.setFixedHeight(135)
        btn_repair.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_repair.setStyleSheet(card_qss.format(hover_bg="#F0FDFA", primary="#0F766E"))
        btn_repair.clicked.connect(self.manage_repairs)

        # Exact half-width alignment
        self.grid.addWidget(btn_stock, 1, 0, 1, 3) # Row 1, Col 0, spans 3
        self.grid.addWidget(btn_repair, 1, 3, 1, 3) # Row 1, Col 3, spans 3
        
        actions_layout.addLayout(self.grid)
        self.container_layout.addWidget(self.actions_area)

    def setup_activity(self):
        self.activity_container = QFrame()
        self.activity_container.setObjectName("ActivityContainer") 
        activity_main_layout = QVBoxLayout(self.activity_container)
        activity_main_layout.setContentsMargins(40, 20, 40, 40)
        activity_main_layout.setSpacing(0)

        # Activity Content Card
        self.history_card = QFrame()
        self.history_card.setObjectName("MainContainer")
        history_layout = QVBoxLayout(self.history_card)
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_layout.setSpacing(0)

        # Header Title
        title_header = QFrame()
        title_header.setFixedHeight(80)
        title_header.setObjectName("Navbar") 
        title_header.setStyleSheet("""
            #Navbar { 
                background-color: #F1F5F9; 
                border-top-left-radius: 20px; 
                border-top-right-radius: 20px;
                border-bottom: 2px solid #E2E8F0;
            }
        """)
        title_layout = QHBoxLayout(title_header)
        title_layout.setContentsMargins(35, 0, 35, 0)
        
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_icon(ICONS["clock"], color="#1E293B", size=QSize(28, 28)).pixmap(28, 28))
        text_lbl = QLabel("Recent System Activity")
        text_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #1E293B;")
        
        title_layout.addWidget(icon_lbl)
        title_layout.addWidget(text_lbl)
        title_layout.addStretch()
        # Search Bar for Recent Activity
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search History...")
        self.search_bar.setFixedWidth(350)
        self.search_bar.setFixedHeight(50)
        self.search_bar.setObjectName("SearchBar") 
        self.search_bar.textChanged.connect(self.on_search)
        title_layout.addWidget(self.search_bar)
        history_layout.addWidget(title_header)

        # Table Implementation
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Customer Name", "User (Repair or Stock)", "Product Name", "Total Bill", "Date & Time"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(65) # Large clear rows
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
    sys.exit(app.exec())