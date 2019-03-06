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
PORTRAIT_DIR = './pad-portrait/'
PORTRAIT_WIDTH = 100
PADDING = 10
LATENTS_WIDTH = 25
LATENTS_MAP = {
    0: 'latent_sdr',
    1: 'killer_balanced',
    2: 'killer_physical',
    3: 'killer_healer',
    4: 'killer_dragon',
    5: 'killer_god',
    6: 'killer_attacker',
    7: 'killer_devil',
    8: 'killer_machine',

    # 9: 'Vendor',
    # 10: 'Evo',
    # 11: 'Enhance',
    # 12: 'Awakening',
    # 13: 'HP',
    # 14: 'Attack',
    # 15: 'RCV',
    # 16: 'Autoheal',
    # 17: 'Fire Resist',
    # 18: 'Water Resist',
    # 19: 'Wood Resist',
    # 20: 'Light Resist',
    # 21: 'Dark Resist',
}


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
    urllib.request.urlretrieve(PORTRAIT_URL + monster_no + '.png', PORTRAIT_DIR + monster_no + '.png')
    print('Downloaded ' + monster_no + '.png')


def outline_text(draw, x, y, font, text_color, text):
    shadow_color = 'black'
    draw.text((x - 1, y - 1), text, font=font, fill=shadow_color)
    draw.text((x + 1, y - 1), text, font=font, fill=shadow_color)
    draw.text((x - 1, y + 1), text, font=font, fill=shadow_color)
    draw.text((x + 1, y + 1), text, font=font, fill=shadow_color)
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
            font = ImageFont.truetype('arialbd.ttf', 15)
            outline_text(draw, 5, 5, font, 'yellow', 'HP+{:d}'.format(card['+HP']))
            outline_text(draw, 5, 20, font, 'yellow', 'ATK+{:d}'.format(card['+ATK']))
            outline_text(draw, 5, 35, font, 'yellow', 'RCV+{:d}'.format(card['+RCV']))
        else:
            font = ImageFont.truetype('arialbd.ttf', 20)
            outline_text(draw, 5, 5, font, 'yellow', '+297')
    # skill level
    if card['SLV'] > 0:
        outline_text(draw, 5, 60, ImageFont.truetype('arialbd.ttf', 15), 'white', 'SLv.{:d}'.format(card['SLV']))
    # level
    if card['LV'] > 0:
        outline_text(draw, 5, 75, ImageFont.truetype('arialbd.ttf', 20), 'white', 'Lv.{:d}'.format(card['LV']))
    del draw
    if show_awakes:
        # awakening
        if card['AWAKE'] >= 9:
            awake = Image.open(ASSETS_DIR + 'star.png')
        else:
            awake = Image.open(ASSETS_DIR + 'circle.png')
            draw = ImageDraw.Draw(awake)
            draw.text((8, 2), str(card['AWAKE']), font=ImageFont.truetype('arialbd.ttf', 25), fill='yellow')
            del draw
        awake.thumbnail((25, 30), Image.LANCZOS)
        portrait.paste(awake, (PORTRAIT_WIDTH-awake.size[0]-5, 5), awake)
        awake.close()
    return portrait


def combine_latents(latents):
    if not latents:
        return False
    latents_bar = Image.new('RGBA',
                            (PORTRAIT_WIDTH, PORTRAIT_WIDTH),
                            (255, 255, 255, 0))
    x_offset = 0
    y_offset = 0
    latents.sort(reverse=True)
    last_height = 0
    for l in latents:
        latent_icon = Image.open(ASSETS_DIR + LATENTS_MAP[l] + '.png')
        if x_offset + latent_icon.size[0] > PORTRAIT_WIDTH:
            x_offset = 0
            print(latent_icon.size)
            y_offset += last_height
        latents_bar.paste(latent_icon, (x_offset, y_offset))
        last_height = latent_icon.size[1]
        x_offset += latent_icon.size[0]
    return latents_bar


def generate_instructions(build):
    output = ''
    for step in build['Instruction']:
        output += 'F{:d}: P{:d} '.format(step['Floor'], step['Player'])
        if step['Active'] is not None:
            output += ' '.join([str(build['Team'][idx][ids]['ID'])
                                for idx, side in enumerate(step['Active'])
                                for ids in side]) + ', '
        output += step['Action']
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
    return math.floor((line_height - font_size) / 2)


def idx_to_xy(idx):
        return idx // 2, (idx + 1) % 2


def generate_build_image(build, include_instructions=False):
    p_w = PORTRAIT_WIDTH * len(build['Team'][0]) // 2 + PADDING * math.ceil(len(build['Team'][0]) / 10)
    p_h = (PORTRAIT_WIDTH * 2 + LATENTS_WIDTH * 2 + PADDING) * len(build['Team'])
    include_instructions &= build['Instruction'] is not None
    if include_instructions:
        p_h += len(build['Instruction']) * (PORTRAIT_WIDTH//2 + PADDING)
    build_img = Image.new('RGBA',
                          (p_w, p_h),
                          (255, 255, 255, 0))
    y_offset = 0
    for team in build['Team']:
        has_assist = False
        has_latents = False
        for idx, card in enumerate(team):
            if idx > 11 or idx > 9 and len(build['Team']) > 1:
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
        y_offset += PORTRAIT_WIDTH + PADDING
        if has_assist:
            y_offset += PORTRAIT_WIDTH
        if has_latents:
            y_offset += LATENTS_WIDTH * 2

    if include_instructions:
        draw = ImageDraw.Draw(build_img)
        font = ImageFont.truetype('arialbd.ttf', 20)
        text_padding = text_center_pad(25, PORTRAIT_WIDTH//2)
        for step in build['Instruction']:
            x_offset = PADDING
            outline_text(draw, x_offset, y_offset + text_padding,
                         font, 'white', 'F{:d}:   P{:d} '.format(step['Floor'], step['Player'] + 1))
            x_offset += PORTRAIT_WIDTH - PADDING
            if step['Active'] is not None:
                actives_used = [str(build['Team'][idx][ids]['ID'])
                                for idx, side in enumerate(step['Active'])
                                for ids in side]
                for card in actives_used:
                    p_small = Image.open(PORTRAIT_DIR + str(card) + '.png')\
                        .resize((PORTRAIT_WIDTH//2, PORTRAIT_WIDTH//2), Image.LANCZOS)
                    build_img.paste(p_small, (x_offset, y_offset))
                    x_offset += PORTRAIT_WIDTH//2
                x_offset += PADDING
            outline_text(draw, x_offset, y_offset + text_padding, font, 'white', step['Action'])
            y_offset += PORTRAIT_WIDTH//2
        del draw

    build_img = trim(build_img)

    fname = filename(build['Name'])
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