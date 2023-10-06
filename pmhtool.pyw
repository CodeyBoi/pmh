import os
from threading import Thread
from time import sleep
from tkinter.filedialog import askopenfilename, askdirectory
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from pypdf.papersizes import PaperSize
import tkinter as tk
from tkinter import StringVar, Toplevel, Text
from tkinter.ttk import Frame, Label, Entry, Button, Progressbar, Scrollbar

CONFIG_PATH = "C:/ProgramData/PMHMaker/config.txt"
if not os.path.exists(os.path.dirname(CONFIG_PATH)):
    os.makedirs(os.path.dirname(CONFIG_PATH))

MISSING_NOTE_FILENAME = "missing.pdf"

FRAME_PADDING = 6
PADDING = 6
TRANSLATE = Transformation().translate(0, PaperSize.A4.height / 2)
ROTATE = (
    Transformation().rotate(180).translate(PaperSize.A4.width, PaperSize.A4.height / 2)
)


class Config:
    DEFAULT = {
        "note_dir": "Noter",
        "instruments": [
            "Flute 1",
            "Flute 2",
            "Clarinet 1",
            "Clarinet 2",
            "Clarinet 3",
            "Alto Sax 1",
            "Alto Sax 2",
            "Tenor Sax",
            "Baritone Sax",
            "Horn 1",
            "Horn 2",
            "Horn 3",
            "Trumpet 1",
            "Trumpet 2",
            "Trumpet 3",
            "Trombone 1",
            "Trombone 2",
            "Trombone 3",
            "Euphonium",
            "Tuba",
            "Drumset",
            "Glockenspiel",
        ],
    }

    def __init__(self, path=CONFIG_PATH):
        config = Config.load(path)
        self.instruments = config["instruments"]
        self.note_dir = config["note_dir"]

    def load(path=CONFIG_PATH):
        if not os.path.exists(path):
            print(f"Varning: saknar konfigurationsfil {path}, använder standardvärden")
            return Config.DEFAULT
        config = {}
        with open(path) as f:
            for line in f:
                key, value = line.split(":")
                config[key.strip()] = value.strip()
        if set(config.keys()) != set(Config.DEFAULT.keys()):
            print(
                f"Varning: konfigurationsfil {path} har felaktigt format, använder standardvärden"
            )
            return Config.DEFAULT
        config["instruments"] = [
            s.strip() for s in config["instruments"].split(",") if s.strip()
        ]
        return config

    def save(self, path=CONFIG_PATH):
        with open(path, "w") as f:
            f.write(f"note_dir: {self.note_dir}\n")
            f.write(f"instruments: {','.join(self.instruments)}\n")


config = Config()


def main():
    start_gui()


def write_pdfs(title: str, instruments: list, songs: list):
    outdir = title.replace(" ", "_")
    os.makedirs(outdir, exist_ok=True)

    for instrument in instruments:
        writer = PdfWriter()

        for song1, song2 in gen_pairs(songs):
            page1 = get_pdf(instrument, song1)
            page2 = get_pdf(instrument, song2)
            writer.add_page(merge_pages(page1, page2))

        outpath = os.path.join(outdir, f"{instrument}.pdf".replace(" ", "_"))
        with open(outpath, "wb") as out:
            writer.write(out)
        print(f"Skrev {instrument} till {outpath}")

    print("Klar!")


def get_pdf(instrument: str, song: str):
    inpath = None
    for path in gen_paths(instrument, song):
        if os.path.exists(path) and os.path.isfile(path):
            inpath = path
            break

    exists = inpath is not None
    if not exists:
        print(f"Varning: {instrument} saknar noter för {song}")

    doc = (
        PdfReader(inpath)
        if exists
        else PdfReader(os.path.join(config.note_dir, MISSING_NOTE_FILENAME))
    )
    if len(doc.pages) > 1:
        print(
            f"Varning: {instrument} har mer än en sida till {song} (plockar bara första)"
        )

    return doc.pages[0]


