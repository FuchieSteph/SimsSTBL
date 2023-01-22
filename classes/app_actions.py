import os
import sys
import traceback

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import *
from s4py.package import *
from translatepy.translators import GoogleTranslateV2

import csv

from classes.dictionnaries import DictionnariesWindow
from classes.search_replace import SearchReplaceWindow
from classes.settings import SettingsWindow
from helpers.definitions import *
from classes.package import Package
from helpers.helpers import relative_path


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
        export_path = self.package.getFilePath() + '/!' + self.package.getFilename() + '_' + self.package.lang + '.package'

        if not self.package.isMulti:
            if not self.package.isQuick:
                export_path = QFileDialog.getSaveFileName(self, 'Open file', export_path, "Package (*.package)")[0]
                if export_path == '':
                    return

                self.write_logs('Translation package exported : ' + export_path)

            self.package.export(False, export_path)

        else:
            for package in self.package.multipath:
                self.write_logs(package.getFilename() + ': translation exported')

                export_path = package.getFilePath() + '/!' + package.getFilename() + '_' + package.lang + '.package'
                package.export(False, export_path)

            self.raiseMessage('Export complete', '', 1)

    def export_replace_package(self):

        if not self.package.isMulti:
            self.package.export(True, None)
            self.write_logs('Translation package saved')

        else:
            for package in self.package.multipath:
                package.export(True, None)
                self.write_logs(package.getFilename() + ': translation exported')

            self.raiseMessage('Export complete', '', 1)

    def export_csv(self):
        name = self.package.getFilename()
        export_path = QFileDialog.getSaveFileName(self, 'Export translation to CSV', name + '.csv', "CSV (*.csv)")

        if export_path[0] == '':
            return

        with open(export_path[0], 'w', newline='', encoding='UTF-8') as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(['KEY', 'INSTANCE', 'INSTANCE', 'EN', 'FR', 'STATE'])
            writer.writerows(self.package.model._data)
            f.close()

        self.write_logs('Translation exported: ' + export_path[0])

    def import_csv(self):
        import_path = QFileDialog.getOpenFileName(self, 'Open file', '', "CSV (*.csv)")

        if import_path[0] == '':
            return

        with open(import_path[0], 'r', newline='', encoding='utf-8') as f:
            self.package.load_csv_translation(csv.reader(f, delimiter=';'))

    def load_package(self, path=False):
        if path == False:
            path = \
                QFileDialog.getOpenFileName(self, 'Open the package to translate', self.sourcepath,
                                            "Packages files (*.package)")[0]

            if path == '':
                return

        lang, ok = QInputDialog.getItem(self, "Language Selection", "Select the lang to load", LANG_LIST, 5, False)

        if not ok:
            return

        self.package = Package(path, lang, False)

        if self.package.isLoaded and len(self.package.DATA) > 0:
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

    def save_translation(self, ask=False, db=False):
        name = self.package.getFilename()

        if db == True:
            export_path = self.dbfolder + '/' + 'db_' + self.package.lang + '.json'


        elif self.package.isQuick:
            export_path = self.settings.value(
                "DatabasePath") + '/' + name + '_auto_' + self.package.lang + '.json'

        elif (not self.package.isQuick and self.package.database_path is None) or ask == True:
            export_path = QFileDialog.getSaveFileName(self, 'Save a translation', self.settings.value(
                "DatabasePath") + '/' + name + '_' + self.package.lang + '.json',
                                                      "JSON (*.json)")[0]

            if export_path == '':
                return

            self.package.database_path = export_path
            self.write_logs('Translation saved: ' + export_path)

        else:
            export_path = self.package.database_path

        self.package.save_translation(export_path)
        self.write_logs('Translation Saved')

    def save_translation_as(self):
        self.save_translation(True)

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

        if path is not None:
            package = Package(os.path.join(path, file), lang, True)

        else:
            package = self.package

        if package.isLoaded:
            self.sourcepath = package.filepath

            if path is not None:
                self.load_table(package)

            translator = GoogleTranslateV2()
            n = 1

            for data in package.model._data:

                try:
                    if data[STATE_INDEX] == NO_STATE:
                        results = translator.translate(data[BASE_INDEX], 'fr')
                        data[TRANSLATION_INDEX] = results.result
                        data[STATE_INDEX] = TO_VALIDATE_STATE
                except:
                    pass

                progress_callback.emit(file + ' ' + str(n) + "/" + str(len(package.model._data)))
                n = n + 1

            if path is not None:
                package.save_translation(self.settings.value(
                    "DatabasePath") + '/' + package.getFilename() + '_auto_' + package.lang + '.json')
                package.export(False, package.filepath.replace('.package', '_' + package.lang + '.package'))
        else:
            return 'No strings found, file skipped: ' + file

        return file + ' correctly translated'

    def open_folder(self):
        path = \
            QFileDialog.getExistingDirectory(self, 'Select the folder to open', self.sourcepath)

        if path == '':
            return

        lang = QInputDialog.getItem(self, "Language Selection", "Select the lang", LANG_LIST, 5, False)[0]

        if lang == '':
            self.write_logs('No lang was selected, translation abandoned', True)
            return

        data = {}
        packages = []

        for subdir, dirs, files in os.walk(path):

            for file in files:
                if file.endswith(".package") and not file.startswith('!'):
                    self.write_logs('Opening :' + subdir + os.sep + file)

                    pack = Package(subdir + os.sep + file, lang, True)
                    if pack.isLoaded:
                        if file not in data:
                            data[file] = {}

                        data[file] = data[file] | pack.DATA[file]
                        packages.append(pack)
                        self.write_logs(subdir + os.sep + file + ': loaded')

        self.package = Package(os.path.join(path, os.path.dirname(path) + '.package'), lang, False, True,
                               [data, packages])

        self.load_table(self.package)

    def build_dictionnaries(self, source, trans):
        data = {}
        packages = []
        source_name = 'Strings_' + source + '.package'
        trans_name = 'Strings_' + trans + '.package'

        for subdir, dirs, files in os.walk(relative_path("database")):

            for file in files:
                if file == source_name or file == trans_name:
                    self.write_logs('Opening :' + subdir + os.sep + file)

                    pack = Package(subdir + os.sep + file, trans, True)

                    if pack.isLoaded:
                        if file not in data:
                            data[file] = {}

                        data[file] = data[file] | pack.DATA[file]
                        packages.append(pack)
                        self.write_logs(subdir + os.sep + file + ': loaded')

            full_data = {}

            # We loop through the file & instances & merge the dictionnaries
            if source_name in data:
                full_data = data[source_name]

                for instance in data[trans_name].items():
                    if instance[0] in full_data:
                        for key in instance[1].items():
                            if key[0] in full_data[instance[0]]:
                                full_data[instance[0]][key[0]][TRANSLATION_INDEX] = key[1][TRANSLATION_INDEX]

        self.package = Package(os.path.join(relative_path("database"), 'db_' + trans + '.package'), trans, True, True,
                               [full_data, packages])

        self.load_table(self.package)
        self.save_translation(False, True)
        self.initTable()

    def show_settings(self):
        if self.params is None:
            self.params = SettingsWindow()
        self.params.show()
        self.params.buildClicked.connect(self.build_dictionnaries)
        self.params.submitClicked.connect(self.update_settings)

    def update_settings(self, trans, source):
        self.dirpath = trans
        self.sourcepath = source

    def search_replace(self):
        if self.search is None:
            self.search = SearchReplaceWindow()

        self.search.submitClicked.connect(self.process_search)
        self.search.show()

    def search_dict(self):
        if self.search_dict_w is None:
            self.search_dict_w = DictionnariesWindow()

        self.search_dict_w.show()

    def process_search(self, search, replace):
        nb = self.package.model.search_replace(search, replace)
        self.write_logs(str(nb) + ' rows updated')

    def translate_google(self):
        # Pass the function to execute
        worker = Worker(self.translate, self.package.getFilename(), self.package.lang, None)
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)

        # Execute
        self.threadpool.start(worker)
