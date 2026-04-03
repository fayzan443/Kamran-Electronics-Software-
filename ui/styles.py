# styles.py - Fully Neumorphic Premium Theme (Image 2 Inspired)
STYLE_SHEET = """
QMainWindow, QDialog { 
    background-color: #F0F2F5; 
    font-family: 'Poppins', 'SF Pro Display', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}

/* --- NEUMORPHIC RAISED CARDS --- */
#MainContainer, .Card, #StatCard, #Navbar {
    background-color: #FFFFFF;
    border-radius: 25px;
    border: 1px solid rgba(255, 255, 255, 0.6);
}

#AdminSidebar {
    background-color: #F0F2F5;
    border-right: none;
}

/* --- SUNKEN (RECESSED) INPUTS & COMBOBOXES --- */
QLineEdit, QComboBox, QTimeEdit, #SearchBar {
    background-color: #E6E9EE;
    border-radius: 22px;
    padding: 12px 20px;
    border: 1px solid #D1D9E6;
    color: #44474B;
    font-size: 14px;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #3A8DFF;
    background-color: #FFFFFF;
}

/* Capsule Search Bar specifically */
#SearchBar {
    border-radius: 25px;
    background-color: #FFFFFF;
    border: 2px solid #E0E0E0;
}

/* --- NEUMORPHIC PILLOW BUTTONS --- */
QPushButton {
    background-color: #FFFFFF;
    color: #44474B;
    border-radius: 20px;
    padding: 12px 25px;
    font-weight: 600;
    font-size: 14px;
    border: 1px solid #E0E0E0;
}

QPushButton:hover {
    background-color: #F8F9FA;
    border: 1px solid #3A8DFF;
    color: #3A8DFF;
}

QPushButton:pressed {
    background-color: #E6E9EE;
    padding-top: 14px;
    padding-bottom: 10px;
}

/* Special Case for Sidebar Buttons */
#AdminSidebar QPushButton {
    text-align: left;
    background-color: transparent;
    border: none;
    color: #636E72;
}

#AdminSidebar QPushButton:hover {
    background-color: #FFFFFF;
    border-radius: 15px;
    color: #1E293B;
}

#AdminSidebar QPushButton#ActiveNav {
    background-color: #FFFFFF;
    border-radius: 15px;
    color: #1E293B;
    font-weight: 800;
}

/* --- TABLES & LISTS --- */
QTableWidget, QListWidget {
    background-color: #FFFFFF;
    border: none;
    border-radius: 20px;
    outline: none;
}

QHeaderView::section {
    background-color: #FFFFFF;
    padding: 15px;
    border: none;
    border-bottom: 2px solid #F0F2F5;
    font-weight: 800;
    color: #1E293B;
    text-align: center;
}

QTableWidget::item, QListWidget::item {
    border-bottom: 1px solid #F0F2F5;
    padding: 15px;
    color: #44474B;
}

QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #3A8DFF10;
    color: #3A8DFF;
    border-radius: 10px;
}

/* --- SCROLLBARS --- */
QScrollBar:vertical {
    border: none;
    background: #F0F2F5;
    width: 10px;
    border-radius: 5px;
    margin: 0px 2px 0px 2px;
}

QScrollBar::handle:vertical {
    background: #D1D9E6;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #3A8DFF50;
}

/* --- TABS --- */
QTabWidget::pane {
    border: none;
    background: #FFFFFF;
    border-radius: 25px;
}

QTabBar::tab {
    background: transparent;
    color: #636E72;
    padding: 12px 30px;
    font-weight: 600;
    margin-right: 10px;
}

QTabBar::tab:selected {
    background: #FFFFFF;
    border-radius: 15px;
    color: #1E293B;
}
"""
