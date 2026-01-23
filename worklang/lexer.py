import string
import enum
from typing import Any

CYRILLIC_LOWER = ''.join(chr(c) for c in range(0x0430, 0x044F + 1))
CYRILLIC_UPPER = ''.join(chr(c) for c in range(0x0410, 0x042F + 1))
CYRILLIC_NON_STANDARD = 'ёЁєЄіїІґҐ'

CYRILLIC_LETTERS = CYRILLIC_LOWER + CYRILLIC_UPPER + CYRILLIC_NON_STANDARD
ALL_LETTERS = string.ascii_letters + CYRILLIC_LETTERS + "_"
ALL_LETTERS_DIGITS = ALL_LETTERS + string.digits

WHITESPACE = " \t\r\n\v"

class TokenType(enum.Enum):
    EOF = -1
    
    Identifier = 1
    Number = 2
    String = 3
    Keyword = 4

    ParenOpen = "("
    ParenClose = ")"
    Semicolon = ";"
    Dot = "."
    Comma = ","

    QuestionMark = "?"
    Eq = "="

    Plus = "+"
    Multiply = "*"

class Keyword(enum.Enum):
    Use = "использовать"
    If = "если"
    Module = "модуль"
    Proc = "процедура"
    End = "конец"
    Return = "вернуть"
    For = "для"
    In = "в"

KEYWORDS = list(x.value for x in Keyword)
TOKENTYPES = list(x.value for x in TokenType)

class Token:
    def __init__(self, token_type: TokenType, value: Any = None):
        self.type = token_type
        self.value = value

    def __repr__(self):
        if self.value is not None:
            return f'Token({self.type}, {self.value})'
        return f'Token({self.type})'

class LexerException(Exception):
    pass

class Lexer:
    def __init__(self):
        pass

    def next(self, step: int = 1):
        self.idx += step
        self.ch = self.text[self.idx] if self.idx < len(self.text) else None

    def run(self, data: str):
        self.idx = -1
        self.ch = None
        self.text = data + "\n"

        self.next()

        tokens: list[Token] = []

        while self.ch is not None:
            if self.ch in WHITESPACE:
                self.next()
            elif self.ch in TOKENTYPES:
                tokens.append(Token(TokenType(self.ch)))
                self.next()
            elif self.ch in ALL_LETTERS:
                iden = ""
                while self.ch in ALL_LETTERS_DIGITS:
                    iden += self.ch
                    self.next()

                if iden.lower() in KEYWORDS:
                    tokens.append(Token(TokenType.Keyword, Keyword(iden.lower())))
                else:
                    tokens.append(Token(TokenType.Identifier, iden))
            elif self.ch.isdigit():
                num = ""
                while self.ch is not None and self.ch.isdigit():
                    num += self.ch
                    self.next()

                tokens.append(Token(TokenType.Number, int(num)))
            elif self.ch in "\"'":
                quote = self.ch
                self.next()

                s = ""
                while self.ch != quote:
                    s += self.ch
                    self.next()
                self.next()

                tokens.append(Token(TokenType.String, s))
            else:
                raise LexerException(f"Неизвестный символ '{self.ch}'")

        return tokens