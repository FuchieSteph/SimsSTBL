import shutil
from tkinter import filedialog
from tkinter.messagebox import showinfo

import customtkinter
import tksheet
from s4py.package import *

import csv
from definitions import LANGS, LANG_LIST
from libs import helpers
from libs.stbl import readStbl


class App(customtkinter.CTk):
    APP_NAME = "map_view_demo.py"

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.width = self.winfo_screenwidth()
        self.height = self.winfo_screenheight()
        center_x = int(self.width / 2 - self.width / 2)
        center_y = int(self.height / 2 - self.height / 2)

        self.title(self.APP_NAME)
        self.geometry(f'{self.width}x{self.height}+{center_x}+{center_y}')
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed

        self.frame_left = customtkinter.CTkFrame(master=self,
                                                 width=180,
                                                 corner_radius=0)

        self.frame_left.grid(row=0, column=0, sticky="nswe")
        self.frame_left.grid_rowconfigure(0, minsize=10)


        ####DEFINE LEFT FRAME######
        self.title = customtkinter.CTkLabel(master=self.frame_left,
                                            text="CustomTkinter",
                                            text_font=("Roboto Medium", -16))  # font name and size in px
        self.title.grid(row=1, column=0, pady=10, padx=10)

        self.combobox_lang = customtkinter.CTkComboBox(master=self.frame_left,
                                                       values=LANG_LIST,
                                                       command=self.define_lang)

        self.combobox_lang.set("Lang")  # set initial value
        self.combobox_lang.grid(row=2, column=0, pady=10, padx=20)

        self.button_open = customtkinter.CTkButton(master=self.frame_left,
                                                   text="Open package",
                                                   command=self.upload_file)

        self.button_open.grid(row=3, column=0, pady=10, padx=5)

        #####DEFINE RIGHT FRAME///////
        self.frame_right = customtkinter.CTkFrame(master=self)
        self.frame_right.grid(row=0, column=1, sticky="nswe", padx=20, pady=20)

        self.sheet = tksheet.Sheet(self.frame_right, width=800, height=600)
        self.sheet.grid()
        self.sheet.enable_bindings(("single_select",
                                    "row_select",
                                    "column_width_resize",
                                    "arrowkeys",
                                    "right_click_popup_menu",
                                    "rc_select",
                                    "rc_insert_row",
                                    "rc_delete_row",
                                    "copy",
                                    "cut",
                                    "paste",
                                    "delete",
                                    "undo",
                                    "edit_cell"))

        self.STRINGS = {}
        self.DATA = []
        self.lang = ''
        self.filepath = ''
        self.package = None

    def define_lang(self, choice):
        self.lang = choice
        print(self.lang)

    def upload_file(self):
        global img
        f_types = [('Package File', '*.package')]
        self.filepath = filedialog.askopenfilename(filetypes=f_types)

        try:
            self.readPackage()
        except:
            print('Error while reading file')
            raise

    def readPackage(self):
        dbfile = open_package(self.filepath)

        self.STRINGS = {}
        self.DATA = []

        for entry in dbfile.scan_index(None):
            idx = dbfile[entry]
            type = "%08x" % idx.id.type
            instance = "%016x" % idx.id.instance
            lang = instance[:2]

            if type != "220557da" or (lang != LANGS[self.lang] and lang != LANGS['ENG_US']):
                continue

            content = idx.content
            current_lang = list(LANGS.keys())[list(LANGS.values()).index(lang)]
            stbl = readStbl(content, self.DATA)

            self.package = idx
            self.KEYS = stbl[0]
            self.DATA = stbl[1]

        self.initSheets()

    def initSheets(self):
        self.sheet.set_sheet_data(self.DATA)
        self.sheet.set_all_cell_sizes_to_text()
        self.sheet.redraw(redraw_header=True, redraw_row_index=True)

        self.button_2 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Load translation",
                                                command=self.import_csv)
        self.button_2.grid(row=4, column=0, padx=10, pady=5)

        self.button_3 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Export to CSV",
                                                command=self.export_csv)
        self.button_3.grid(row=5, column=0, padx=10, pady=5)

        self.button_4 = customtkinter.CTkButton(master=self.frame_left,
                                                text="Export translation",
                                                command=self.export_translation)
        self.button_4.grid(row=6, column=0, padx=10, pady=5)

    def export_csv(self):
        self.export_path = filedialog.askdirectory()

        try:
            filename = self.filepath.split('/')[-1].split('.')[0]
        except:
            filename = "translation"

        with open(self.export_path + "/" + filename + '.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';', quotechar='"', quoting=csv.QUOTE_ALL)
            writer.writerow(['KEY', 'EN', 'FR'])
            writer.writerows(self.DATA)

        showinfo('Success', 'The file has correctly been exported')

    def import_csv(self):
        import_path = filedialog.askopenfile()

        with import_path as csvfile:
            spamreader = csv.reader(csvfile, delimiter=';', quotechar='|')
            for row in spamreader:
                print(', '.join(row))

    def export_translation(self):
        self.export_path = filedialog.askdirectory()

        try:
            filename = self.filepath.split('/')[-1].split('.')[0]
        except:
            filename = "translation"

        dbfile2 = open_package(self.export_path + "/" + filename + '.package'.replace('.package', '_'+self.lang+'.package'), 'w')
        data = self.sheet.get_column_data(1, return_copy=True)

        i = 0
        totalchar = 0

        for key in self.KEYS:
            totalchar += len(data[i].encode('utf-8'))
            i = i + 1

        f = helpers.BinPacker(bytes())
        f.put_strz('STBL')
        f.put_uint16(5)  # Version
        f.put_uint8(0)  # Compressed
        f.put_uint64(len(self.KEYS))  # numEntries
        f.put_uint16(0)  # Flag
        f.put_uint32(totalchar)  # mnStringLength

        i = 0
        for key in self.KEYS:
            nbChar = len(data[i].encode('utf-8'))
            print(nbChar)
            f.put_uint32(key)  # HASH
            f.put_uint8(0)  # FLAG
            f.put_uint16(nbChar)  # NB CHAR
            f.put_strz(data[i])  # DATA
            if i == 0:
                print(f.raw.getvalue())

            i = i + 1

        f.raw.seek(0)
        dbfile2.put(self.package.id, f.raw.getvalue())
        dbfile2.commit()

        showinfo('Success', 'The file has correctly been exported')

    def on_closing(self, event=0):
        self.destroy()
        exit()

    def start(self):
        # self.readPackage()
        self.mainloop()


if __name__ == "__main__":
    app = App()
    app.start()
