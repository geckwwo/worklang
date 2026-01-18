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