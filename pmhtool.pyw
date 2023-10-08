import os
from threading import Thread
from time import sleep
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.font import Font
from pypdf import PdfReader, PdfWriter, PageObject, Transformation
from pypdf.papersizes import PaperSize
import tkinter as tk
from tkinter import StringVar, Toplevel, Text
from tkinter.ttk import Frame, Label, Entry, Button, Scrollbar

PROGRAMDATA_DIR = "C:/ProgramData/PMHMaker"
if not os.path.exists(PROGRAMDATA_DIR):
    os.makedirs(PROGRAMDATA_DIR)
CONFIG_PATH = os.path.join(PROGRAMDATA_DIR, "config.txt")
ERROR_PATH = os.path.join(PROGRAMDATA_DIR, "error.log")

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
        if config is None:
            print(
                f"Hittade ingen konfigurationsfil vid {path}, skapar ny fil med standardvärden"
            )
            config = Config.DEFAULT
        self.instruments = config["instruments"]
        self.note_dir = config["note_dir"]

    def load(path=CONFIG_PATH):
        if not os.path.exists(path):
            return None
        config = {}
        with open(path) as f:
            for line in f:
                key, value = line.split(":")
                config[key.strip()] = value.strip()
        if set(config.keys()) != set(Config.DEFAULT.keys()):
            print(
                f"Varning: konfigurationsfil {path} har felaktigt format, använder standardvärden"
            )
            return None
        config["instruments"] = [
            s.strip() for s in config["instruments"].split(",") if s.strip()
        ]
        return config

    def save(self, path=CONFIG_PATH):
        with open(path, "w") as f:
            f.write(f"note_dir: {self.note_dir}\n")
            f.write(f"instruments: {','.join(self.instruments)}\n")


def main():
    start_gui()


def write_pdfs(title: str, instruments: list, songs: list):
    outdir = title
    os.makedirs(outdir, exist_ok=True)
    write_song_order(outdir, songs)

    for instrument in instruments:
        writer = PdfWriter()

        for song1, song2 in gen_pairs(songs):
            page1 = get_pdf(instrument, song1)
            if song2:
                page2 = get_pdf(instrument, song2)
            else:
                page2 = PageObject.create_blank_page(
                    width=PaperSize.A5.height, height=PaperSize.A5.width
                )
            writer.add_page(merge_pages(page1, page2))

        outpath = os.path.join(outdir, f"{instrument}.pdf")
        with open(outpath, "wb") as out:
            writer.write(out)
        print(f"Skrev {instrument} till {outpath}")

    print("Klar!")


def get_pdf(instrument: str, song: str):
    missing = lambda: PdfReader(
        os.path.join(config.note_dir, MISSING_NOTE_FILENAME)
    ).pages[0]
    note_dir = os.path.join(config.note_dir, song)
    if not os.path.exists(note_dir):
        print(f"Varning: {instrument} saknar noter för {song}")
        return missing()

    pdfpath = get_pdf_path(instrument, song)
    if pdfpath is None:
        print(f"Varning: {instrument} saknar noter för {song}")
        return missing()

    doc = PdfReader(pdfpath)
    if len(doc.pages) > 1:
        print(
            f"Varning: {instrument} har mer än en sida till {song} (plockar bara första)"
        )

    return doc.pages[0]


def get_pdf_path(instrument: str, song: str):
    note_dir = os.path.join(config.note_dir, song)
    for filename in get_filenames(instrument):
        for f in os.listdir(note_dir):
            if filename.lower() in f.lower():
                return os.path.join(note_dir, f)
    return None


def write_song_order(title: str, songs: list):
    with open(os.path.join(title, "låtordning.txt"), "w") as f:
        for index, song in zip(get_indices(len(songs)), songs):
            f.write(f"{index}.\t{song}\n")


def get_filenames(instrument: str):
    number = instrument.split(" ")[-1]
    yield instrument.strip()
    no_num = instrument.removesuffix(number).strip()
    yield no_num
    yield no_num + " 1"
    yield no_num + " 2"
    yield no_num + " 3"
    yield no_num + " 4"


