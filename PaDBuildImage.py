import json
import sys
from pathlib import Path
import urllib.request
import math
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageChops

ASSETS_DIR = './assets/'
PORTRAIT_URL = 'https://f002.backblazeb2.com/file/miru-data/padimages/jp/portrait/'
PORTRAIT_DIR = './portrait/'
PORTRAIT_WIDTH = 100
PADDING = 10
LATENTS_WIDTH = 25
LATENTS_MAP = {
    1: 'bak',
    2: 'phk',
    3: 'hek',
    4: 'drk',
    5: 'gok',
    6: 'aak',
    7: 'dek',
    8: 'mak',
    9: 'evk',
    10: 'rek',
    11: 'awk',
    12: 'enk',
    13: 'all',
    14: 'hp+',
    15: 'atk+',
    16: 'rcv+',
    17: 'rres+',
    18: 'bres+',
    19: 'gres+',
    20: 'lres+',
    21: 'dres+',
    # size changes
    22: 'hp',
    23: 'atk',
    24: 'rcv',
    25: 'rres',
    26: 'bres',
    27: 'gres',
    28: 'lres',
    29: 'dres',
    30: 'ah',
    31: 'sdr'
}
REVERSE_LATENTS_MAP = {v: k for k, v in LATENTS_MAP.items()}
FONT_NAME = ASSETS_DIR + 'OpenSans-ExtraBold.ttf'


def download_portrait(monster_no):
    monster_no = str(monster_no)
    p = Path(PORTRAIT_DIR)
    if p.exists():
        if p.is_dir():
            p = Path(PORTRAIT_DIR + monster_no + '.png')
            if p.exists():
                return False
        else:
            print(PORTRAIT_DIR + ' taken, cannot create folder')
            return False
    else:
        p.mkdir()
        print('Created ' + PORTRAIT_DIR)
    print('Downloading ' + monster_no + '.png')
    urllib.request.urlretrieve(PORTRAIT_URL + monster_no + '.png', PORTRAIT_DIR + monster_no + '.png')


def outline_text(draw, x, y, font, text_color, text, thickness=1):
    shadow_color = 'black'
    draw.text((x - thickness, y - thickness), text, font=font, fill=shadow_color)
    draw.text((x + thickness, y - thickness), text, font=font, fill=shadow_color)
    draw.text((x - thickness, y + thickness), text, font=font, fill=shadow_color)
    draw.text((x + thickness, y + thickness), text, font=font, fill=shadow_color)
    draw.text((x, y), text, font=font, fill=text_color)


def combine_portrait(card, show_awakes):
    if card['ID'] == 'delay_buffer':
        return Image.open(ASSETS_DIR + 'delay_buffer.png')
    download_portrait(card['ID'])
    portrait = Image.open(PORTRAIT_DIR + str(card['ID']) + '.png')
    draw = ImageDraw.Draw(portrait)
    # + eggs
    sum_plus = card['+HP'] + card['+ATK'] + card['+RCV']
    if 0 < sum_plus:
        if sum_plus < 297:
            font = ImageFont.truetype(FONT_NAME, 14)
            outline_text(draw, 5, 2, font, 'yellow', '+{:d} HP'.format(card['+HP']))
            outline_text(draw, 5, 14, font, 'yellow', '+{:d} ATK'.format(card['+ATK']))
            outline_text(draw, 5, 26, font, 'yellow', '+{:d} RCV'.format(card['+RCV']))
        else:
            font = ImageFont.truetype(FONT_NAME, 18)
            outline_text(draw, 5, 0, font, 'yellow', '+297')
    # level
    slv_offset = 80
    if card['LV'] > 0:
        outline_text(draw, 5, 75, ImageFont.truetype(FONT_NAME, 18), 'white', 'Lv.{:d}'.format(card['LV']))
        slv_offset = 62
    # skill level
    if card['SLV'] > 0:
        outline_text(draw, 5, slv_offset,
                     ImageFont.truetype(FONT_NAME, 14), 'pink', 'SLv.{:d}'.format(card['SLV']))
    # ID
    outline_text(draw, 67, 82, ImageFont.truetype(FONT_NAME, 12), 'lightblue', str(card['ID']))
    del draw
    if show_awakes:
        # awakening
        if card['AWAKE'] >= 9:
            awake = Image.open(ASSETS_DIR + 'star.png')
        else:
            awake = Image.open(ASSETS_DIR + 'circle.png')
            draw = ImageDraw.Draw(awake)
            draw.text((9, -2), str(card['AWAKE']), font=ImageFont.truetype(FONT_NAME, 24), fill='yellow')
            del draw
        awake.thumbnail((25, 30), Image.LINEAR)
        portrait.paste(awake, (PORTRAIT_WIDTH-awake.size[0]-5, 5), awake)
        awake.close()
    return portrait


