import argparse
import sys
from collections.abc import Sequence
from typing import TextIO

from ._helpers.generate_user_configs_yaml import generate_user_configs_yaml


def main(argv: Sequence[str] | None = None) -> int:
    parser = _create_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args, stdout=sys.stdout, stderr=sys.stderr))


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pydantic-settings-manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_user_configs_parser = subparsers.add_parser(
        "generate-user-configs",
        help="Generate a commented user settings YAML template.",
    )
    generate_user_configs_parser.add_argument(
        "import_paths",
        metavar="MODULE",
        nargs="+",
        help="Module path containing a settings manager.",
    )
    generate_user_configs_parser.add_argument(
        "--manager-name",
        default="settings_manager",
        help="Settings manager attribute name. Defaults to settings_manager.",
    )
    generate_user_configs_parser.set_defaults(handler=_run_generate_user_configs)

    return parser


def _run_generate_user_configs(
    args: argparse.Namespace,
    *,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    try:
        yaml_text = generate_user_configs_yaml(args.import_paths, manager_name=args.manager_name)
    except (ModuleNotFoundError, AttributeError, TypeError) as e:
        print(f"error: {e}", file=stderr)
        return 1

    print(yaml_text, file=stdout)
    return 0
