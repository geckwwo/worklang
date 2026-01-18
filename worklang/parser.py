from .lexer import TokenType, Token, Keyword

class Node:
    def __repr__(self):
        props = list(filter(lambda x: not x.startswith("__"), dir(self)))
        pairs = list((f"{prop}={repr(getattr(self, prop))}" for prop in props))
        return self.__class__.__name__ + f"({', '.join(pairs)})"

class CallNode(Node):
    def __init__(self, callee: Node, args: list[Node]):
        self.callee = callee
        self.args = args

class IdenNode(Node):
    def __init__(self, iden: str):
        self.iden = iden

class ConstNode(Node):
    def __init__(self, value: str | int | float | bool):
        self.value = value

class ParserException(Exception):
    pass

class Parser:
    def __init__(self):
        pass

    def next(self, step: int = 1):
        self.idx += step
        self.tok = self.tokens[self.idx] if self.idx < len(self.tokens) else Token(TokenType.EOF)

    def run(self, tokens: list[Token]):
        self.tokens = tokens
        self.idx = -1
        self.tok = Token(TokenType.EOF)
        self.next()

        body: list[Node] = []
        while self.tok.type != TokenType.EOF:
            body.append(self.root_statement())
        
        return body

    def root_statement(self):
        # TODO: keyword shit

        # expr
        v: Node = self.expr()
        
        assert self.tok.type == TokenType.Semicolon, "';' expected"
        self.next()

        return v
    
    def expr(self):
        return self.call()
    
    def call(self):
        v = self.atom()

        while self.tok.type == TokenType.ParenOpen:
            self.next()
            args: list[Node] = []
            while self.tok.type != TokenType.ParenClose: # pyright: ignore[reportUnnecessaryComparison]
                args.append(self.expr())
                if self.tok.type == TokenType.ParenClose: # pyright: ignore[reportUnnecessaryComparison]
                    break

                assert self.tok.type == TokenType.Comma, "',' expected"
                self.next()
            self.next()

            v = CallNode(v, args)
        return v
    
    def atom(self) -> Node:
        if self.tok.type in (TokenType.String, TokenType.Number):
            v = ConstNode(self.tok.value)
            self.next()
            return v
        elif self.tok.type == TokenType.ParenOpen:
            self.next()
            v = self.expr()
            assert self.tok.type == TokenType.ParenClose, "')' expected"
            self.next()
            return v
        elif self.tok.type == TokenType.Identifier:
            v = IdenNode(self.tok.value)
            self.next()
            return v
        else:
            raise ParserException(f"Unknown atom {self.tok}")