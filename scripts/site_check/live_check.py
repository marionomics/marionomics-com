"""After the DNS switch: request every old Ghost path on the live site and report anything that is not
a 200 ending on https://marionomics.com<path> (so www and http:// inputs prove their redirects).
Standard library only.

Usage: python scripts/site_check/live_check.py redirects.txt [--base https://marionomics.com] [--expect https://marionomics.com]
"""
from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SITE = "https://marionomics.com"


def old_paths(redirects: Path) -> list[str]:
    return [line.split("\t")[0] for line in redirects.read_text(encoding="utf-8").splitlines() if line.strip()]


def http_status(url: str) -> tuple[int, str]:
    """Status and final URL after following HTTP redirects."""
    request = urllib.request.Request(url, headers={"User-Agent": "marionomics-live-check"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.geturl()
    except urllib.error.HTTPError as error:
        return error.code, error.geturl()


def check(paths, fetch, base: str, expect: str = SITE) -> list[str]:
    def one(path):
        try:
            status, final = fetch(base + path)
        except OSError as error:
            return f"{path}: error {error}"
        if status != 200:
            return f"{path}: {status}"
        return None if final == expect + path else f"{path}: ended at {final}"

    with ThreadPoolExecutor(max_workers=8) as pool:
        return [problem for problem in pool.map(one, paths) if problem]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("redirects", type=Path)
    parser.add_argument("--base", default=SITE)
    parser.add_argument("--expect", default=SITE, help="origin every request must end on")
    args = parser.parse_args(argv)
    paths = old_paths(args.redirects)
    problems = check(paths, http_status, args.base.rstrip("/"), args.expect.rstrip("/"))
    for problem in problems:
        print(problem)
    print(f"{len(paths) - len(problems)}/{len(paths)} OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
