"""Minimal IPFS HTTP API client."""

from __future__ import annotations

import argparse
import os
import time
from typing import Optional

import requests

_BASE_URL = "http://127.0.0.1:5001/api/v0"


def _post(endpoint: str, *, params: Optional[dict] = None, files: Optional[dict] = None) -> requests.Response:
    url = f"{_BASE_URL}/{endpoint}"
    resp = requests.post(url, params=params, files=files)
    resp.raise_for_status()
    return resp


def add_bytes(data: bytes) -> str:
    """Add bytes to IPFS and return CID."""
    resp = _post("add", files={"file": data})
    payload = resp.json()
    cid = payload.get("Hash") or payload.get("Cid") or payload.get("CID")
    if not cid:
        raise RuntimeError(f"Unexpected add response: {payload}")
    return str(cid)


def cat_bytes(cid: str) -> bytes:
    """Fetch bytes from IPFS by CID."""
    resp = _post("cat", params={"arg": cid})
    return resp.content


def pin_add(cid: str) -> None:
    """Pin a CID in IPFS."""
    _post("pin/add", params={"arg": cid})


def pin_rm(cid: str) -> None:
    """Unpin a CID in IPFS."""
    _post("pin/rm", params={"arg": cid})


def _ms_since(start_ns: int, end_ns: int) -> float:
    return (end_ns - start_ns) / 1_000_000.0


def _self_test() -> int:
    data = os.urandom(1 * 1024 * 1024)

    t0 = time.perf_counter_ns()
    cid = add_bytes(data)
    t1 = time.perf_counter_ns()
    print(f"add_ms={_ms_since(t0, t1):.3f}")
    print(f"cid={cid}")

    t2 = time.perf_counter_ns()
    pin_add(cid)
    t3 = time.perf_counter_ns()
    print(f"pin_ms={_ms_since(t2, t3):.3f}")

    t4 = time.perf_counter_ns()
    got = cat_bytes(cid)
    t5 = time.perf_counter_ns()
    print(f"cat_ms={_ms_since(t4, t5):.3f}")

    if got != data:
        print("error=content_mismatch")
        return 1

    t6 = time.perf_counter_ns()
    pin_rm(cid)
    t7 = time.perf_counter_ns()
    print(f"unpin_ms={_ms_since(t6, t7):.3f}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="IPFS HTTP API client")
    parser.add_argument("--self-test", action="store_true", help="Run a quick self-test")
    args = parser.parse_args()

    if args.self_test:
        return _self_test()

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
