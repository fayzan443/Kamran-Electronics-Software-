# styles.py - Modern Soft Light Theme
STYLE_SHEET = """
QMainWindow, QDialog { 
    background-color: #F8FAFC; 
    font-family: 'Segoe UI Semibold', 'Inter', 'Segoe UI', Roboto, sans-serif;
}

/* --- MODERN GLASS/SOFT CARDS --- */
#MainContainer, .Card, #StatCard, #Navbar {
    background-color: #FFFFFF;
    border-radius: 24px;
    border: 1px solid #E2E8F0;
}

#AdminSidebar {
    background-color: #F1F5F9;
    border-right: 1px solid #E2E8F0;
}

/* --- REFINED INPUTS --- */
QLineEdit, QComboBox, QTimeEdit, #SearchBar {
    background-color: #F1F5F9;
    border-radius: 16px;
    padding: 14px 20px;
    border: 1px solid #E2E8F0;
    color: #1E293B;
    font-size: 15px;
    font-weight: 500;
}

QLineEdit:focus, QComboBox:focus {
    border: 2px solid #2563EB;
    background-color: #FFFFFF;
}

#SearchBar {
    border-radius: 30px;
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    font-size: 16px;
}

/* --- PREMIUM BUTTONS --- */
QPushButton {
    background-color: #FFFFFF;
    color: #334155;
    border-radius: 18px;
    padding: 14px 28px;
    font-weight: 700;
    font-size: 15px;
    border: 1px solid #E2E8F0;
}

QPushButton:hover {
    background-color: #EBF2FF;
    border: 1px solid #2563EB;
    color: #2563EB;
}

QPushButton:pressed {
    background-color: #DBEAFE;
    padding-top: 15px;
    padding-bottom: 13px;
}

/* Specific Style for Primary Action Buttons */
#BlueButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
}

#BlueButton:hover {
    background-color: #1D4ED8;
    color: #FFFFFF;
}

/* --- TABLES & LISTS --- */
QTableWidget, QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 20px;
    outline: none;
    font-size: 15px;
}

QHeaderView::section {
    background-color: #F8FAFC;
    padding: 16px;
    border: none;
    border-bottom: 2px solid #F1F5F9;
    font-weight: 800;
    color: #475569;
    text-align: center;
}

QTableWidget::item, QListWidget::item {
    border-bottom: 1px solid #F8FAFC;
    padding: 16px;
    color: #334155;
}

QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #EFF6FF;
    color: #2563EB;
    border-radius: 8px;
    font-weight: 700;
}

/* --- SCROLLBARS --- */
QScrollBar:vertical {
    border: none;
    background: #F1F5F9;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #CBD5E1;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #94A3B8;
}
"""
