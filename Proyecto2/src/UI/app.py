import sys
import os
import shutil
import sysconfig
import tempfile
from pathlib import Path


def _prepare_macos_qt_plugins() -> None:
    """Prepara plugins Qt en macOS cuando PySide6 no los encuentra solo."""
    if sys.platform != "darwin" or os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH"):
        return

    source = (
        Path(sysconfig.get_paths()["purelib"])
        / "PySide6"
        / "Qt"
        / "plugins"
        / "platforms"
    )
    if not source.exists():
        return

    target = Path(tempfile.gettempdir()) / "pyside6-qt-platforms" / "platforms"
    target.mkdir(parents=True, exist_ok=True)

    for plugin in source.glob("*.dylib"):
        destination = target / plugin.name
        if (
            not destination.exists()
            or plugin.stat().st_size != destination.stat().st_size
            or plugin.stat().st_mtime > destination.stat().st_mtime
        ):
            shutil.copyfile(plugin, destination)

    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(target)


_prepare_macos_qt_plugins()

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.UI.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
