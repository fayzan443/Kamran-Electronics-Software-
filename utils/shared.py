from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtGui import QColor

class RowHoverDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hovered_row = -1

    def paint(self, painter, option, index):
        # Full row hover effect
        if index.row() == self.hovered_row and not (option.state & QStyle.StateFlag.State_Selected):
            painter.fillRect(option.rect, QColor("#dfe6e9")) # Metal light grey
        super().paint(painter, option, index)

TIME_RANGES = {
    'Today': 'CURDATE()',
    'Last Week': 'NOW() - INTERVAL 7 DAY',
    'Last Month': 'NOW() - INTERVAL 30 DAY',
    'Last 6 Months': 'NOW() - INTERVAL 6 MONTH',
    '6 Months': 'NOW() - INTERVAL 6 MONTH',
    'All Time': "'1970-01-01'",
    'All': 'NOW() - INTERVAL 1 YEAR'
}
