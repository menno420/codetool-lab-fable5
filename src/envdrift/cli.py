"""Argparse command-line interface for envdrift."""

from __future__ import annotations

import argparse
import sys

from envdrift import __version__
from envdrift.commands import EXIT_ERROR, CliError
from envdrift.commands import check as check_cmd
from envdrift.commands import diff as diff_cmd
from envdrift.commands import example as example_cmd
from envdrift.commands import lint as lint_cmd


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdrift",
        description="Keep your .env files honest: detect drift, diff env files, "
        "generate safe examples, and lint for common mistakes.",
    )
    parser.add_argument(
        "--version", action="version", version=f"envdrift {__version__}"
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    p_check = sub.add_parser(
        "check",
        help="compare .env against .env.example and report drift",
        description="Report keys missing from the env file, extra keys not in the "
        "example, and keys that are empty in the env but non-empty in the example "
        "(treated as required-but-empty). Exit 0 clean, 1 drift, 2 errors.",
    )
    p_check.add_argument("--env", default=".env", help="env file to check (default: .env)")
    p_check.add_argument(
        "--example", default=".env.example", help="example file (default: .env.example)"
    )
    p_check.add_argument(
        "--allow-extra",
        action="store_true",
        help="do not report keys present in the env but absent from the example",
    )
    p_check.add_argument("--format", choices=["text", "json"], default="text")
    p_check.set_defaults(func=check_cmd.run)

    p_diff = sub.add_parser(
        "diff",
        help="key-level diff between two env files",
        description="Show keys added, removed, and changed between A and B. Values "
        "are hidden by default; pass --values to reveal them. Exit 0 identical, "
        "1 differences, 2 errors.",
    )
    p_diff.add_argument("a", metavar="A", help="first env file")
    p_diff.add_argument("b", metavar="B", help="second env file")
    p_diff.add_argument(
        "--values", action="store_true", help="show values (hidden by default)"
    )
    p_diff.add_argument("--format", choices=["text", "json"], default="text")
    p_diff.set_defaults(func=diff_cmd.run)

    p_example = sub.add_parser(
        "example",
        help="generate a .env.example from a real .env",
        description="Emit an example file preserving key order, comments, and blank "
        "lines, with every value stripped to empty (envdrift never guesses which "
        "values are safe to publish). Use --keep-values-for for non-secrets like "
        "PORT. Exit 0 ok, 2 errors.",
    )
    p_example.add_argument("envfile", metavar="ENVFILE", help="source env file")
    p_example.add_argument(
        "-o", "--output", metavar="OUT", help="write to file instead of stdout"
    )
    p_example.add_argument(
        "--keep-values-for",
        metavar="REGEX",
        help="keep values for keys matching this regex (e.g. '^(PORT|LOG_LEVEL)$')",
    )
    p_example.set_defaults(func=example_cmd.run)

    p_lint = sub.add_parser(
        "lint",
        help="find common dotenv mistakes",
        description="Report duplicate keys, invalid key names, whitespace around "
        "'=', unclosed quotes, and invalid lines. With --example, also flag "
        "likely-secret values that should not be committed. Exit 0 clean, "
        "1 findings, 2 errors.",
    )
    p_lint.add_argument("file", metavar="FILE", help="env file to lint")
    p_lint.add_argument(
        "--example",
        action="store_true",
        help="treat FILE as a committed example: also flag likely-secret values",
    )
    p_lint.add_argument("--format", choices=["text", "json"], default="text")
    p_lint.set_defaults(func=lint_cmd.run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except CliError as exc:
        print(f"envdrift: error: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
