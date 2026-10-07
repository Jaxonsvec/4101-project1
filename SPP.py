"""Scheme Pretty-Printer entry point. Reads Scheme from stdin."""
import argparse
import sys

from parser import ParseError, Parser
from scanner import Scanner, ScannerError


def main(argv=None):
    cli = argparse.ArgumentParser(description="Pretty-print the supported Scheme subset")
    cli.add_argument("-d", action="store_true", help="print scanner tokens to stderr")
    args = cli.parse_args(argv)
    source = sys.stdin.read()
    try:
        scanner = Scanner(source, debug=args.d)
        expressions = Parser(scanner).parse_program()
    except (ScannerError, ParseError) as exc:
        print(f"SPP: {exc}", file=sys.stderr)
        return 1
    print("\n".join(expr.print() for expr in expressions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
