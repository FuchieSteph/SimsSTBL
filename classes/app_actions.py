import os
import sys
import traceback

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import *
from s4py.package import *
from translatepy.translators import GoogleTranslateV2

import csv

from classes.settings import SettingsWindow
from helpers.definitions import LANG_LIST
from classes.package import Package


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    """
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(str)


class Worker(QRunnable):
    """
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    """

    def __init__(self, fn, file, lang, path):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.signals = WorkerSignals()
        self.progress = self.signals.progress
        self.file = file
        self.lang = lang
        self.path = path

    @pyqtSlot()
    def run(self):
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(self.progress, self.file, self.lang, self.path)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


class App_Actions:
    def checkDatabase(self):
        filename = self.package.getFilename()

        if os.path.exists(self.dirpath + '/' + filename + '_' + self.package.lang + '.json'):
            if self.raiseMessage('A translation was detected in the database : ', 'Would you like to load it ?',
                                 0) == 0:
                return False

            else:
                return self.dirpath + '/' + filename + '_' + self.package.lang + '.json'

        elif os.path.exists(self.dirpath + '/' + filename + '_auto_' + self.package.lang + '.json'):
            if self.raiseMessage('A Google translation was detected in the database : ',
                                 'Would you like to load it ?', 0) == 0:
                return False
            else:
                return self.dirpath + '/' + filename + '_auto_' + self.package.lang + '.json'

    def export_package(self):
        export_path = self.package.filepath.replace('.package', '_' + self.package.lang + '.package')

        if not self.package.isQuick:
            export_path = QFileDialog.getSaveFileName(self, 'Open file', export_path, "Package (*.package)")[0]
            if export_path == '':
                return

            self.write_logs('Translation package exported : ' + export_path)

        self.package.export(export_path)

    def export_translation(self):
        name = self.package.getFilename()
        export_path = QFileDialog.getSaveFileName(self, 'Export translation to CSV', name + '.csv', "CSV (*.csv)")

        if export_path[0] == '':
            return

        with open(export_path[0], 'w', newline='', encoding='UTF-8') as f:
            writer = csv.writer(f)
            writer.writerow(['KEY', 'EN', 'FR'])
            writer.writerows(self.package.model._data)
            f.close()

        self.write_logs('Translation exported: ' + export_path[0])

    def import_csv(self):
        import_path = QFileDialog.getOpenFileName(self, 'Open file', '', "CSV (*.csv)")

        if import_path[0] == '':
            return

        with open(import_path[0], 'r') as f:
            self.package.load_csv_translation(csv.reader(f, delimiter=';'))

    def load_package(self):
        path = \
            QFileDialog.getOpenFileName(self, 'Open the package to translate', self.sourcepath,
                                        "Packages files (*.package)")[0]

        if path == '':
            return

        lang = \
            QInputDialog.getItem(self, "Language Selection", "Select the lang to load", LANG_LIST, 5, False)[0]

        self.package = Package(path, lang, False)

        if self.package.isLoaded == 'choice':
            choice = self.raiseMessage('This package doesn\'t contain the following strings : ' + self.package.lang,
                                       'Would you like to copy the English strings ?', 0)

        elif self.package.isLoaded:
            self.sourcepath = self.package.filepath
            self.write_logs(self.package.filepath + ' loaded', True)
            self.load_table(self.package)

        else:
            self.raiseMessage('The file doesn\'t contain any string to translate, please try with another file', '', 1)

    def load_translation(self, path=None):

        if not path:
            path = QFileDialog.getOpenFileName(self, 'Load a translation file', self.dirpath + '/', "Json (*.json)")[
                0]

        if path == '':
            return

        if not self.package.load_translation(path):
            self.raiseMessage('The file is invalid, please try with another file', '', 1)

        else:
            self.write_logs('Translation loaded: ' + path)

    def save_translation(self):
        name = self.package.getFilename()

        if not self.package.isQuick:
            export_path = QFileDialog.getSaveFileName(self, 'Save a translation', self.settings.value(
                "DatabasePath") + '/' + name + '_' + self.package.lang + '.json',
                                                      "JSON (*.json)")[0]

            if export_path == '':
                return

            self.write_logs('Translation saved: ' + export_path)

        else:
            export_path = self.settings.value("DatabasePath") + '/' + name + '_auto_' + self.package.lang + '.json'

        self.package.save_translation(export_path)

    def progress_fn(self, n):
        self.write_logs("%s done" % n)

    def print_output(self, s):
        self.write_logs(s)

    def thread_complete(self):
        self.write_logs('Package translation complete')

    def load_from_package(self):
        path = \
            QFileDialog.getOpenFileName(self, 'Open the package to use', self.sourcepath,
                                        "Packages files (*.package)")[0]

        if path == '':
            return

        package = Package(path, self.package.lang, True)
        if package.isLoaded:
            self.package.load_package_translation(package)
            self.write_logs('Translation loaded')

    def translate(self, progress_callback, file, lang, path):
        package = Package(os.path.join(path, file), lang, True)

        if package.isLoaded:
            self.sourcepath = package.filepath
            self.load_table(package)

            translator = GoogleTranslateV2()
            n = 1

            for data in package.model._data:

                try:
                    results = translator.translate(data[1], 'fr')
                    data[2] = results.result
                except:
                    pass

                progress_callback.emit(file + ' ' + str(n) + "/" + str(len(package.model._data)))
                n = n + 1

            package.save_translation(
                self.settings.value("DatabasePath") + '/' + package.getFilename() + '_auto_' + package.lang + '.json')
            package.export(package.filepath.replace('.package', '_' + package.lang + '.package'))

        else:
            return 'No strings found, file skipped: ' + file

        return file + ' correctly translated'

    def translate_folder(self):
        path = \
            QFileDialog.getExistingDirectory(self, 'Select the folder to translate', self.sourcepath)

        if path == '':
            return

        lang = QInputDialog.getItem(self, "Language Selection", "Select the lang", LANG_LIST, 5, False)[0]

        if lang == '':
            self.write_logs('No lang was selected, translation abandoned', True)
            return

        self.write_logs('Translation started... Please wait...', True)

        for file in os.listdir(path):
            if file.endswith(".package"):
                # Pass the function to execute
                worker = Worker(self.translate, file, lang, path)
                worker.signals.result.connect(self.print_output)
                worker.signals.finished.connect(self.thread_complete)
                worker.signals.progress.connect(self.progress_fn)

                # Execute
                self.threadpool.start(worker)

    def update_settings(self):
        if self.params is None:
            self.params = SettingsWindow()
        self.params.show()
        self.sourcepath = self.settings.value("SourcePath")
