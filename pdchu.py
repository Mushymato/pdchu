import json
from pathlib import Path
import urllib.request
from PIL import Image
from PIL import ImageDraw

PORTRAIT_URL = 'https://f002.backblazeb2.com/file/miru-data/padimages/jp/portrait/'
PORTRAIT_DIR = './pad-portrait/'
PORTRAIT_WIDTH = 100
LATENTS_MAP = {
    1: 'Balanced',
    2: 'Physical',
    3: 'Healer',
    4: 'Dragon',
    5: 'God',
    6: 'Attacker',
    7: 'Devil',
    8: 'Machine',
    9: 'Vendor',
    10: 'Evo',
    11: 'Enhance',
    12: 'Awakening',

    13: 'HP',
    14: 'Attack',
    15: 'RCV',
    16: 'Autoheal',
    17: 'SDR',
    18: 'Fire Resist',
    19: 'Water Resist',
    20: 'Wood Resist',
    21: 'Light Resist',
    22: 'Dark Resist',
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


def idx_to_xy(idx):
        return idx // 2, (idx + 1) % 2


def generate_build_image(build):
    p_w, p_h = PORTRAIT_WIDTH * 5 + 5, int(PORTRAIT_WIDTH * build['Players'] * 2.5)
    build_img = Image.new('RGBA',
                          (p_w, p_h),
                          (255, 255, 255, 0))
    draw = ImageDraw.Draw(build_img, 'RGBA')
    y_offset = 0
    for team in build['Team']:
        for idx, card in enumerate(team):
            if card:
                download_portrait(card['ID'])
                portrait = Image.open(PORTRAIT_DIR + str(card['ID']) + '.png')
                x, y = idx_to_xy(idx)
                x_offset = PORTRAIT_WIDTH + (5 if x > 0 else 0)
                build_img.paste(portrait, (x_offset + x * PORTRAIT_WIDTH, y_offset + y * PORTRAIT_WIDTH))
        y_offset += int(PORTRAIT_WIDTH * 2.5)
    build_img.save(build['Name'] + '.png')
    print("Saved " + build['Name'] + '.png')


if __name__ == '__main__':
    with open('nidhogg.json', 'r') as fp:
        build = json.load(fp)
        generate_build_image(build)
    #with open('nidhogg.json', 'w') as fp:
    #    json.dump(build, fp, indent=4)
