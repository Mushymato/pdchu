from ply import lex
import sys
import json
import csv
from PaDBuildImage import filename, REVERSE_LATENTS_MAP


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
        return t

    def t_ASSIST(self, t):
        r'\(.+?\)'
        # words in ()
        t.value = t.value.strip('()')
        return t

    def t_LATENT(self, t):
        r'\[.+?\]'
        # words in []
        t.value = [REVERSE_LATENTS_MAP[l] for l in t.value.strip('[]').split(',')]
        return t

    def t_LV(self, t):
        r'[lL][vV]\d{1,3}'
        # LV followed by 1~3 digit number
        t.value = int(t.value[2:])
        return t

    def t_SLV(self, t):
        r'[sS][lL][vV]\d{1,2}'
        # SL followed by 1~2 digit number
        t.value = int(t.value[3:])
        return t

    def t_AWAKE(self, t):
        r'[aA][wW]\d'
        # AW followed by 1 digit number
        t.value = int(t.value[2:])
        return t

    def t_STATS(self, t):
        r'\|'
        return t

    def t_P_ALL(self, t):
        r'\+\d{1,3}'
        # + followed by 0 or 297
        t.value = int(t.value[1:])
        return t

    def t_P_HP(self, t):
        r'\+[hH]\d{1,3}'
        # +H followed by 3 digit number
        t.value = int(t.value[2:])
        return t

    def t_P_ATK(self, t):
        r'\+[aA]\d{1,2}'
        # +A followed by 2 digit number
        t.value = int(t.value[2:])
        return t

    def t_P_RCV(self, t):
        r'\+[rR]\d{1,2}'
        # +R followed by 2 digit number
        t.value = int(t.value[2:])
        return t

    t_ignore = ' \t\n'

    def t_error(self, t):
        raise ValueError("Unknown text '{}' at position {}".format(t.value, t.lexpos))

    def build(self, **kwargs):
        # pass debug=1 to enable verbose output
        self.lexer = lex.lex(module=self)
        return self.lexer


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
    team_str_list = [row for row in csv.reader(input_str.split(';'), delimiter='/', quotechar='"')]
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
        'NAME': sys.argv[3] if len(sys.argv) >= 4 and sys.argv[2] == '--name' else 'Nameless Build',
        # 'TEAM': parse_build(sys.argv[1]),
        'TEAM': parse_build('"l/b yog"/"lxyog(r/x yog)";"d/g kami"/"takami"'),
        'INSTRUCTION': None
    }
    with open(filename(build_data['NAME']) + '.json', 'w') as fp:
        json.dump(build_data, fp, indent=4, sort_keys=True)
