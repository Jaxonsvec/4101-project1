"""Recursive-descent parser for the project's simplified Scheme grammar."""
from nodes import BoolLit, Ident, IntLit, NIL, StringLit, make_cons


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, scanner):
        self.scanner = scanner
        self._pending = None

    @property
    def lookahead(self):
        if self._pending is None:
            self._pending = self.scanner.getNextToken()
        return self._pending

    def take(self, expected=None):
        token = self._pending
        if token is None:
            token = self.scanner.getNextToken()
        if expected is not None and token.type != expected:
            self.error(f"expected {expected}, found {token.type}", token)
        self._pending = None
        return token

    def error(self, message, token=None):
        t = token if token is not None else self.lookahead
        raise ParseError(f"line {t.line}, column {t.column}: {message}")

    def parse_program(self):
        expressions = []
        while True:
            expression = self.parse_exp()
            if expression is None:
                break
            expressions.append(expression)
        return expressions

    def parse_exp(self, allow_eof=True):
        """Read an expression without fetching any token after it.

        None marks EOF between top-level expressions; EOF inside an
        expression is a syntax error.
        """
        token = self.take()
        if token.type == "EOF" and allow_eof:
            return None
        if token.type == "LPAREN":
            return self.parse_rest()
        if token.type == "BOOLEAN":
            return BoolLit(token.value == "#t")
        if token.type == "INTEGER":
            return IntLit(token.value)
        if token.type == "STRING":
            return StringLit(token.value)
        if token.type == "IDENTIFIER":
            return Ident(token.value)
        if token.type == "QUOTE":
            return make_cons(Ident("quote"), make_cons(self.parse_exp(False), NIL))
        self.error(f"expected expression, found {token.type}", token)

    def parse_rest(self):
        if self.lookahead.type == "RPAREN":
            self.take()
            return NIL
        if self.lookahead.type in ("EOF", "DOT"):
            self.error("list must start with an expression")
        items = [self.parse_exp(False)]
        while self.lookahead.type not in ("DOT", "RPAREN"):
            if self.lookahead.type == "EOF":
                self.error("unterminated list")
            items.append(self.parse_exp(False))
        tail = NIL
        if self.lookahead.type == "DOT":
            self.take()
            if self.lookahead.type in ("RPAREN", "EOF", "DOT"):
                self.error("dot must be followed by exactly one expression")
            tail = self.parse_exp(False)
            if self.lookahead.type != "RPAREN":
                self.error("dotted list must have one expression after the dot")
        self.take("RPAREN")
        result = tail
        for item in reversed(items):
            result = make_cons(item, result)
        return result
