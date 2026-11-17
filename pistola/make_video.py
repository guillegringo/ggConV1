"""Suma subtitulos a los cuadros de Blender y arma el MP4."""
import os, glob
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
HERE = os.path.dirname(os.path.abspath(__file__))
FR = sorted(glob.glob(os.path.join(HERE, "renders", "frames", "f*.png")))
FPS = 30
CAP = [(0.0, 1.3, "1. Heat inserts M3 en la mitad izquierda (soldador a ~220 C)"),
       (1.3, 2.3, "2. Camara DFRobot: entra justa en el canon, la rosca muerde el plastico"),
       (2.3, 3.3, "3. Pro Micro USB-C: se encastra en sus rieles, el USB sale por la base"),
       (3.3, 4.3, "4. Gatillo sobre su eje (tornillo de ajuste M3x10 en la cola)"),
       (4.3, 5.1, "5. Microswitch en su alojamiento (a presion entre las dos mitades)"),
       (5.1, 6.1, "6. Pulsadores 12x12 + botones impresos: A/B izquierda, START/SELECT derecha"),
       (6.1, 8.1, "7. Cablear todo y cerrar las mitades"),
       (8.1, 9.6, "8. Tornillos M3x10 (y M3x25 en el eje del gatillo) desde la derecha"),
       (9.6, 99, "Lightgun GUN4IR  -  Pro Micro + DFRobot SEN0158")]
try: font = ImageFont.truetype("arialbd.ttf", 30)
except OSError: font = ImageFont.load_default()
out = os.path.join(HERE, "renders", "ensamblado.mp4")
w = imageio_ffmpeg.write_frames(out, (1280, 720), fps=FPS, quality=8, macro_block_size=8); w.send(None)
for i, f in enumerate(FR + [FR[-1]] * FPS):
    t = i / FPS
    img = Image.open(f).convert("RGB"); d = ImageDraw.Draw(img)
    txt = next((c for a, b, c in CAP if a <= t < b), "")
    if txt:
        bb = d.textbbox((0, 0), txt, font=font); tw = bb[2] - bb[0]
        x, y = (1280 - tw) // 2, 650
        d.rounded_rectangle([x - 18, y - 10, x + tw + 18, y + 44], 10, fill=(20, 20, 24))
        d.text((x, y), txt, font=font, fill=(255, 255, 255))
    w.send(img.tobytes())
w.close(); print("OK", out)