def gen_pairs(songs: list):
    for i in range(0, len(songs), 2):
        yield songs[i], songs[i + 1] if i + 1 < len(songs) else ""


def merge_pages(page1: PageObject, page2: PageObject):
    outpage = PageObject.create_blank_page(
        width=PaperSize.A4.width, height=PaperSize.A4.height
    )
    outpage.merge_transformed_page(page1, TRANSLATE)
    outpage.merge_transformed_page(page2, ROTATE)
    return outpage


def parse_songs(string: str):
    return [s.strip() for s in string.split("\n") if s.strip()]


def get_indices(n: int):
    for i in range((n + 1) // 2):
        for c in "ab":
            yield f"{i + 1}{c}"


def start_gui():
    root = tk.Tk()
    root.title("PMHTool")

    top_frame = frame(root)
    mid_frame = frame(root)
    bottom_frame = frame(root, expand=False, anchor=tk.E)

    title_entry = widget(top_frame, Entry(top_frame, width=25), label="Titel")

    songs_label = Label(mid_frame, text="Låtordning")
    songs_entry = Text(
        mid_frame,
        height=12,
        width=40,
        undo=True,
        maxundo=-1,
        font=Font(family="Segoe UI", size=9),
    )
    songs_scroll = Scrollbar(mid_frame, command=songs_entry.yview)
    songs_entry["yscrollcommand"] = songs_scroll.set

    songs_label.pack(side=tk.TOP, anchor=tk.NW)
    songs_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    songs_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    settings_button = Button(
        bottom_frame, text="Inställningar...", command=lambda: open_settings(root)
    )

    def validate():
        title = title_entry.get().strip()
        songs = parse_songs(songs_entry.get("1.0", tk.END))
        errors = []
        if not title:
            errors.append("Skriv in en titel.")

        if not songs:
            errors.append("Skriv in låtordning.")

        if errors:
            popup("\n".join(errors), parent=root)
            return False

        return True

    status_text = StringVar(value="Kör!")

    def run():
        if not validate():
            return

        title = title_entry.get()
        songs = parse_songs(songs_entry.get("1.0", tk.END))
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

    # DEBUG
    title_entry.insert(0, "PMH 2021")
    songs_entry.insert("1.0", "Blaze Away\nThe Great Escape\nNågot med å, ä, och ö\n")

    center_window(root)
    root.mainloop()


def open_settings(parent):
    win = Toplevel(parent)
    win.grab_set()
    win.wm_title("Inställningar")

    top_frame = frame(win)
    mid_frame = frame(win)
    bottom_frame = frame(win, expand=False, anchor=tk.E)

    note_dir_label = Label(top_frame, text="Notmapp")
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

    instruments_entry = widget(
        mid_frame,
        Text(
            mid_frame,
            height=14,
            width=40,
            undo=True,
            maxundo=-1,
            font=Font(family="Segoe UI", size=9),
        ),
        label="Instrument",
        side=tk.LEFT,
    )

    instruments_scroll = Scrollbar(mid_frame, command=instruments_entry.yview)
    instruments_entry["yscrollcommand"] = instruments_scroll.set
    instruments_entry.insert("1.0", "\n".join(config.instruments))

    instruments_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def save():
        config.note_dir = note_dir_entry.get()
        config.instruments = [
            s.strip()
            for s in instruments_entry.get("1.0", tk.END).split("\n")
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


def frame(
    parent,
    side=tk.TOP,
    anchor=tk.NW,
    expand=True,
    padx=FRAME_PADDING,
    pady=FRAME_PADDING,
):
    frame = Frame(parent)
    frame.pack(
        side=side,
        anchor=anchor,
        expand=expand,
        padx=padx,
        pady=pady,
    )
    return frame


def widget(
    parent,
    widget,
    label=None,
    side=tk.TOP,
    label_side=tk.TOP,
    anchor=tk.NW,
    expand=False,
):
    if label is not None:
        label_element = Label(parent, text=label)
        label_element.pack(side=label_side, anchor=anchor, expand=expand)
    widget.pack(side=side, anchor=anchor, expand=expand)
    return widget


if __name__ == "__main__":
    config = Config()
    main()
