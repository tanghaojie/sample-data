"""Deterministic shared PBR textures; no photographs or baked sunlight."""

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

STYLES = {
    "office": {"wall": (154, 166, 168), "glass": (75, 111, 121), "lit": 0.38, "roughness": 0.25},
    "residential": {"wall": (182, 176, 164), "glass": (79, 99, 106), "lit": 0.46, "roughness": 0.32},
    "concrete": {"wall": (173, 175, 174), "glass": (77, 99, 105), "lit": 0.25, "roughness": 0.34},
    "brick": {"wall": (149, 118, 96), "glass": (73, 90, 99), "lit": 0.32, "roughness": 0.34},
    "commercial": {"wall": (183, 179, 167), "glass": (77, 102, 111), "lit": 0.42, "roughness": 0.28},
}


def create_materials(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    entries = []
    size = 256
    for index, (name, style) in enumerate(STYLES.items()):
        rng = np.random.default_rng(3100 + index)
        base = Image.new("RGB", (size, size), style["wall"])
        orm = Image.new("RGB", (size, size), (255, 205, 0))
        emission = Image.new("RGB", (size, size), (0, 0, 0))
        relief = Image.new("L", (size, size), 128)
        base_draw, orm_draw = ImageDraw.Draw(base), ImageDraw.Draw(orm)
        light_draw, relief_draw = ImageDraw.Draw(emission), ImageDraw.Draw(relief)
        for row in range(4):
            for col in range(4):
                x, y = col * 64, row * 64
                window = (x + 9, y + 12, x + 54, y + 53)
                if name == "office":
                    window = (x + 3, y + 4, x + 60, y + 59)
                shade = float(rng.uniform(0.88, 1.12))
                glass = tuple(min(255, round(c * shade)) for c in style["glass"])
                base_draw.rectangle(window, fill=glass, outline=(117, 129, 130), width=2)
                orm_draw.rectangle(window, fill=(255, round(255 * style["roughness"]), 0))
                relief_draw.rectangle(window, fill=110, outline=150, width=2)
                if rng.random() < style["lit"]:
                    brightness = float(rng.uniform(0.30, 0.78))
                    color = tuple(round(c * brightness) for c in (255, 208, 154))
                    light_draw.rectangle((window[0] + 2, window[1] + 2, window[2] - 2, window[3] - 2), fill=color)
                    light_draw.line((x + 32, window[1], x + 32, window[3]), fill=(0, 0, 0), width=2)
        # Low amplitude surface variation remains fixed across all exports.
        pixels = np.asarray(base, dtype=np.int16)
        noise = rng.integers(-2, 3, (size, size, 1), dtype=np.int16)
        base = Image.fromarray(np.clip(pixels + noise, 0, 255).astype(np.uint8))
        heights = np.asarray(relief.filter(ImageFilter.GaussianBlur(0.65)), dtype=np.float32) / 255
        dy, dx = np.gradient(heights)
        normal = np.stack((-dx * 2.0, -dy * 2.0, np.ones_like(dx)), axis=2)
        normal /= np.linalg.norm(normal, axis=2, keepdims=True)
        normal = Image.fromarray(np.round((normal * 0.5 + 0.5) * 255).astype(np.uint8))
        for suffix, texture in [("base", base), ("orm", orm), ("emissive", emission), ("normal", normal)]:
            texture.save(directory / f"{name}-{suffix}.png", optimize=True)
        entries.append({"name": name, "span_m": [12, 12], "emissive": True})
    rng = np.random.default_rng(3180)
    roof = np.full((size, size, 3), (133, 139, 138), dtype=np.int16)
    roof += rng.integers(-3, 4, (size, size, 1), dtype=np.int16)
    roof[::32, :, :] -= 12
    roof[:, ::32, :] -= 12
    Image.fromarray(np.clip(roof, 0, 255).astype(np.uint8)).save(directory / "roof-base.png", optimize=True)
    Image.new("RGB", (size, size), (255, 220, 0)).save(directory / "roof-orm.png", optimize=True)
    Image.new("RGB", (size, size), (128, 128, 255)).save(directory / "roof-normal.png", optimize=True)
    entries.append({"name": "roof", "span_m": [16, 16], "emissive": False})
    (directory / "library.json").write_text(json.dumps({"version": 1, "entries": entries}, indent=2) + "\n")
    return entries
