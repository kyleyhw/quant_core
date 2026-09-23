"""Fail if any tracked file names the private repository or its strategies.

The public platform must never contain, import or name private code, and this
check must not publish the names it looks for. So it stores only their SHA-256
hashes. Every identifier-like token in every tracked text file is hashed in
lower case, together with each of its prefixes of six or more characters, so a
longer name that begins with a private one is caught too. A hit prints the file
and line only, because CI logs for this repository are public.

To add a name, hash it and append the digest to HASHES:

    python tools/check_private_references.py --hash SomeName
"""

import hashlib
import re
import subprocess
import sys

HASHES = frozenset(
    {
        "ffb07be5d0e94c708043138ee4b7153640cc04aa17e762dd48532e65af295c27",
        "6188616936839b29496ee1e20813810391488a9e94f4db76898911d5f2e73149",
        "d726e8b43c8c55d36c45941eda67e9187d09e1612cb6fc614c10e7244918b38d",
        "f45adc7307d2209c7964facb26cb0c8a32ed3298290b67175ef0c300c39208e2",
        "e26a11c99c0c51f6bc56dd352c1336d6240a0662a01a4597c386695260cf9f47",
        "503aecc626e6deb3ff349b1f912b7bc724d98cd0999f35bf9d71c282d9fdd757",
        "9c34be28edf26c2c1e58a7f340be8a3fa39e73ff4fc5ac55002a90834f36bea0",
        "c583c22d76526e2774187b8f9c951f497fecb60e9b5425f52769bf4c18ceb2a4",
        "de68253cc42bc65f168b54a5feb1ff92c694c2ebfa683c0d2aa6254316806dae",
        "f8d65ffa843caf4e8978861d34e7c8f45abf93677578928dc303d220ffc11395",
        "946efaa5609f72790dc02559827f062192e86f10ef14b6b485fb089ce17c5a2a",
        "3008a0ff2d68c53deff6838971a3a98c551aa3fffd3a47ae7b38af2f8da573a6",
        "47d66676fd10d3971aa63412ddaaa4f33fbde29112dc2f1639ecd3721391d31e",
        "33c55557e0e118cb1c7ed0eb67d6b1dffd87a039eaa2eeb40b473e7f7938cce7",
        "617f1f1a2afe9e5bb062d847ef49d27e9eb7082f9507650e8eae3dc389452b80",
        "53535bcedaa06fa4495fde732d611f55b21078250326051a01a33bca271b125f",
        "8d7b8172074d94e096465a4a1c6e0bffaa72a9357e3a2dafc35339f7135dfb34",
        "8aa376e3cec01513ad858ae8cf4ccaaeee2458123e08bff08d8145485bde0e4d",
        "b6cd5b165607c0c16c5453823c061ab43da39f95ebab0bb131dff4907e71e91c",
        "de662a8c0b57643649d2873de8cc0e4a3d449242873fd8cbc8d07db7f55b9791",
        "7bd7975f214c938efd2b08894820eec226fbbc3624ca080079ff9ee01b4efbd0",
        "c36789309bb516119b9b69ed9ecb09ef9e48af604b3c00e6e4ebe50e067b7718",
        "ad02dba0ddf3a4afca26ba6f5dbed2a895da6cdb1ade094079c7304fdc72943b",
        "418ca535ef4c340d6f35969f226db17d08a56bdabc34de02d25c9fb88f38f635",
        "5f611ec3dbffa365d2f7f6f376342fce732ec061dc0b568f4b84a90b6fb8974d",
    }
)
TOKEN = re.compile(r"[A-Za-z0-9_\-]{6,}")
MIN_PREFIX = 6
# Market data and the lockfile are large and hold no names.
SKIP_SUFFIXES = (".csv", ".lock")


def digest(text: str) -> str:
    return hashlib.sha256(text.lower().encode()).hexdigest()


def is_private(token: str) -> bool:
    token = token.lower()
    return any(digest(token[:end]) in HASHES for end in range(MIN_PREFIX, len(token) + 1))


def main(argv: list[str]) -> int:
    if argv[:1] == ["--hash"] and len(argv) == 2:
        print(digest(argv[1]))
        return 0
    files = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True).stdout
    hits = []
    for raw in files.split(b"\0"):
        path = raw.decode()
        if not path or path.endswith(SKIP_SUFFIXES):
            continue
        try:
            with open(path, encoding="utf-8") as f:
                for lineno, line in enumerate(f, 1):
                    if any(is_private(t) for t in TOKEN.findall(line)):
                        hits.append(f"{path}:{lineno}")
        except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
            continue
    if hits:
        print("These lines name the private repository or one of its strategies:")
        print("\n".join(hits))
        return 1
    print("No private references.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
