from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parent.parent
CHARACTERS = ROOT / "assets" / "characters"
ENEMIES = ROOT / "assets" / "enemies"
OUT = ROOT / "assets" / "runtime"
PREVIEWS = ROOT / "assets" / "previews"
OUT.mkdir(parents=True, exist_ok=True)
PREVIEWS.mkdir(parents=True, exist_ok=True)


def normalized_frame(image: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    """Crop one known atlas cell and align visible pixels to a shared baseline."""
    cell = image.crop(box).convert("RGBA")
    bounds = cell.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError(f"Selected an empty sprite cell: {box}")
    sprite = cell.crop(bounds)
    frame = Image.new("RGBA", (64, 64))
    x = (64 - sprite.width) // 2
    y = 59 - sprite.height
    frame.alpha_composite(sprite, (x, y))
    return frame


def make_strip(
    source: Path,
    destination: Path,
    frame_width: int,
    frame_height: int,
    cells: list[tuple[int, int]],
) -> list[Image.Image]:
    image = Image.open(source).convert("RGBA")
    frames = [
        normalized_frame(
            image,
            (
                column * frame_width,
                row * frame_height,
                (column + 1) * frame_width,
                (row + 1) * frame_height,
            ),
        )
        for row, column in cells
    ]
    strip = Image.new("RGBA", (64 * len(frames), 64))
    for index, frame in enumerate(frames):
        strip.alpha_composite(frame, (index * 64, 0))
    strip.save(destination)
    return frames


def save_preview(frames: list[Image.Image], labels: list[str], destination: Path) -> None:
    scale = 3
    cell_width = 64 * scale
    cell_height = 64 * scale + 22
    preview = Image.new("RGBA", (cell_width * len(frames), cell_height), (20, 24, 34, 255))
    draw = ImageDraw.Draw(preview)
    for index, (frame, label) in enumerate(zip(frames, labels)):
        x = index * cell_width
        for cy in range(0, 64 * scale, 16):
            for cx in range(0, cell_width, 16):
                shade = 38 if (cx // 16 + cy // 16) % 2 else 48
                draw.rectangle((x + cx, cy, x + cx + 15, cy + 15), fill=(shade, shade + 4, shade + 12, 255))
        preview.alpha_composite(frame.resize((cell_width, 64 * scale), Image.Resampling.NEAREST), (x, 0))
        draw.text((x + 5, 64 * scale + 4), label, fill=(240, 225, 177, 255))
    preview.save(destination)


# These cells were selected from a labeled 48x32 grid. Attack art is intentionally
# rendered as a separate FX layer because the slash frames span multiple atlas cells.
player_cells = [(0, 0), *[(3, column) for column in range(6)], (6, 0), (15, 0)]
player_labels = ["idle", "run-1", "run-2", "run-3", "run-4", "run-5", "run-6", "jump", "hurt"]

for suffix in ("a", "b", "c", "d"):
    frames = make_strip(
        CHARACTERS / f"player-{suffix}.png",
        OUT / f"player-{suffix}.png",
        48,
        32,
        player_cells,
    )
    frames[0].save(OUT / f"portrait-{suffix}.png")
    save_preview(frames, player_labels, PREVIEWS / f"player-{suffix}.png")

for name in ("healer", "smith", "guide", "master"):
    frames = make_strip(
        CHARACTERS / f"npc-{name}.png",
        OUT / f"npc-{name}.png",
        48,
        32,
        [(0, 0)],
    )
    save_preview(frames, ["idle"], PREVIEWS / f"npc-{name}.png")

enemy_specs = {
    "slime": (ENEMIES / "slime-walk.png", 32, 32, [(0, c) for c in range(4)]),
    "pig": (ENEMIES / "pig.png", 64, 32, [(0, c) for c in range(8)]),
    "orc": (ENEMIES / "orc.png", 64, 32, [(0, c) for c in range(8)]),
    "skeleton": (ENEMIES / "skeleton.png", 64, 32, [(0, c) for c in range(5)]),
}

for name, (source, width, height, cells) in enemy_specs.items():
    frames = make_strip(source, OUT / f"enemy-{name}.png", width, height, cells)
    save_preview(frames, [f"walk-{i + 1}" for i in range(len(frames))], PREVIEWS / f"enemy-{name}.png")

slime_death = make_strip(
    ENEMIES / "slime-death.png",
    OUT / "enemy-slime-death.png",
    32,
    32,
    [(0, c) for c in range(4)],
)
save_preview(slime_death, [f"death-{i + 1}" for i in range(4)], PREVIEWS / "enemy-slime-death.png")
