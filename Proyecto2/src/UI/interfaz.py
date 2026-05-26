import sys
from pathlib import Path

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.UI.app import main
from src.UI.main_window import MainWindow
from src.UI.pages.comparison_page import ComparisonPage
from src.UI.pages.processor_page import ProcessorPage
from src.UI.widgets.datapath_view import DatapathWidget
from src.UI.widgets.metric_card import MetricCard

__all__ = [
    "main",
    "MainWindow",
    "ProcessorPage",
    "ComparisonPage",
    "DatapathWidget",
    "MetricCard",
]


if __name__ == "__main__":
    sys.exit(main())
