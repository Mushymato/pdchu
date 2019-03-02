import json
import sys
from pathlib import Path
import urllib.request
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

PORTRAIT_URL = 'https://f002.backblazeb2.com/file/miru-data/padimages/jp/portrait/'
PORTRAIT_DIR = './pad-portrait/'
PORTRAIT_WIDTH = 100
PADDING = 10
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

    9: 'Vendor',
    10: 'Evo',
    11: 'Enhance',
    12: 'Awakening',
    13: 'HP',
    14: 'Attack',
    15: 'RCV',
    16: 'Autoheal',
    17: 'Fire Resist',
    18: 'Water Resist',
    19: 'Wood Resist',
    20: 'Light Resist',
    21: 'Dark Resist',
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
    shadow_color = "black"
    draw.text((x - 1, y - 1), text, font=font, fill=shadow_color)
    draw.text((x + 1, y - 1), text, font=font, fill=shadow_color)
    draw.text((x - 1, y + 1), text, font=font, fill=shadow_color)
    draw.text((x + 1, y + 1), text, font=font, fill=shadow_color)
    draw.text((x, y), text, font=font, fill=text_color)


def combine_portrait(card, mode='BASE_CARD'):
    download_portrait(card['ID'])
    portrait = Image.open(PORTRAIT_DIR + str(card['ID']) + '.png')
    if mode == 'OFF_COLOR_ASSIST':
        return portrait
    draw = ImageDraw.Draw(portrait)
    # + eggs
    if 0 < card['+HP'] + card['+ATK'] + card['+RCV'] < 297:
        font = ImageFont.truetype("arialbd.ttf", 15)
        outline_text(draw, 5, 5, font, "yellow", "HP+{:d}".format(card['+HP']))
        outline_text(draw, 5, 20, font, "yellow", "ATK+{:d}".format(card['+ATK']))
        outline_text(draw, 5, 35, font, "yellow", "RCV+{:d}".format(card['+RCV']))
    else:
        font = ImageFont.truetype("arialbd.ttf", 20)
        outline_text(draw, 5, 5, font, "yellow", "+{:d}".format(card['+HP'] + card['+ATK'] + card['+RCV']))
    if card['SLV'] > 0:
        outline_text(draw, 5, 60, ImageFont.truetype("arialbd.ttf", 15), "pink", "SLv.{:d}".format(card['SLV']))
    # level
    outline_text(draw, 5, 75, ImageFont.truetype("arialbd.ttf", 20), "white", "Lv.{:d}".format(card['LV']))
    if mode == 'ON_COLOR_ASSIST':
        return portrait
    # awakening
    if card['AWAKE'] >= 9:
        awake = Image.open('assets/star.png')
    else:
        awake = Image.open('assets/circle.png')
        draw = ImageDraw.Draw(awake)
        draw.text((8, 2), str(card['AWAKE']), font=ImageFont.truetype("arialbd.ttf", 25), fill="yellow")
    del draw
    awake.thumbnail((25, 30), Image.LANCZOS)
    portrait.paste(awake, (PORTRAIT_WIDTH-awake.size[0]-5, 5), awake)
    awake.close()
    if mode == 'BASE_CARD':
        return portrait


def combine_latents(latents):
    if not latents:
        return False
    latents_bar = Image.new('RGBA',
                            (PORTRAIT_WIDTH, PORTRAIT_WIDTH),
                            (255, 255, 255, 0))
    x_offset = 0
    y_offset = 0
    for l in latents:
        latent_icon = Image.open('assets/' + LATENTS_MAP[l] + '.png')
        if x_offset + latent_icon.size[0] >= PORTRAIT_WIDTH:
            x_offset = 0
            y_offset += latent_icon.size[1]
        latents_bar.paste(latent_icon, (x_offset, y_offset))
        x_offset += latent_icon.size[0]
    return latents_bar


def idx_to_xy(idx):
        return idx // 2, (idx + 1) % 2


def generate_build_image(build):
    p_w, p_h = PORTRAIT_WIDTH * 5 + PADDING, int(PORTRAIT_WIDTH * build['Players'] * 3)
    build_img = Image.new('RGBA',
                          (p_w, p_h),
                          (255, 255, 255, 0))
    y_offset = 0
    for team in build['Team']:
        for idx, card in enumerate(team):
            if card:
                portrait = combine_portrait(card)
                x, y = idx_to_xy(idx)
                x_offset = PADDING if x > 0 else 0
                build_img.paste(portrait, (x_offset + x * PORTRAIT_WIDTH, y_offset + y * PORTRAIT_WIDTH))
                if y % 2 == 1:
                    latents = combine_latents(card['LATENT'])
                    if latents:
                        build_img.paste(latents, (x_offset + x * PORTRAIT_WIDTH, y_offset + (y + 1) * PORTRAIT_WIDTH))
        y_offset += int(PORTRAIT_WIDTH * 3)
    build_img.save(build['Name'] + '.png')
    print("Saved " + build['Name'] + '.png')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("USAGE: " + sys.argv[0] + " build.json")
    with open(sys.argv[1], 'r') as fp:
        build = json.load(fp)
        generate_build_image(build)
    # with open('nidhogg.json', 'w') as fp:
    #     json.dump(build, fp, indent=4)
