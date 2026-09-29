#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time


MIN_BYTES_PER_SECOND = 256 * 1024
MAX_BYTES_PER_SECOND = 64 * 1024 * 1024
CHUNK_SIZE = 64 * 1024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Limita a taxa de um stream binário.")
    parser.add_argument("--bytes-per-second", required=True, type=int)
    args = parser.parse_args()
    if not MIN_BYTES_PER_SECOND <= args.bytes_per_second <= MAX_BYTES_PER_SECOND:
        parser.error(
            f"--bytes-per-second deve ficar entre {MIN_BYTES_PER_SECOND} e "
            f"{MAX_BYTES_PER_SECOND}"
        )
    return args


def copy_limited(*, bytes_per_second: int) -> None:
    started_at = time.monotonic()
    transferred = 0
    while chunk := sys.stdin.buffer.read(CHUNK_SIZE):
        transferred += len(chunk)
        expected_elapsed = transferred / bytes_per_second
        delay = expected_elapsed - (time.monotonic() - started_at)
        if delay > 0:
            time.sleep(delay)
        sys.stdout.buffer.write(chunk)
        sys.stdout.buffer.flush()


def main() -> None:
    args = parse_args()
    copy_limited(bytes_per_second=args.bytes_per_second)


if __name__ == "__main__":
    main()