def gen_paths(instrument: str, song: str):
    number = instrument.split(" ")[-1]
    path = lambda x: os.path.join(config.note_dir, song, f"{x.strip()}.pdf")
    yield path(instrument)
    no_num = instrument.removesuffix(number)
    yield path(no_num)
    yield path(no_num + " 1")
    yield path(no_num + " 2")
    yield path(no_num + " 3")
    yield path(no_num + " 4")


def gen_pairs(songs: list):
    for i in range(0, len(songs), 2):
        yield songs[i], songs[i + 1]


def merge_pages(page1: PageObject, page2: PageObject):
    outpage = PageObject.create_blank_page(
        width=PaperSize.A4.width, height=PaperSize.A4.height
    )
    outpage.merge_transformed_page(page1, TRANSLATE)
    outpage.merge_transformed_page(page2, ROTATE)
    return outpage


def parse_songs(path: str):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield line


def start_gui():
    root = tk.Tk()
    root.title("PMHTool")

    top_frame = Frame(root)
    top_frame.pack(
        side=tk.TOP,
        anchor=tk.NW,
        expand=True,
        padx=FRAME_PADDING,
        pady=FRAME_PADDING,
    )

    bottom_frame = Frame(root)
    bottom_frame.pack(
        side=tk.BOTTOM,
        anchor=tk.SE,
        expand=False,
        padx=FRAME_PADDING,
        pady=FRAME_PADDING,
    )

    title_input = StringVar()
    title_label = Label(top_frame, text="Titel:")
    title_entry = Entry(top_frame, textvariable=title_input, width=33)

    file_path = tk.StringVar()
    file_label = Label(top_frame, text="Låtordning:")
    file_entry = Entry(top_frame, textvariable=file_path, width=20, state="readonly")

    def browse_file():
        filetypes = (("PMH-låtordningsfiler", "*.txt"), ("Alla filer", "*.*"))
        path = askopenfilename(title="Välj låtordning", filetypes=filetypes)
        if not path:
            return
        file_path.set(path)
        file_entry.config(state=tk.NORMAL)
        file_entry.delete(0, tk.END)
        file_entry.insert(0, path.split("/")[-1])
        file_entry.config(state="readonly")

    file_browser = Button(top_frame, text="Välj fil...", command=browse_file)

    title_label.grid(row=0, column=0, sticky=tk.W)
    title_entry.grid(row=1, column=0, sticky=tk.W, columnspan=2)
    file_label.grid(row=2, column=0, sticky=tk.W)
    file_entry.grid(row=3, column=0, sticky=tk.W)
    file_browser.grid(row=3, column=1, sticky=tk.E, padx=PADDING)

    settings_button = Button(
        bottom_frame, text="Inställningar...", command=lambda: open_settings(root)
    )

    def validate():
        title = title_entry.get()
        path = file_path.get()
        errors = []
        if not title:
            errors.append("Skriv in en titel.")
        if not path:
            errors.append("Välj en låtordningsfil.")
        if path and not os.path.exists(path):
            errors.append("Låtordningsfilen finns inte.")

        if errors:
            popup("\n".join(errors), parent=root)
            return False

        return True

    status_text = StringVar(value="Kör!")

    def run():
        if not validate():
            return

        title = title_entry.get()
        songs = list(parse_songs(file_path.get()))
        work_thread = Thread(
            target=lambda: write_pdfs(title, config.instruments, songs)
        )
        work_thread.start()

        while work_thread.is_alive():
            for i in range(30):
                if not work_thread.is_alive():
                    break
                if i % 10 == 0:
                    status_text.set("Jobbar." + "." * (i // 10))
                root.update_idletasks()
                sleep(0.05)
        status_text.set("Kör!")
        popup("Alla noter utskrivna!", parent=root)

    run_button = Button(bottom_frame, textvariable=status_text, command=run)

    settings_button.pack(side=tk.LEFT, padx=PADDING, pady=PADDING)
    run_button.pack(side=tk.RIGHT, padx=PADDING, pady=PADDING)

    # # DEBUG
    # title_entry.insert(0, "PMH 2021")
    # file_path.set("songorder.txt")
    # file_entry.insert(0, "songorder.txt")

    center_window(root)
    root.mainloop()


def open_settings(parent):
    win = Toplevel(parent)
    win.grab_set()
    win.wm_title("Inställningar")

    top_frame = Frame(win)
    top_frame.pack(
        side=tk.TOP,
        anchor=tk.NW,
        expand=True,
        padx=FRAME_PADDING,
        pady=FRAME_PADDING,
    )

    mid_frame = Frame(win)
    mid_frame.pack(
        side=tk.TOP,
        expand=True,
        padx=FRAME_PADDING,
        pady=FRAME_PADDING,
    )

    bottom_frame = Frame(win)
    bottom_frame.pack(
        side=tk.BOTTOM,
        anchor=tk.SE,
        expand=False,
        padx=FRAME_PADDING,
        pady=FRAME_PADDING,
    )

    note_dir_label = Label(top_frame, text="Notmapp:")
    note_dir_entry = Entry(top_frame, width=30)
    note_dir_entry.insert(0, config.note_dir)
    note_dir_entry.config(state="readonly")

    def browse_note_dir():
        path = askdirectory(title="Välj notmapp")
        if not path:
            return
        note_dir_entry.config(state=tk.NORMAL)
        note_dir_entry.delete(0, tk.END)
        note_dir_entry.insert(0, path)
        note_dir_entry.config(state="readonly")

    note_dir_button = Button(top_frame, text="Välj mapp...", command=browse_note_dir)

    note_dir_label.grid(row=0, column=0, sticky=tk.W)
    note_dir_entry.grid(row=1, column=0, sticky=tk.W)
    note_dir_button.grid(row=1, column=1, sticky=tk.E, padx=PADDING)

    instruments_label = Label(mid_frame, text="Instrument:")
    instruments_entry = Text(mid_frame, height=14, width=30)
    instruments_scroll = Scrollbar(mid_frame, command=instruments_entry.yview)
    instruments_entry["yscrollcommand"] = instruments_scroll.set
    instruments_entry.insert("1.0", "\n".join(config.instruments))

    instruments_label.pack(side=tk.TOP, anchor=tk.NW)
    instruments_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    instruments_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def save():
        config.note_dir = note_dir_entry.get()
        config.instruments = [
            s.strip()
            for s in instruments_entry.get("1.0", tk.END).replace(",", "\n").split("\n")
            if s.strip()
        ]
        config.save()
        win.destroy()

    save_button = Button(bottom_frame, text="Spara", command=save)
    cancel_button = Button(bottom_frame, text="Avbryt", command=win.destroy)

    save_button.pack(side=tk.RIGHT, padx=PADDING, pady=PADDING)
    cancel_button.pack(side=tk.LEFT, padx=PADDING, pady=PADDING)

    center_window(win, parent)


def center_window(win, parent=None):
    # place window in center of parent, if parent is None, place in center of screen
    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()
    has_parent = parent is not None
    if has_parent:
        parent.update_idletasks()
    winx = parent.winfo_x() if has_parent else 0
    winy = parent.winfo_y() if has_parent else 0
    parent_w = parent.winfo_width() if has_parent else win.winfo_screenwidth()
    parent_h = parent.winfo_height() if has_parent else win.winfo_screenheight()
    x = (parent_w // 2) - (w // 2) + winx
    y = (parent_h // 2) - (h // 2) + winy
    win.geometry("{}x{}+{}+{}".format(w, h, x, y))


def popup(msg="", parent=None, textvariable=None):
    popup = tk.Toplevel(parent)
    popup.overrideredirect(True)
    popup.config(relief=tk.GROOVE, borderwidth=5)
    popup.grab_set()
    if textvariable is None:
        textvariable = tk.StringVar()
        textvariable.set(msg)
    label = Label(popup, textvariable=textvariable, padding=PADDING)
    label.pack(side=tk.TOP, fill=tk.X, pady=PADDING)
    button = Button(popup, text="OK", command=popup.destroy)
    button.pack(side=tk.BOTTOM, pady=PADDING, padx=PADDING)
    center_window(popup, parent)
    popup.resizable(False, False)
    popup.mainloop()


if __name__ == "__main__":
    main()
