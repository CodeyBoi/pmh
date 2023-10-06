import os
from pypdf import PdfReader, PdfWriter, PageObject
from pypdf.papersizes import PaperSize

INFILEPATH = "songorder.txt"
NOTE_DIR = "Noter"


def main():
    title, instruments, songs = parse_input(INFILEPATH)

    outdir = title.replace(" ", "_")

    for instrument in instruments:
        outpath = f"{outdir}/{instrument}.pdf".replace(" ", "_")
        writer = PdfWriter()
        song_pairs = [(songs[i], songs[i + 1]) for i in range(0, len(songs), 2)]
        for song1, song2 in song_pairs:
            merged_page = PageObject.create_blank_page(
                width=PaperSize.A4.width, height=PaperSize.A4.height
            )
            page1 = get_pdf_page(instrument, song1)
            page2 = get_pdf_page(instrument, song2)
            
            
    
            # # TODO: Handle pngs
            # inpath = f"{NOTE_DIR}/{song}/{instrument}.pdf".replace(" ", "_")
            # if not os.path.exists(inpath):
            #     print(f"Varning: låten {song} saknar noter för {instrument}")
            #     continue
            reader = PdfReader(inpath)
            writer.addpages(reader.pages)


def parse_input(path):
    with open(INFILEPATH) as f:
        indata = "\n".join(f.readlines())
    start = indata.find("titel:") + 6
    end = indata.find("instrument:")
    title = indata[start:end].strip()

    start = end + 11
    end = indata.find("låtar:")
    instruments = [
        s.strip() for s in indata[start:end].replace(",", "\n").split("\n") if s.strip()
    ]

    start = end + 6
    songs = [
        s.strip() for s in indata[start:].replace(",", "\n").split("\n") if s.strip()
    ]
    return title, instruments, songs


def get_pdf_page(instrument, song):
    inpath = f"{NOTE_DIR}/{song}/{instrument}.pdf"
    if not os.path.exists(inpath):
        print(f"Varning: låten {song} saknar noter för {instrument}")
        return None
    return PdfReader(inpath).pages[0]


def merge_pdfs


if __name__ == "__main__":
    main()
