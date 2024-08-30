import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
import time
class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Close Confirmation")
        self.setGeometry(100, 100, 400, 200)  # (x, y, width, height)

    def closeEvent(self, event):
        for i in range(10):
            print(i)
            time.sleep(0.5)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec())

