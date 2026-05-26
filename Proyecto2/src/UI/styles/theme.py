# Estilos globales de la interfaz PySide6.
STYLE = """
QMainWindow {
    background-color: #f4f7ff;
}

QWidget {
    font-family: Segoe UI;
    color: #44506b;
    font-size: 11pt;
}

QFrame#topCard {
    background:qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #7b8cff,
        stop:0.5 #b07cff,
        stop:1 #ff88b7
    );
    border-radius: 28px;
}

QFrame#mainCard {
    background-color: white;
    border-radius: 28px;
    border: 2px solid #edf0ff;
}

QFrame#metricCard {
    border-radius: 22px;
}

QLabel#mainTitle {
    color: white;
    font-size: 30pt;
    font-weight: bold;
}

QLabel#subtitle {
    color: rgba(255,255,255,0.85);
    font-size: 12pt;
}

QLabel#sectionTitle {
    font-size: 14pt;
    font-weight: bold;
    color: #5a67a5;
}

QPushButton {
    border: none;
    border-radius: 16px;
    padding: 12px;
    color: white;
    font-weight: bold;
    font-size: 11pt;
}

QPushButton:hover {
    opacity: 0.8;
}

QComboBox {
    background-color: rgba(255,255,255,0.95);
    border: 2px solid #e4e8ff;
    border-radius: 18px;
    padding: 14px;
    padding-left: 18px;
    font-size: 11pt;
    font-weight: bold;
    color: #5865a5;
    min-height: 24px;
}

QComboBox:hover {
    border: 2px solid #cfd8ff;
    background-color: white;
}

QComboBox::drop-down {
    border: none;
    width: 40px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 8px solid #7c88c9;
    margin-right: 14px;
}

QComboBox QAbstractItemView {
    background-color: white;
    border: 2px solid #e4e8ff;
    border-radius: 18px;
    padding: 10px;
    selection-background-color: #eef2ff;
    selection-color: #5a67a5;
    outline: none;
}

QTabWidget::pane {
    border: none;
}

QTabBar::tab {
    background-color: #eef1ff;
    padding: 14px 24px;
    border-top-left-radius: 18px;
    border-top-right-radius: 18px;
    margin-right: 10px;
    font-weight: bold;
    color: #6975b4;
}

QTabBar::tab:selected {
    background-color: white;
}

QPlainTextEdit {
    background-color: #fbfcff;
    border-radius: 20px;
    border: 2px solid #e5e9ff;
    padding: 14px;
    font-size: 11pt;
}

QTableWidget {
    background-color: white;
    border-radius: 20px;
    border: 2px solid #e5e9ff;
    gridline-color: #edf0ff;
}

QHeaderView::section {
    background-color: #e5eeff;
    border: none;
    padding: 10px;
    font-weight: bold;
    color: #55639a;
}

QListWidget {
    background-color: white;
    border-radius: 20px;
    border: 2px solid #e5e9ff;
    padding: 10px;
}

QScrollBar:vertical {
    background: rgba(255,255,255,0.7);
    width: 22px;
    margin: 12px 6px 12px 6px;
    border-radius: 11px;
}

QScrollBar::handle:vertical {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #8f7cff,
        stop:1 #ff7eb6
    );

    min-height: 80px;
    border-radius: 10px;
    border: 4px solid rgba(255,255,255,0.7);
}

QScrollBar::handle:vertical:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #7a68ff,
        stop:1 #ff63a6
    );
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    height: 0px;
    max-height: 0px;
    background: transparent;
}

QScrollBar:horizontal {
    background: rgba(255,255,255,0.7);
    height: 20px;
    margin: 6px 12px 6px 12px;
    border-radius: 10px;
}

"""

