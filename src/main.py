import sys

from PyQt6.QtWidgets import QApplication

from DebugWindow import runWindow as debugWindow

# test commit

if __name__ == '__main__':
    app = QApplication([])
    debugWindow()
    sys.exit(app.exec())
