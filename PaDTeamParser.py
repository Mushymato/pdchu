from ply import lex
import sys
import json
from PaDBuildImage import filename, LATENTS_MAP


class PaDTeamLexer(object):
    tokens = [
        'ID',
        'ASSIST',
        'LATENT',
        'STATS',
        'LV',
        'SLV',
        'AWAKE',
        'P_HP',
        'P_ATK',
        'P_RCV',
        'P_ALL',
    ]

    def t_ID(self, t):
        r'^.+?(?=[\(\|\[])|^(?!.*[\(\|\[].*).+'
        # first word before ( or [ or { or entire word if those characters are not in string
        if t.value != 'sdr':
            t.value = int(t.value)
        return t

    def t_ASSIST(self, t):
        r'\(.+\)'
        # words in ()
        t.value = t.value.strip('()')
        return t

    def t_LATENT(self, t):
        r'\[.+\]'
        # words in []
        t.value = map_latents(t.value.strip('[]').split(','))
        return t

    def t_LV(self, t):
        r'LV\d{1,3}'
        # LV followed by 1~3 digit number
        t.value = int(t.value.replace('LV', ''))
        return t

    def t_SLV(self, t):
        r'SLV\d{1,2}'
        # SL followed by 1~2 digit number
        t.value = int(t.value.replace('SLV', ''))
        return t

    def t_AWAKE(self, t):
        r'AW\d'
        # AW followed by 1 digit number
        t.value = int(t.value.replace('AW', ''))
        return t

    def t_STATS(self, t):
        r'\|'
        return t

    def t_P_ALL(self, t):
        r'\+(0|297)'
        # + followed by 0 or 297
        t.value = int(t.value.strip('+'))
        return t

    def t_P_HP(self, t):
        r'\+H\d{1,3}'
        # +H followed by 3 digit number
        t.value = int(t.value.replace('+H', ''))
        return t

    def t_P_ATK(self, t):
        r'\+A\d{1,3}'
        # AW followed by 1 digit number
        t.value = int(t.value.replace('+A', ''))
        return t

    def t_P_RCV(self, t):
        r'\+R\d{1,3}'
        # AW followed by 1 digit number
        t.value = int(t.value.replace('+R', ''))
        return t

    t_ignore = ' \t\n'

    def t_error(self, t):
        raise ValueError("Unknown text '%s'" % (t.value,))

    def build(self, **kwargs):
        # pass debug=1 to enable verbose output
        self.lexer = lex.lex(module=self)
        return self.lexer


def map_latents(latent_arr):
    latent_idx = []
    for latent in latent_arr:
        for id, lt in LATENTS_MAP.items():
            if latent in lt or lt in latent:
                latent_idx.append(id)
                break
    return latent_idx


def process_card(lexer, card_str, is_assist=False):
    lexer.input(card_str)
    if not is_assist:
        result_card = {
            '+ATK': 99,
            '+HP': 99,
            '+RCV': 99,
            'AWAKE': 9,
            'ID': 1,
            'LATENT': None,
            'LV': 99,
            'SLV': 0
        }
    else:
        result_card = {
            '+ATK': 0,
            '+HP': 0,
            '+RCV': 0,
            'AWAKE': 9,
            'ID': 1,
            'LATENT': None,
            'LV': 0,
            'SLV': 0
        }
    assist = False
    for tok in iter(lexer.token, None):
        if tok.type == 'ASSIST':
            assist = tok.value
        elif tok.type == 'ID' and tok.value == 'sdr':
            result_card['ID'] = 'delay_buffer'
        elif tok.type == 'P_ALL':
            result_card['+HP'] = tok.value // 3
            result_card['+ATK'] = tok.value // 3
            result_card['+RCV'] = tok.value // 3
        elif tok.type != 'STATS':
            result_card[tok.type.replace('P_', '+')] = tok.value
    if is_assist:
        return result_card
    else:
        if isinstance(assist, str):
            return [result_card, process_card(lexer, assist, is_assist=True)]
        else:
            return [result_card, None]


def parse_build(input_str):
    lexer = PaDTeamLexer().build()
    team_str_list = [x.split('/') for x in input_str.split(';')]
    team_list = []
    for team in team_str_list:
        team_sublist = []
        for slot in team:
            team_sublist.extend(process_card(lexer, slot))
        team_list.append(team_sublist)
    return team_list


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('USAGE: ' + sys.argv[0] + ' <team_str> [--name <build_name>]')
    build_data = {
        'Name': sys.argv[3] if len(sys.argv) >= 4 and sys.argv[2] == '--name' else 'Nameless Build',
        'Team': parse_build(sys.argv[1]),
        'Instruction': None
    }
    with open(filename(build_data['Name']) + '.json', 'w') as fp:
        json.dump(build_data, fp, indent=4, sort_keys=True)