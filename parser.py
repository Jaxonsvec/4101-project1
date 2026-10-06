"""Recursive-descent parser for the project's simplified Scheme grammar."""
from nodes import BoolLit, Cons, FALSE, Ident, IntLit, NIL, StringLit, make_cons


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    @property
    def lookahead(self):
        return self.tokens[self.position]

    def take(self, expected=None):
        token = self.lookahead
        if expected is not None and token.type != expected:
            self.error(f"expected {expected}, found {token.type}")
        self.position += 1
        return token

    def error(self, message):
        t = self.lookahead
        raise ParseError(f"line {t.line}, column {t.column}: {message}")

    def parse_program(self):
        expressions = []
        while self.lookahead.type != "EOF":
            expressions.append(self.parse_exp())
        return expressions

    def parse_exp(self):
        token = self.lookahead
        if token.type == "LPAREN":
            self.take()
            return self.parse_rest()
        if token.type == "BOOLEAN":
            self.take()
            return BoolLit(token.value == "#t")
        if token.type == "INTEGER":
            self.take()
            return IntLit(token.value)
        if token.type == "STRING":
            self.take()
            return StringLit(token.value)
        if token.type == "IDENTIFIER":
            self.take()
            return Ident(token.value)
        if token.type == "QUOTE":
            self.take()
            return make_cons(Ident("quote"), make_cons(self.parse_exp(), NIL))
        self.error(f"expected expression, found {token.type}")

    def parse_rest(self):
        if self.lookahead.type == "RPAREN":
            self.take()
            return NIL
        if self.lookahead.type in ("EOF", "DOT"):
            self.error("list must start with an expression")
        items = [self.parse_exp()]
        while self.lookahead.type not in ("DOT", "RPAREN"):
            if self.lookahead.type == "EOF":
                self.error("unterminated list")
            items.append(self.parse_exp())
        tail = NIL
        if self.lookahead.type == "DOT":
            dot = self.take()
            if self.lookahead.type in ("RPAREN", "EOF", "DOT"):
                self.error("dot must be followed by exactly one expression")
            tail = self.parse_exp()
            if self.lookahead.type != "RPAREN":
                self.error("dotted list must have one expression after the dot")
        self.take("RPAREN")
        result = tail
        for item in reversed(items):
            result = make_cons(item, result)
        return result
