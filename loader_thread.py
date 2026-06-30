from PyQt6.QtCore import QThread, pyqtSignal
from res_loader import ResourceLoader

class LoaderThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def run(self):
        loader = ResourceLoader(self.settings, progress_callback=self.progress.emit)
        self.finished.emit(loader)
