"""How assets/zoom-png.png and assets/zoom-pdf.png were made: the same 90x160 px window of the poster
(around the "8" in "$89"), enlarged 12x. PNG: nearest-neighbour upscale of funkbox's PNG export.
PDF: funkbox's PDF export rasterized by pdftoppm at 12x the PNG's resolution (page 810x1440 pt)."""
import subprocess
from PIL import Image
Z = 12
w, h = 90, 160
cx, cy = 745, 766
x0, y0 = cx - w // 2, cy - h // 2
png = Image.open("assets/poster/sale.png").convert("RGB")
png.crop((x0, y0, x0 + w, y0 + h)).resize((1080, 1920), Image.NEAREST).save("assets/zoom-png.png")
dpi = 72 * 1080 / 810 * Z
subprocess.run(["pdftoppm", "-r", str(dpi), "-x", str(x0 * Z), "-y", str(y0 * Z), "-W", str(w * Z), "-H", str(h * Z),
                "-png", "-singlefile", "assets/poster/sale.pdf", "assets/zoom-pdf"], check=True)
