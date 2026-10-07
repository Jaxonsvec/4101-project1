"""Object-oriented parse tree and Scheme pretty-printing behavior."""


class Node:
    def print(self, indent=0, force_regular=False):
        raise NotImplementedError

    def __str__(self):
        return self.print()


class Ident(Node):
    def __init__(self, value): self.value = value.lower()
    def print(self, indent=0, force_regular=False): return self.value


class BoolLit(Node):
    _instances = {}
    def __new__(cls, value):
        value = bool(value)
        if value not in cls._instances:
            obj = super().__new__(cls)
            obj.value = value
            cls._instances[value] = obj
        return cls._instances[value]
    def __init__(self, value): pass
    def print(self, indent=0, force_regular=False): return "#t" if self.value else "#f"


class IntLit(Node):
    def __init__(self, value): self.value = int(value)
    def print(self, indent=0, force_regular=False): return str(self.value)


class StringLit(Node):
    def __init__(self, value): self.value = value
    def print(self, indent=0, force_regular=False): return self.value


class Nil(Node):
    _instance = None
    def __new__(cls):
        if cls._instance is None: cls._instance = super().__new__(cls)
        return cls._instance
    def print(self, indent=0, force_regular=False): return "()"


class Special:
    def print(self, cons, indent=0):
        return cons.print_regular(indent)


class Regular(Special): pass


class Quote(Special):
    def print(self, cons, indent=0):
        items, tail = cons.parts()
        if len(items) != 2 or tail is not NIL:
            # The parser does not validate special-form arity in Project 1.
            return cons.print_regular(indent, force_subtree=True)
        return "'" + items[1].print(indent, force_regular=True)


class _MultilineSpecial(Special):
    def keyword(self, cons): return cons.parts()[0][0].value
    def print(self, cons, indent=0):
        items, tail = cons.parts()
        if not items: return "()"
        keyword = self.keyword(cons)
        if len(items) == 1 and tail is NIL:
            return "(" + keyword + "\n" + " " * indent + ")"
        result = "(" + keyword
        for item in items[1:]:
            result += "\n" + " " * (indent + 2) + item.print(indent + 2, force_regular=True)
        if tail is not NIL:
            result += "\n" + " " * (indent + 2) + ". " + tail.print(indent + 2, force_regular=True)
        return result + "\n" + " " * indent + ")"


class Begin(_MultilineSpecial): pass
class Let(_MultilineSpecial): pass
class Cond(_MultilineSpecial): pass


class _HeadThenLines(Special):
    def print(self, cons, indent=0):
        items, tail = cons.parts()
        if not items: return "()"
        if len(items) == 1 and tail is NIL:
            return "(" + items[0].print(indent) + "\n" + " " * indent + ")"
        result = "(" + items[0].print(indent)
        if len(items) > 1:
            result += " " + items[1].print(indent)
        for item in items[2:]:
            result += "\n" + " " * (indent + 2) + item.print(indent + 2)
        if tail is not NIL:
            result += "\n" + " " * (indent + 2) + ". " + tail.print(indent + 2)
        return result + "\n" + " " * indent + ")"


class If(_HeadThenLines): pass
class Lambda(_HeadThenLines): pass


class Define(Special):
    def print(self, cons, indent=0):
        items, _ = cons.parts()
        # Function-definition syntax has a list as its second element.
        if len(items) > 1 and isinstance(items[1], Cons):
            return _HeadThenLines().print(cons, indent)
        return cons.print_regular(indent)


class Set(Special): pass


SPECIALS = {
    "quote": Quote, "lambda": Lambda, "begin": Begin, "if": If,
    "let": Let, "cond": Cond, "define": Define, "set!": Set,
}


class Cons(Node):
    def __init__(self, car, cdr, special=None):
        self.car, self.cdr = car, cdr

        if special is None:
            special_type = Regular
            if isinstance(car, Ident):
                special_type = SPECIALS.get(car.value, Regular)
            special = special_type()

        self.special = special

    def parts(self):
        items, cur = [], self
        while isinstance(cur, Cons):
            items.append(cur.car)
            cur = cur.cdr
        return items, cur

    def print_regular(self, indent=0, force_subtree=False):
        items, tail = self.parts()
        if not items and tail is NIL: return "()"
        rendered = [item.print(indent, force_regular=force_subtree) for item in items]
        body = " ".join(rendered)
        if tail is not NIL:
            body += (" " if body else "") + ". " + tail.print(indent, force_regular=force_subtree)
        return "(" + body + ")"

    def print(self, indent=0, force_regular=False):
        if force_regular: return self.print_regular(indent, force_subtree=True)
        return self.special.print(self, indent)


NIL = Nil()
TRUE = BoolLit(True)
FALSE = BoolLit(False)


def make_cons(car, cdr):
    return Cons(car, cdr)
