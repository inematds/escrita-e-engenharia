#!/usr/bin/env python3
"""Roda um comando e desenha a saída como uma janela de terminal (PNG), para o guia e o vídeo.

Uso: python3 ferramentas/print_terminal.py saida.png "titulo da janela" -- comando args...
Precisa de Pillow (pip install pillow). Fonte: DejaVu Sans Mono (padrão no Linux).
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
TAM = 26
CORES = {"✔": (74, 222, 128), "✘": (248, 113, 113), "!": (250, 204, 21)}


def main():
    saida, titulo = sys.argv[1], sys.argv[2]
    cmd = sys.argv[sys.argv.index("--") + 1:]
    p = subprocess.run(cmd, capture_output=True, text=True)
    linhas = ["$ " + " ".join(cmd[1:] if cmd[0].startswith("python") else cmd)] + p.stdout.rstrip().splitlines()
    f = ImageFont.truetype(FONTE, TAM)
    lh = int(TAM * 1.45)
    w = max(1500, int(max(f.getlength(l) for l in linhas)) + 120)
    h = 90 + lh * len(linhas) + 50
    im = Image.new("RGB", (w, h), (12, 12, 16))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, 56), 0, fill=(28, 28, 36))
    for i, c in enumerate([(248, 113, 113), (250, 204, 21), (74, 222, 128)]):
        d.ellipse((24 + i * 34, 18, 44 + i * 34, 38), fill=c)
    d.text((150, 14), titulo, font=f, fill=(160, 160, 170))
    y = 80
    for i, l in enumerate(linhas):
        cor = (250, 204, 21) if i == 0 else CORES.get(l[:1], (230, 230, 235))
        if l.startswith(("nota:", "  ", "     dica")) or "ok," in l:
            cor = (250, 204, 21) if (l.startswith("nota:") or "ok," in l) else (150, 150, 160)
        d.text((40, y), l, font=f, fill=cor)
        y += lh
    Path(saida).parent.mkdir(parents=True, exist_ok=True)
    im.save(saida)
    print(saida, im.size)


if __name__ == "__main__":
    main()
