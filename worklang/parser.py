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

class DiscardNode(Node):
    def __init__(self, value: Node):
        self.value = value

class ModuleDeclNode(Node):
    def __init__(self, modname: list[str]):
        self.modname = modname

class BinOpNode(Node):
    def __init__(self, left: Node, op: TokenType, right: Node):
        self.left = left
        self.op = op
        self.right = right

class ProcDeclNode(Node):
    def __init__(self, name: str, args: list[str], body: list[Node]):
        self.name = name
        self.args = args
        self.body = body

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
        if self.tok.type == TokenType.Keyword:
            if self.tok.value == Keyword.Module:
                v = self.module_decl()

                assert self.tok.type == TokenType.Semicolon, "';' expected"
                self.next()

                return v

        return self.statement()
    
    def statement(self):
        if self.tok.type == TokenType.Keyword:
            if self.tok.value == Keyword.Proc:
                return self.proc_decl()
            else:
                raise NotImplementedError(f"Cannot process keyword {self.tok.value} in statement context")
        else:
            # expr
            v: Node = self.expr()
            v = DiscardNode(v)
        
        assert self.tok.type == TokenType.Semicolon, "';' expected"
        self.next()

        return v

    def proc_decl(self):
        self.next()

        assert self.tok.type == TokenType.Identifier, "identifier expected"
        proc_name = self.tok.value
        self.next()

        assert self.tok.type == TokenType.ParenOpen, "'(' expected"
        self.next()

        args: list[str] = []
        while self.tok.type != TokenType.ParenClose:
            assert self.tok.type == TokenType.Identifier, "identifier expected"
            args.append(self.tok.value)
            self.next()

            if self.tok.type == TokenType.ParenClose:
                break

            assert self.tok.type == TokenType.Comma, "',' expected"
            self.next()
        self.next()

        body: list[Node] = []
        while self.tok.value != Keyword.End:
            body.append(self.statement())
        self.next()

        return ProcDeclNode(proc_name, args, body)
    
    def module_decl(self):
        self.next()
        assert self.tok.type == TokenType.Identifier, "identifier expected"

        modname: list[str] = []
        while self.tok.type == TokenType.Identifier:
            modname.append(self.tok.value)
            self.next()

            if self.tok.type == TokenType.Comma: # type: ignore
                self.next()
                continue
            break

        return ModuleDeclNode(modname)

    def expr(self):
        return self.expr_add()
    
    def expr_add(self) -> Node:
        v = self.expr_mul()

        while self.tok.type in (TokenType.Plus,):
            t = self.tok.type
            self.next()
            right = self.expr()
            v = BinOpNode(v, t, right)

        return v
    
    def expr_mul(self):
        v = self.call()

        while self.tok.type in (TokenType.Multiply,):
            t = self.tok.type
            self.next()
            right = self.expr()
            v = BinOpNode(v, t, right)

        return v
    
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
        