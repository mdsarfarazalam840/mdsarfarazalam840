"""Turn an image (or a single big glyph) into the art block used on the card.

Two output modes:

* Plain ASCII (default). Prints a 42x25 character block; eyeball it, then paste
  it into ASCII_ART in build_neofetch_svg.py and re-run that script.

      python tools/image_to_ascii.py me.jpg              # from a photo
      python tools/image_to_ascii.py --glyph ☣           # from one character

* Shaded mosaic (--shaded). Writes cache/ascii_art.json, a grid of brightness
  levels that build_neofetch_svg.py renders as block characters tinted per cell.
  Because brightness is carried by colour instead of by glyph density, this keeps
  far more of a photograph than the plain mode can, and it can afford a much
  finer grid than 42x25.

      python tools/image_to_ascii.py me.jpg --shaded --crop 300,95,800,800

Plain ASCII only works on high-contrast subjects on a plain background; a real
photograph usually needs --contrast turned up before the shapes survive being
squashed to 42x25 characters, and a low-key photograph (dark subject, dark
background) will not survive at all -- use --shaded for those.

Tone controls, in the order they are applied: --median denoises, --black/--white
set the black and white points (everything at or below --black becomes empty
background), --gamma lifts or crushes the mid-tones, --blur smooths what is left
before the downscale. Requires Pillow (pip install pillow), which CI does not
need.
"""

import argparse
import json
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

# The card reserves a 42x25 character block for plain ASCII art. A character cell
# is about twice as tall as it is wide, hence the 12x24 pixel cell.
COLUMNS, ROWS = 42, 25
CELL_WIDTH, CELL_HEIGHT = 12, 24

# Default grid for --shaded, and the pixel cell it samples. The cell is much
# closer to square than the ASCII one because a shaded cell is a block character
# squeezed to the mosaic's pitch, not a letter at the card's font size. Keep this
# in sync with the aspect ratio build_neofetch_svg.py gives the art panel.
SHADED_COLUMNS, SHADED_ROWS = 106, 62
SHADED_CELL_WIDTH, SHADED_CELL_HEIGHT = 4, 8

# Brightness levels in the mosaic, encoded as one hex digit per cell. Level 0 is
# background and is not drawn at all.
SHADED_LEVELS = 16

ART_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'cache', 'ascii_art.json')

# Darkest to brightest. Doubled entries widen the mid-tones, which is where most
# of the detail lands.
RAMP = ' ...,,;;::||!!ll%%$$@@@'


def from_glyph(glyph, font_path, size, width, height):
    image = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, size)
    left, top, right, bottom = draw.textbbox((0, 0), glyph, font=font)
    draw.text(((image.width - (right - left)) / 2 - left,
               (image.height - (bottom - top)) / 2 - top), glyph, font=font, fill=255)
    return image


def from_image(path, args, width, height):
    image = ImageOps.exif_transpose(Image.open(path)).convert('L')
    if args.crop:
        image = image.crop(args.crop)
    if args.median > 1:
        # Median beats a blur for film grain: it kills speckle without smearing
        # the edges the mosaic depends on.
        image = image.filter(ImageFilter.MedianFilter(args.median))
    if args.black or args.white != 255 or args.gamma != 1.0:
        image = image.point(tone_curve(args.black, args.white, args.gamma))
    else:
        image = ImageOps.autocontrast(image)
    if args.contrast != 1.0:
        image = ImageEnhance.Contrast(image).enhance(args.contrast)
    if args.invert:
        image = ImageOps.invert(image)
    # Letterbox onto the art block's aspect ratio so nothing gets stretched.
    return ImageOps.pad(image, (width, height), color=0)


def tone_curve(black, white, gamma):
    """Lookup table that clips below `black`, clips above `white`, then gammas.

    A gamma under 1.0 lifts the mid-tones, which is what pulls a face out of a
    low-key photograph. Everything at or below `black` lands on 0 so the
    background stays empty instead of turning into a grey slab.
    """
    span = max(1, white - black)
    curve = []
    for value in range(256):
        level = min(1.0, max(0.0, (value - black) / span))
        curve.append(int(255 * level ** gamma))
    return curve


def downscale(image, columns, rows, blur):
    return image.filter(ImageFilter.GaussianBlur(blur)).resize((columns, rows), Image.LANCZOS)


