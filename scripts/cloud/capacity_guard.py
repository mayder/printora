#!/usr/bin/env python3
"""Guard disk-intensive operational work before creating temporary artifacts."""
import json
import shutil
import sys


def allowed(total: int, free: int) -> bool:
    return total > 0 and free * 100 >= total * 10


def main() -> int:
    usage = shutil.disk_usage("/var/lib/postgresql")
    ok = allowed(usage.total, usage.free)
    print(json.dumps({"event": "operational_capacity", "allowed": ok,
                      "free_percent": round(usage.free * 100 / usage.total, 2)}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
