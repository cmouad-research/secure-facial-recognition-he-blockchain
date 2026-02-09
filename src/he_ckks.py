"""TenSEAL CKKS helper utilities."""

from __future__ import annotations

import argparse
import time
from typing import Iterable

import numpy as np
import tenseal as ts

from embeddings import get_embedding


def make_context() -> ts.Context:
    """Create a CKKS context with fixed parameters."""
    ctx = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60],
    )
    ctx.global_scale = 2**40
    ctx.generate_galois_keys()
    return ctx


def encrypt_vector(ctx: ts.Context, vec512: Iterable[float]) -> ts.CKKSVector:
    """Encrypt a 512-D vector using CKKS."""
    return ts.ckks_vector(ctx, list(vec512))


def decrypt_vector(ctx: ts.Context, ct: ts.CKKSVector) -> np.ndarray:
    """Decrypt a CKKS vector into float32 numpy array."""
    vals = ct.decrypt()
    return np.asarray(vals, dtype=np.float32)


def ciphertext_bytes(ct: ts.CKKSVector) -> bytes:
    """Serialize ciphertext to bytes."""
    return ct.serialize()


def _self_test() -> int:
    ctx = make_context()
    emb = get_embedding(0)

    t0 = time.perf_counter()
    ct = encrypt_vector(ctx, emb)
    t1 = time.perf_counter()

    ct_bytes = ciphertext_bytes(ct)

    t2 = time.perf_counter()
    dec = decrypt_vector(ctx, ct)
    t3 = time.perf_counter()

    enc_ms = (t1 - t0) * 1000.0
    dec_ms = (t3 - t2) * 1000.0
    size_kb = len(ct_bytes) / 1024.0
    max_err = float(np.max(np.abs(dec - emb)))

    print(f"encrypt_ms={enc_ms:.3f}")
    print(f"ciphertext_kb={size_kb:.3f}")
    print(f"decrypt_ms={dec_ms:.3f}")
    print(f"max_abs_error={max_err:.6g}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="TenSEAL CKKS utility")
    parser.add_argument("--self-test", action="store_true", help="Run a quick self-test")
    args = parser.parse_args()

    if args.self_test:
        return _self_test()

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
