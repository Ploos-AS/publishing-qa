from __future__ import annotations

import sys

from .release_cli import release_main


def main():
    if len(sys.argv) < 2:
        print("usage: ploos-qa <release> ...", file=sys.stderr)
        return 2
    command, args = sys.argv[1], sys.argv[2:]
    if command == "release":
        return release_main(args)
    print(f"unknown command: {command}", file=sys.stderr)
    return 2


def entrypoint():
    sys.exit(main())


if __name__ == "__main__":
    entrypoint()
