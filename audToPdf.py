import sys
from pathlib import Path

import librosa.display
import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from fpdf import FPDF
from pypdf import PdfReader, PdfWriter
from pynput import keyboard

import pipeclient


debugOn = len(sys.argv) > 1 and sys.argv[1] == '--debug'
isPreSaved = False
exportsFolder = Path("tmp").absolute()
exportsFolder.mkdir(parents=True, exist_ok=True)
pc = pipeclient.PipeClient()

audioExport = str(exportsFolder / "audioExport.wav")
firstImageWave = str(exportsFolder / "first.png")
secondImageWave = str(exportsFolder / "second.png")


def pprint(text: str, level: int = 0) -> None:
    match level:
        case 1: print(f"\033[32m{text}\033[0m")
        case 2: print(f"\033[33m{text}\033[0m")
        case 3: print(f"\033[31m{text}\033[0m")
        case _: print(text)


def export_selected_audio() -> bool:
    pc.write(f'Export2: Filename="{audioExport}" NumChannels=1')

    response = pc.read()
    while response == '':      # busy waiting's fine -> won't take long + thread should continue only after A response is received
        response = pc.read()
    pprint(response, 2)

    return response.startswith("Exported to WAV format:")      # return False on failed export


def parse_image(default: bool) -> None:
    global isPreSaved
    color = '#0064be' if default else '#E07A5F'
    y, sr = librosa.load(audioExport, sr=None)
    x = np.linspace(0, 100, num=len(y))

    plt.figure(figsize=(8.0, 2.0))
    plt.plot(x, y, color=color, linewidth=1.75)
    plt.xlim(0, 100)
    imgPath = secondImageWave if default else firstImageWave

    if debugOn:
        plt.gca().set_facecolor('red')
    else:
        plt.axis('off')

    plt.savefig(imgPath, dpi=400, transparent=(not debugOn))
    if not default: isPreSaved = True
    plt.close()


def create_pdf() -> None:
    global isPreSaved
    PAGE_W = 275.1
    img_w = 240
    x = (PAGE_W - img_w) / 2

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()

    if not isPreSaved:
        pdf.image(str(secondImageWave), x=x, y=55, w=img_w, h=120)
    else:
        pdf.image(str(firstImageWave), x=x, y=40, w=img_w, h=80)
        pdf.image(str(secondImageWave), x=x, y=104, w=img_w, h=80)
    isPreSaved = False

    tmpPdfPath = str(exportsFolder / "tmp.pdf")
    pdf.output(tmpPdfPath)
    template = PdfReader("template.pdf")
    rimg = PdfReader(tmpPdfPath)
    writer = PdfWriter()
    templatePage = template.pages[0]
    imagePage = rimg.pages[0]

    if templatePage.rotation != 0:
        templatePage.transfer_rotation_to_content()
    if imagePage.rotation != 0:
        imagePage.transfer_rotation_to_content()

    templatePage.merge_page(imagePage)
    writer.add_page(templatePage)

    with open("output.pdf", "wb") as out:
        writer.write(out)

    pprint("================= ✓ Pdf created. ✓ =================", 1)


def on_export_to_png_pressed(default: bool) -> None:
    if export_selected_audio():
        parse_image(default)
        if default: create_pdf()
        else: pprint("========= ✓ Image saved, you can proceed ✓ =========", 1)
    else: pprint("Audio export has failed...", 3)


def on_img_reset_pressed() -> None:
    global isPreSaved
    isPreSaved = False
    pprint("============= ✓ Image has been reset ✓ =============", 2)


currentKeys = set()
SHORTCUTS = {
    frozenset({keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_vk(80)}): lambda: on_export_to_png_pressed(True),
    frozenset({keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_vk(79)}): lambda: on_export_to_png_pressed(False),
    frozenset({keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_vk(82)}): on_img_reset_pressed,
    frozenset({keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_vk(81)}): lambda: sys.exit(0)
}

def on_press(key, clear=currentKeys.clear()):
    currentKeys.add(key)
    currentKeys_str = {str(k) for k in currentKeys}

    for shortcut, callback in SHORTCUTS.items():
        shortcut_str = {str(k) for k in shortcut}

        if shortcut_str.issubset(currentKeys_str):
            currentKeys.clear()
            callback()


def on_release(key):
    if key in currentKeys:
        currentKeys.remove(key)


if __name__ == "__main__":
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()