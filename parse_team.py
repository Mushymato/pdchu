from ply import lex, yacc
# basecard(assist{stats})[latents]{stats} / ...
class PadTeamStatsLexer(object):
    tokens = [
		'LEVEL',
		'SKILL_LEVEL',
		'P_SUM',
		'P_HP',
		'P_ATK',
		'P_RCV',
    ]
	
	def t_LEVEL(self, t)
		# numbers prepended with LV
		r'LV(\d+)'
		return t

	def t_SKILL_LEVEL(self, t)
		# numbers prepended with SL
		r'SL(\d+)'
		return t
		
	def t_P_SUM(self, t)
		# numbers prepended with +
		r'\+(\d+)'
		return t
		
	def t_P_HP(self, t)
		# numbers prepended with +H
		r'\+H(\d+)'
		return t
		
	def t_P_ATK(self, t)
		# numbers prepended with +A
		r'\+A(\d+)'
		return t

	def t_P_RCV(self, t)
		# numbers prepended with +R
		r'\+R(\d+)'
		return t
		
    t_ignore = ' \t\n'

    #def t_error(self, t):
        #raise rpadutils.ReportableError("Unknown text '%s'" % (t.value,))

    def build(self, **kwargs):
        # pass debug=1 to enable verbose output
        self.lexer = lex.lex(module=self)
        return self.lexer
	
class PadTeamLexer(object):
    tokens = [
        'CARD',
		'LATENTS',
        'ASSIST',
		'STATS'
    ]

    def t_CARD(self, t):
		# first word before ( or [ or { or entire word if those characters are not in string
        r'^(.+?)[\(\{\[]|^((?!.*[\(\{\[].*).*)'
        return t
		
	def t_ASSIST(self, t)
		# words inside a ()
		r'\((.+)\)'
		return t

	def t_LATENTS(self, t)
		# words inside a []
		r'\[(.+)\]'
		return t
		
	def t_STATS(self, t)
		# words inside a {}
		r'\{(.+)\}'
		return t

    t_ignore = ' \t\n'

    #def t_error(self, t):
        #raise rpadutils.ReportableError("Unknown text '%s'" % (t.value,))

    def build(self, **kwargs):
        # pass debug=1 to enable verbose output
        self.lexer = lex.lex(module=self)
        return self.lexer
