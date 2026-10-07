"""Scanner for the Scheme subset used by the pretty printer."""
from dataclasses import dataclass
import sys


@dataclass(frozen=True)
class Token:
    type: str
    value: object = None
    line: int = 1
    column: int = 1

    def __repr__(self):
        return f"Token({self.type!r}, {self.value!r}, {self.line}:{self.column})"


class ScannerError(Exception):
    pass


class Scanner:
    SINGLE = {"'": "QUOTE", ".": "DOT", "(": "LPAREN", ")": "RPAREN"}
    INITIAL = set("!$%&*/:<=>?^_~")
    SUBSEQUENT = set("+- .@") - {" "}

    def __init__(self, source, debug=False):
        self.source = source
        self.debug = debug
        self.i = 0
        self.line = 1
        self.column = 1

    def _advance(self):
        ch = self.source[self.i]
        self.i += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _emit(self, kind, value=None, line=None, col=None):
        token = Token(kind, value, line or self.line, col or self.column)
        if self.debug:
            print(token, file=sys.stderr)
        return token

    def tokens(self):
        out = []
        while True:
            token = self.getNextToken()
            out.append(token)
            if token.type == "EOF":
                return out

    def getNextToken(self):
        """Consume and return one token, skipping whitespace and comments."""
        n = len(self.source)
        while self.i < n:
            ch = self.source[self.i]
            if ch in " \t\n\r\f":
                self._advance()
                continue
            if ch == ";":
                while self.i < n and self._advance() != "\n":
                    pass
                continue
            line, col = self.line, self.column
            if self.source.startswith("...", self.i):
                end = self.i + 3
                if end < n and self._is_identifier_constituent(self.source[end]):
                    raise ScannerError(f"line {line}, column {col}: invalid identifier '...'")
                self._advance(); self._advance(); self._advance()
                self._require_delimiter(line, col)
                return self._emit("IDENTIFIER", "...", line, col)
            if ch in self.SINGLE:
                self._advance()
                if ch == ".":
                    self._require_delimiter(line, col)
                return self._emit(self.SINGLE[ch], ch, line, col)
            if ch == '"':
                self._advance()
                chars = []
                while self.i < n and self.source[self.i] != '"':
                    c = self._advance()
                    if c == "\\":
                        if self.i >= n:
                            raise ScannerError(f"line {line}, column {col}: unterminated string escape")
                        escaped = self._advance()
                        # Preserve the escaped character; strings are opaque data here.
                        chars.extend(("\\", escaped))
                    else:
                        chars.append(c)
                if self.i >= n:
                    raise ScannerError(f"line {line}, column {col}: unterminated string")
                self._advance()
                return self._emit("STRING", '"' + "".join(chars) + '"', line, col)
            if ch == "#":
                spelling = self.source[self.i:self.i + 2].lower()
                if spelling in ("#t", "#f"):
                    end = self.i + 2
                    if end < n and self.source[end] not in " \t\n\r\f();\"":
                        raise ScannerError(f"line {line}, column {col}: boolean must be followed by a delimiter")
                    self._advance(); self._advance()
                    return self._emit("BOOLEAN", spelling, line, col)
                raise ScannerError(f"line {line}, column {col}: invalid boolean or unsupported token")
            if "0" <= ch <= "9":
                start = self.i
                while self.i < n and "0" <= self.source[self.i] <= "9":
                    self._advance()
                self._require_delimiter(line, col)
                return self._emit("INTEGER", int(self.source[start:self.i]), line, col)
            if ch in "+-":
                self._advance()
                if self.i < n and self._is_subsequent(self.source[self.i]):
                    raise ScannerError(f"line {line}, column {col}: invalid identifier starting with {ch!r}")
                self._require_delimiter(line, col)
                return self._emit("IDENTIFIER", ch, line, col)
            if self._is_initial(ch):
                start = self.i
                self._advance()
                while self.i < n and self._is_subsequent(self.source[self.i]):
                    self._advance()
                name = self.source[start:self.i]
                self._require_delimiter(line, col)
                return self._emit("IDENTIFIER", name.lower(), line, col)
            raise ScannerError(f"line {line}, column {col}: unexpected character {ch!r}")
        return self._emit("EOF", None, self.line, self.column)

    def _require_delimiter(self, line, col):
        if (
            self.i < len(self.source)
            and self.source[self.i] not in " \t\n\r\f();\""
        ):
            raise ScannerError(f"line {line}, column {col}: must be followed by a delimiter")

    @classmethod
    def _is_initial(cls, c):
        return "a" <= c <= "z" or "A" <= c <= "Z" or c in cls.INITIAL

    @classmethod
    def _is_subsequent(cls, c):
        return cls._is_initial(c) or "0" <= c <= "9" or c in cls.SUBSEQUENT

    @classmethod
    def _is_identifier_constituent(cls, c):
        return cls._is_initial(c) or cls._is_subsequent(c)
