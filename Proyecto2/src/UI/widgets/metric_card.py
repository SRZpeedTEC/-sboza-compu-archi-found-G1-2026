from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class MetricCard(QFrame):

    def __init__(self, title, value, color):
        super().__init__()

        self.setObjectName("metricCard")

        self.setStyleSheet(f"""
        QFrame#metricCard {{
            background-color: {color};
        }}
        """)

        self.setMinimumHeight(120)

        layout = QVBoxLayout()

        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)

        self.title_label.setStyleSheet("""
            font-size: 11pt;
            font-weight: bold;
            color: #5a6484;
        """)

        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignCenter)

        self.value_label.setStyleSheet("""
            font-size: 24pt;
            font-weight: bold;
            color: #33415c;
        """)

        layout.addStretch()
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

        self.setLayout(layout)

    def set_value(self, value):
        self.value_label.setText(str(value))
    
