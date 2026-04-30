#!/usr/bin/env python3
"""registry_verify.py — OSBuilder package registry existence gate.

Checks whether a package name exists on a public registry (npm, PyPI,
crates.io) before any install command runs. Defends against slopsquatting
(hallucinated package names) without downloading the package.

Exit codes:
  0 = package verified to exist (or network error — fail-open)
  1 = package does NOT exist on registry — BLOCK INSTALL

Pure stdlib — no third-party deps.
"""
from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request


def verify_npm(package_name: str, timeout: int = 10) -> bool:
    """Return True if the package exists on the npm registry, False if 404.

    Fail-open: network errors (URLError, OSError) return True because a network
    failure does not mean the package is hallucinated — only an explicit 404
    means "not found."
    """
    url = f"https://registry.npmjs.org/{package_name}"
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        return e.code != 404  # 404 = not found; other 4xx = network issue, not hallucinated
    except (urllib.error.URLError, OSError):
        return True  # fail-open: network error != hallucinated package


def verify_pypi(package_name: str, timeout: int = 10) -> bool:
    """Return True if the package exists on PyPI, False if 404.

    Fail-open: network errors return True.
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        return e.code != 404
    except (urllib.error.URLError, OSError):
        return True  # fail-open


def verify_cargo(package_name: str, timeout: int = 10) -> bool:
    """Return True if the crate exists on crates.io, False if 404.

    crates.io requires a User-Agent header; fail-open on network errors.
    """
    url = f"https://crates.io/api/v1/crates/{package_name}"
    req = urllib.request.Request(url, method="HEAD")
    req.add_header("User-Agent", "OSBuilder/1.0 (registry verification gate)")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        return e.code != 404
    except (urllib.error.URLError, OSError):
        return True  # fail-open


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 if package exists, 1 if not found."""
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="registry_verify",
        description="OSBuilder package registry existence gate.",
    )
    parser.add_argument("--pkg", required=True, help="Package name to verify")
    parser.add_argument(
        "--ecosystem",
        choices=("npm", "pip", "cargo"),
        required=True,
        help="Package ecosystem to check",
    )
    args = parser.parse_args(argv)

    verifiers = {"npm": verify_npm, "pip": verify_pypi, "cargo": verify_cargo}
    exists = verifiers[args.ecosystem](args.pkg)
    if not exists:
        sys.stderr.write(
            f"OSBuilder: package '{args.pkg}' not found on {args.ecosystem} registry. "
            f"Install blocked (slopsquatting defense).\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
