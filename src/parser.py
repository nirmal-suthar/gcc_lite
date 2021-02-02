from ply import yacc
from lexer import lexer
from lexer import tokens as lexTokens

precedence = (
    ('left', 'PLUSOP', 'MINUSOP'),
    ('left', 'MULTOP', 'DIVOP', 'MODOP'),
    ('left', 'DECOP', 'INCOP'),
    ('left', 'LSHIFT', 'RLIFT'),
    ('left', 'LTCOMP', 'LTECOMP'),
    ('left', 'GTCOMP', 'GTECOMP'),
)

#functions for handling various operators/expressions/conditionals
#functional would call the tree function which creates parse tree