def combine_latents(latents):
    if not latents:
        return False
    if len(latents) > 6:
        latents = latents[0:6]
    latents_bar = Image.new('RGBA',
                            (PORTRAIT_WIDTH, LATENTS_WIDTH * 2),
                            (255, 255, 255, 0))
    x_offset = 0
    y_offset = 0
    row_count = 0
    one_slot, two_slot = [], []
    for l in latents:
        if l < 22:
            two_slot.append(l)
        else:
            one_slot.append(l)
    sorted_latents = []
    if len(one_slot) > len(two_slot):
        sorted_latents.extend(one_slot)
        sorted_latents.extend(two_slot)
    else:
        sorted_latents.extend(two_slot)
        sorted_latents.extend(one_slot)
    last_height = 0
    for l in sorted_latents:
        latent_icon = Image.open(ASSETS_DIR + LATENTS_MAP[l] + '.png')
        if x_offset + latent_icon.size[0] > PORTRAIT_WIDTH:
            row_count += 1
            x_offset = 0
            y_offset += last_height
        latents_bar.paste(latent_icon, (x_offset, y_offset))
        last_height = latent_icon.size[1]
        x_offset += latent_icon.size[0]
        if row_count == 1 and x_offset >= LATENTS_WIDTH * 2:
            break
    return latents_bar


def generate_instructions(build):
    output = ''
    for step in build['INSTRUCTION']:
        output += 'F{:d}: P{:d} '.format(step['FLOOR'], step['PLAYER'])
        if step['ACTIVE'] is not None:
            output += ' '.join([str(build['TEAM'][idx][ids]['ID'])
                                for idx, side in enumerate(step['ACTIVE'])
                                for ids in side]) + ', '
        output += step['ACTION']
        output += '\n'
    return output


def trim(im):
    bg = Image.new(im.mode, im.size, (255, 255, 255, 0))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)


def filename(name):
    keep_characters = ('.', '_')
    return "".join(c for c in name if c.isalnum() or c in keep_characters).rstrip()


def text_center_pad(font_size, line_height):
    return math.floor((line_height - font_size) / 3)


def idx_to_xy(idx):
        return idx // 2, (idx + 1) % 2


def generate_build_image(build, include_instructions=False):
    p_w = PORTRAIT_WIDTH * math.ceil(len(build['TEAM'][0]) / 2) + PADDING * math.ceil(len(build['TEAM'][0]) / 10)
    p_h = (PORTRAIT_WIDTH + LATENTS_WIDTH + PADDING) * 2 * len(build['TEAM'])
    include_instructions &= build['INSTRUCTION'] is not None
    if include_instructions:
        p_h += len(build['INSTRUCTION']) * (PORTRAIT_WIDTH//2 + PADDING)
    build_img = Image.new('RGBA',
                          (p_w, p_h),
                          (255, 255, 255, 0))
    y_offset = 0
    for team in build['TEAM']:
        has_assist = False
        has_latents = False
        for idx, card in enumerate(team):
            if idx > 11 or idx > 9 and len(build['TEAM']) > 1:
                break
            if card:
                x, y = idx_to_xy(idx)
                portrait = combine_portrait(card, y % 2 == 1)
                x_offset = PADDING * math.ceil(x / 4)
                build_img.paste(portrait, (x_offset + x * PORTRAIT_WIDTH, y_offset + y * PORTRAIT_WIDTH))
                if y % 2 == 0:
                    has_assist = True
                elif y % 2 == 1:
                    latents = combine_latents(card['LATENT'])
                    if latents:
                        has_latents = True
                        build_img.paste(latents, (x_offset + x * PORTRAIT_WIDTH, y_offset + (y + 1) * PORTRAIT_WIDTH))
        y_offset += PORTRAIT_WIDTH + PADDING * 2
        if has_assist:
            y_offset += PORTRAIT_WIDTH
        if has_latents:
            y_offset += LATENTS_WIDTH * 2

    if include_instructions:
        y_offset -= PADDING * 2
        draw = ImageDraw.Draw(build_img)
        font = ImageFont.truetype(FONT_NAME, 24)
        text_padding = text_center_pad(25, PORTRAIT_WIDTH//2)
        for step in build['INSTRUCTION']:
            x_offset = PADDING
            outline_text(draw, x_offset, y_offset + text_padding,
                         font, 'white', 'F{:d} - P{:d} '.format(step['FLOOR'], step['PLAYER'] + 1))
            x_offset += PORTRAIT_WIDTH
            if step['ACTIVE'] is not None:
                actives_used = [str(build['TEAM'][idx][ids]['ID'])
                                for idx, side in enumerate(step['ACTIVE'])
                                for ids in side]
                for card in actives_used:
                    p_small = Image.open(PORTRAIT_DIR + str(card) + '.png')\
                        .resize((PORTRAIT_WIDTH//2, PORTRAIT_WIDTH//2), Image.LINEAR)
                    build_img.paste(p_small, (x_offset, y_offset))
                    x_offset += PORTRAIT_WIDTH//2
                x_offset += PADDING
            outline_text(draw, x_offset, y_offset + text_padding, font, 'white', step['ACTION'])
            y_offset += PORTRAIT_WIDTH//2
        del draw

    build_img = trim(build_img)

    fname = filename(build['NAME'])
    build_img.save(fname + '.png')
    print('Saved ' + fname + '.png')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('USAGE: ' + sys.argv[0] + ' build.json [--instructions]')
    instructions = len(sys.argv) >= 3 and sys.argv[2] == '--instructions'
    with open(sys.argv[1], 'r') as fp:
        build_data = json.load(fp)
        generate_build_image(build_data, instructions)
    with open(sys.argv[1], 'w') as fp:
        json.dump(build_data, fp, indent=4, sort_keys=True)