def to_ascii(image, blur):
    small = downscale(image, COLUMNS, ROWS, blur)
    pixels = small.load()
    lines = []
    for y in range(ROWS):
        row = ''.join(RAMP[min(len(RAMP) - 1, pixels[x, y] * len(RAMP) // 256)]
                      for x in range(COLUMNS))
        lines.append(row.rstrip())
    # Trim blank rows top and bottom so the art sits where you expect it to.
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def to_shaded(image, columns, rows, blur, floor):
    """Grid of hex brightness levels, one digit per cell, '0' meaning empty."""
    small = downscale(image, columns, rows, blur)
    pixels = small.load()
    grid = []
    for y in range(rows):
        row = ''
        for x in range(columns):
            value = pixels[x, y]
            level = 0 if value < floor else min(SHADED_LEVELS - 1,
                                                value * SHADED_LEVELS // 256)
            row += f'{level:x}'
        grid.append(row)
    return grid


def preview(grid):
    """Rough terminal look at a shaded grid, two columns per character."""
    ramp = ' .:-=+*#%@'
    lines = []
    for row in grid:
        lines.append(''.join(
            ramp[min(len(ramp) - 1, int(row[x], 16) * len(ramp) // SHADED_LEVELS)]
            for x in range(0, len(row), 2)))
    return lines


def parse_crop(text):
    parts = [int(part) for part in text.split(',')]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError('crop takes four numbers: x0,y0,x1,y1')
    return tuple(parts)


def parse_grid(text):
    parts = text.lower().split('x')
    if len(parts) != 2:
        raise argparse.ArgumentTypeError('grid looks like 106x62')
    return int(parts[0]), int(parts[1])


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('image', nargs='?', help='path to a source image')
    parser.add_argument('--glyph', help='render one character instead of an image')
    parser.add_argument('--font', default='C:/Windows/Fonts/seguisym.ttf',
                        help='font used with --glyph')
    parser.add_argument('--size', type=int, default=640, help='point size for --glyph')
    parser.add_argument('--shaded', action='store_true',
                        help='write a shaded mosaic to cache/ascii_art.json '
                             'instead of printing ASCII')
    parser.add_argument('--grid', type=parse_grid,
                        help='mosaic grid, e.g. 106x62 (--shaded only)')
    parser.add_argument('--crop', type=parse_crop,
                        help='crop the source first: x0,y0,x1,y1 in source pixels')
    parser.add_argument('--black', type=int, default=0,
                        help='black point; source values at or below this go empty')
    parser.add_argument('--white', type=int, default=255, help='white point')
    parser.add_argument('--gamma', type=float, default=1.0,
                        help='under 1.0 lifts mid-tones, over 1.0 crushes them')
    parser.add_argument('--median', type=int, default=1,
                        help='median filter window, odd; 5 is a good start for grain')
    parser.add_argument('--floor', type=int, default=0,
                        help='mosaic cells below this brightness stay empty (--shaded only)')
    parser.add_argument('--contrast', type=float, default=1.0)
    parser.add_argument('--blur', type=float, default=2.5,
                        help='smooths speckle; raise it if the art looks noisy')
    parser.add_argument('--invert', action='store_true',
                        help='use for dark subjects on a light background')
    args = parser.parse_args()

    if args.shaded:
        columns, rows = args.grid or (SHADED_COLUMNS, SHADED_ROWS)
        cell = (SHADED_CELL_WIDTH, SHADED_CELL_HEIGHT)
    else:
        columns, rows = COLUMNS, ROWS
        cell = (CELL_WIDTH, CELL_HEIGHT)
    width, height = columns * cell[0], rows * cell[1]

    if args.glyph:
        image = from_glyph(args.glyph, args.font, args.size, width, height)
    elif args.image:
        image = from_image(args.image, args, width, height)
    else:
        parser.error('give an image path or --glyph')

    if not args.shaded:
        print('\n'.join(to_ascii(image, args.blur)))
        return

    grid = to_shaded(image, columns, rows, args.blur, args.floor)
    art = {
        'source': os.path.basename(args.image or f'glyph {args.glyph}'),
        'columns': columns,
        'rows': rows,
        'levels': SHADED_LEVELS,
        'settings': {
            'crop': list(args.crop) if args.crop else None,
            'black': args.black, 'white': args.white, 'gamma': args.gamma,
            'median': args.median, 'blur': args.blur, 'floor': args.floor,
        },
        'grid': grid,
    }
    os.makedirs(os.path.dirname(ART_FILE), exist_ok=True)
    with open(ART_FILE, 'w', encoding='utf-8', newline='\n') as handle:
        json.dump(art, handle, indent=2)
        handle.write('\n')
    print('\n'.join(preview(grid)))
    print(f'\nwrote {ART_FILE} ({columns}x{rows}). '
          'Run tools/build_neofetch_svg.py to put it on the card.')


if __name__ == '__main__':
    main()
