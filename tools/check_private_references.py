"""Fail if any tracked file references the private strategies repository.

The public platform must never contain, import or name private code. The
changelog and the project plan are allowed to, because they describe the
separation itself.

The forbidden strings are assembled from pieces so this script does not match
itself.
"""

import subprocess
import sys

FORBIDDEN = ["strategies" + "_private", "quant" + "_strategies"]
ALLOWED = {"CHANGELOG.md", "PROJECT_PLAN.md"}


def main() -> int:
    files = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True).stdout.split(
        b"\0"
    )
    hits = []
    for raw in files:
        path = raw.decode()
        if not path or path in ALLOWED:
            continue
        try:
            with open(path, encoding="utf-8") as f:
                for lineno, line in enumerate(f, 1):
                    for needle in FORBIDDEN:
                        if needle in line:
                            hits.append(f"{path}:{lineno}: {line.strip()[:120]}")
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue
    if hits:
        print("Public files must not reference the private strategies repository:")
        print("\n".join(hits))
        return 1
    print("No private references.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
