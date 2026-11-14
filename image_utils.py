from pathlib import Path
from PIL import Image


PINTEREST_WIDTH = 1000
PINTEREST_HEIGHT = 1500


def prepare_pinterest_image(
    input_path,
    output_path=None,
    target_width=PINTEREST_WIDTH,
    target_height=PINTEREST_HEIGHT,
):
    """Prepare a Pinterest-friendly 2:3 image without cropping the product."""
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Image not found: {input_path}")

    if output_path is None:
        output_path = input_path.with_name(input_path.stem + "_pinterest.jpg")
    else:
        output_path = Path(output_path)

    with Image.open(input_path) as img:
        img = img.convert("RGB")

        ratio = min(target_width / img.width, target_height / img.height)
        new_width = max(1, int(img.width * ratio))
        new_height = max(1, int(img.height * ratio))

        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        canvas = Image.new("RGB", (target_width, target_height), "white")
        x = (target_width - new_width) // 2
        y = (target_height - new_height) // 2
        canvas.paste(resized, (x, y))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output_path, format="JPEG", quality=95, optimize=True)

    return str(output_path.resolve())
