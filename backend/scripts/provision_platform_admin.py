#!/usr/bin/env python3
"""Provisiona uma conta administrativa sem expor cadastro público."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.modules.identity.platform_admin_provisioning import provision_platform_admin


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password-file", type=Path, required=True)
    parser.add_argument("--display-name", default="Platform Admin")
    parser.add_argument("--initialize-empty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = provision_platform_admin(
        data_dir=args.data_dir,
        email=args.email,
        password_file=args.password_file,
        display_name=args.display_name,
        initialize_empty=args.initialize_empty,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
