import os
import sys
import subprocess
from pathlib import Path
import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import librosa
import librosa.display
from pynput import keyboard
from fpdf import FPDF
from pypdf import PdfReader, PdfWriter

debugOn = len(sys.argv) > 1 and sys.argv[1] == "--debug"

TONAME = None
FROMNAME = None
EOL = None
isPreSaved = False
homeDir = Path.home()
exportsFolder = homeDir / "AudacityExports"
exportsFolder.mkdir(parents=True, exist_ok=True)
fullPath = exportsFolder / "latest.wav"
outputPath = str(fullPath).replace("\\", "/")
imgPath = exportsFolder / "img.png"
preImgPath = exportsFolder / "pre.png"
SUCCESS = "Exported to WAV format:"


def launchAudacity():
    if sys.platform.startswith("win"):
        path = r"C:\Program Files\Audacity\Audacity.exe"
    elif sys.platform == "darwin":
        path = "/Applications/Audacity.app"
    elif sys.platform.startswith("linux"):
        path = "audacity"

    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen([path])
    except FileNotFoundError:
        print("Could not find Audacity. Either it is not installed or your PATH differs from the standard path. "
              "Continuing ...")


def init():
    global TONAME, FROMNAME, EOL

    if sys.platform == 'win32':
        TONAME = '\\\\.\\pipe\\ToSrvPipe'
        FROMNAME = '\\\\.\\pipe\\FromSrvPipe'
        EOL = '\r\n\0'
    else:
        TONAME = '/tmp/audacity_script_pipe.to.' + str(os.getuid())
        FROMNAME = '/tmp/audacity_script_pipe.from.' + str(os.getuid())
        EOL = '\n'

    if not os.path.exists(TONAME):
        print("\033[93mPIPE ERROR. Ensure Audacity is running with mod-script-pipe.\033[0m")
        sys.exit()


def exportSoundFromAudacity():
    try:
        with open(TONAME, 'w') as pipew:
            pipew.write(f'Export2: Filename="{outputPath}" NumChannels=1' + EOL)
            pipew.flush()

        with open(FROMNAME, 'r') as piper:
            response = piper.readline()
            if debugOn: ("Response: " + response)
            return response.startswith(SUCCESS)

    except Exception as e:
        print(f"\033[93mError occurred: {e}\033[0m")
        return False


def generateWave(norm: bool):
    if debugOn: print("generating wave...")
    color = '#0064be' if norm else '#E07A5F'
    y, sr = librosa.load(fullPath, sr=None)
    x = np.linspace(0, 100, num=len(y))

    plt.figure(figsize=(8, 2))
    plt.plot(x, y, color=color, linewidth=1.75)
    plt.xlim(0, 100)

    if (debugOn):
        plt.gca().set_facecolor('red')
        if norm:
            plt.savefig(imgPath, dpi=400)
        else:
            plt.savefig(preImgPath, dpi=400)
    else:
        plt.axis('off')
        if norm:
            plt.savefig(imgPath, dpi=400, transparent=True)
        else:
            plt.savefig(preImgPath, dpi=400, transparent=True)

    plt.close()


def createPdf():
    if debugOn: print("creating pdf...")
    PAGE_W = 275.1
    PAGE_H = 190.5

    img_w = 240
    x = (PAGE_W - img_w) / 2

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()

    if not isPreSaved:
        y = (PAGE_H - 120) / 2 + 20
        pdf.image(str(imgPath), x=x, y=y, w=img_w, h=120)
    else:
        pdf.image(str(preImgPath), x=x, y=40, w=img_w, h=80)
        pdf.image(str(imgPath), x=x, y=104, w=img_w, h=80)

    pdf.output("tmp.pdf")
    template = PdfReader("template.pdf")
    rimg = PdfReader("tmp.pdf")
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

    if os.path.exists("tmp.pdf"):
        os.remove("tmp.pdf")


def shortcutSavePressed():
    global isPreSaved
    if exportSoundFromAudacity():
        generateWave(True)
        createPdf()
        isPreSaved = False
        print("\033[32mPDF created\033[0m")


def shortcutPreSavePressed():
    global isPreSaved
    generateWave(False)
    isPreSaved = True
    print("\033[32m1st img SAVED\033[0m")


def shortcutResetPressed():
    global isPreSaved
    isPreSaved = False
    print("\033[38;5;208mimg RESET\033[0m")


if __name__ == "__main__":
    launchAudacity()
    init()

    with keyboard.GlobalHotKeys({'<ctrl>+<alt>+p': shortcutSavePressed,
                                 '<ctrl>+<alt>+o': shortcutPreSavePressed,
                                 '<ctrl>+<alt>+r': shortcutResetPressed}) as listener:
        listener.join()

