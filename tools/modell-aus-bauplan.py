"""Erzeugt modell.json (Blockmodell für die Website) aus einem bauplan.html.

Nutzung:  python3 tools/modell-aus-bauplan.py gebaeude/wabenhaus
Braucht:  pip install playwright && playwright install chromium

Der Bauplan baut sein Blockmodell in JavaScript zusammen. Das Skript öffnet ihn
in einem unsichtbaren Browser, liest das Modell aus und schreibt es kompakt als
modell.json in denselben Ordner. Sobald es für ein Gebäude eine Schematic gibt,
wird modell.json durch die echte Welt ersetzt.
"""
import asyncio
import json
import re
import sys
from pathlib import Path

from playwright.async_api import async_playwright


def lies_palette(html):
    """Blocknamen und Farben aus MAT und OBJ des Bauplans holen."""
    palette = {}
    for key, name, farbe in re.findall(r'^\s*(\w+):\s*\{ en: "([^"]+)", k: "\w+", c: "(#[0-9a-f]{6})"', html, re.M):
        palette[key] = {"name": name, "farbe": farbe}
    for key, name, farbe in re.findall(r'^\s*"([mx]-\w+)": \{ n: "([^"]+)", c: "(#[0-9a-f]{6})"', html, re.M):
        palette[key] = {"name": name, "farbe": farbe}
    return palette


async def lies_voxel(html):
    html = html.replace("var V = {};", "var V = window.__V = {};", 1)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html)
        await page.wait_for_timeout(500)
        voxel = await page.evaluate("window.__V")
        await browser.close()
    return voxel


def main():
    ordner = Path(sys.argv[1] if len(sys.argv) > 1 else "gebaeude/wabenhaus")
    html = (ordner / "bauplan.html").read_text(encoding="utf-8")
    palette = lies_palette(html)
    voxel = asyncio.run(lies_voxel(html))
    # Teile aus dem Bauplan, die im echten Gebäude nicht stehen
    weglassen = {"x-ae2"}  # ME-System steht im ME-Gebäude
    voxel = {k: m for k, m in voxel.items() if m not in weglassen}

    ids = sorted(set(voxel.values()))
    index = {m: i for i, m in enumerate(ids)}
    eintraege = []
    for m in ids:
        info = palette.get(m, {"name": m, "farbe": "#888888"})
        eintraege.append({
            "id": m,
            "name": info["name"],
            "farbe": info["farbe"],
            "transparent": m in ("glass", "orangeglass"),
            "klein": m == "flower",
        })
    bloecke = []
    for key, m in voxel.items():
        x, y, z = (int(v) for v in key.split(","))
        bloecke.append([x, y, z, index[m]])
    bloecke.sort(key=lambda b: (b[1], b[2], b[0]))

    ziel = ordner / "modell.json"
    with ziel.open("w", encoding="utf-8") as f:
        f.write('{"quelle":"bauplan.html","palette":')
        json.dump(eintraege, f, ensure_ascii=False, separators=(",", ":"))
        f.write(',"bloecke":[\n')
        f.write(",\n".join(json.dumps(b, separators=(",", ":")) for b in bloecke))
        f.write("\n]}\n")
    print(f"{ziel}: {len(bloecke)} Blöcke, {len(eintraege)} Sorten")


if __name__ == "__main__":
    main()
