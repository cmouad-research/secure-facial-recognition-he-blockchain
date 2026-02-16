"""Benchmark utilities."""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import time
from typing import Dict, List, Tuple

import numpy as np
import tenseal as ts
from sklearn.datasets import fetch_olivetti_faces

from embeddings import get_embedding
from he_ckks import make_context, encrypt_vector, decrypt_vector, ciphertext_bytes
from ipfs_client import add_bytes, cat_bytes, pin_add

_WARMUP_COUNT = 3
_PROCESS_START_NS = time.perf_counter_ns()
_FIRST_EMBED_DONE_NS: int | None = None


def _ms(start_ns: int, end_ns: int) -> float:
    return (end_ns - start_ns) / 1_000_000.0


def _record_first_embedding_done() -> None:
    global _FIRST_EMBED_DONE_NS
    if _FIRST_EMBED_DONE_NS is None:
        _FIRST_EMBED_DONE_NS = time.perf_counter_ns()


def _embedding_warmup(warmup_count: int) -> np.ndarray | None:
    emb = None
    for _ in range(warmup_count):
        emb = get_embedding(0)
        _record_first_embedding_done()
    return emb


def _cold_start_ms() -> float | None:
    if _FIRST_EMBED_DONE_NS is None:
        return None
    return _ms(_PROCESS_START_NS, _FIRST_EMBED_DONE_NS)


def _smoke() -> int:
    emb = _embedding_warmup(_WARMUP_COUNT)
    if emb is None:
        emb = get_embedding(0)
        _record_first_embedding_done()
    ctx = make_context()
    ct = encrypt_vector(ctx, emb)
    _ = decrypt_vector(ctx, ct)
    warm_cid = add_bytes(b"warmup")
    _ = cat_bytes(warm_cid)

    t_start = time.perf_counter_ns()

    t0 = time.perf_counter_ns()
    emb = get_embedding(0)
    t1 = time.perf_counter_ns()

    ctx = make_context()

    t2 = time.perf_counter_ns()
    ct = encrypt_vector(ctx, emb)
    t3 = time.perf_counter_ns()

    t4 = time.perf_counter_ns()
    ct_bytes = ciphertext_bytes(ct)
    t5 = time.perf_counter_ns()

    t6 = time.perf_counter_ns()
    cid = add_bytes(ct_bytes)
    t7 = time.perf_counter_ns()

    t8 = time.perf_counter_ns()
    got_bytes = cat_bytes(cid)
    t9 = time.perf_counter_ns()

    t10 = time.perf_counter_ns()
    ct2 = ts.ckks_vector_from(ctx, got_bytes)
    t11 = time.perf_counter_ns()

    t12 = time.perf_counter_ns()
    dec = decrypt_vector(ctx, ct2)
    t13 = time.perf_counter_ns()

    max_err = float(np.max(np.abs(dec - emb)))
    if max_err > 1e-3:
        print(f"error=max_abs_error {max_err:.6g}")
        return 1

    t_end = time.perf_counter_ns()

    measured_sum_ms = sum(
        [
            _ms(t0, t1),
            _ms(t2, t3),
            _ms(t4, t5),
            _ms(t6, t7),
            _ms(t8, t9),
            _ms(t10, t11),
            _ms(t12, t13),
        ]
    )

    print(f"embed_ms={_ms(t0, t1):.3f}")
    print(f"encrypt_ms={_ms(t2, t3):.3f}")
    print(f"serialize_ms={_ms(t4, t5):.3f}")
    print(f"ipfs_add_ms={_ms(t6, t7):.3f}")
    print(f"ipfs_cat_ms={_ms(t8, t9):.3f}")
    print(f"deserialize_ms={_ms(t10, t11):.3f}")
    print(f"decrypt_ms={_ms(t12, t13):.3f}")
    print(f"measured_sum_ms={measured_sum_ms:.3f}")
    print(f"end_to_end_ms={_ms(t_start, t_end):.3f}")
    return 0


def _orl_split() -> Tuple[Dict[int, int], Dict[int, List[int]]]:
    dataset = fetch_olivetti_faces()
    targets = np.asarray(dataset.target)
    template_idx: Dict[int, int] = {}
    query_idx: Dict[int, List[int]] = {}
    for subj in range(40):
        idxs = np.where(targets == subj)[0]
        idxs = np.sort(idxs)
        template_idx[subj] = int(idxs[0])
        query_idx[subj] = [int(i) for i in idxs[1:]]
    return template_idx, query_idx


def _auth_bench(
    tau: float,
    ipfs_mode: str,
    threads: int,
    query_encrypted: bool,
    n_impostor_per_query: int,
) -> int:
    run_id = time.strftime("%Y%m%dT%H%M%S")
    rng = random.Random(0)

    os.makedirs("results/raw", exist_ok=True)
    csv_path = os.path.join("results", "raw", f"auth_{run_id}.csv")
    meta_path = os.path.join("results", "raw", f"auth_{run_id}.json")

    # Warmup to avoid cold-start effects in embed_ms.
    emb = _embedding_warmup(_WARMUP_COUNT)
    if emb is None:
        emb = get_embedding(0)
        _record_first_embedding_done()

    ctx = make_context()
    ct = encrypt_vector(ctx, emb)
    _ = decrypt_vector(ctx, ct)
    warm_cid = add_bytes(b"warmup")
    _ = cat_bytes(warm_cid)

    template_idx, query_idx = _orl_split()

    # Enrollment
    template_cid: Dict[int, str] = {}
    template_emb: Dict[int, np.ndarray] = {}
    for subj in range(40):
        emb = get_embedding(template_idx[subj])
        template_emb[subj] = emb
        ct = encrypt_vector(ctx, emb)
        ct_bytes = ciphertext_bytes(ct)
        cid = add_bytes(ct_bytes)
        template_cid[subj] = cid
        if ipfs_mode == "pinned":
            pin_add(cid)

    # Metadata
    meta = {
        "run_id": run_id,
        "cold_start_ms": _cold_start_ms(),
        "ckks": {
            "poly_modulus_degree": 8192,
            "coeff_mod_bit_sizes": [60, 40, 40, 60],
            "global_scale": 2**40,
        },
        "ipfs_mode": ipfs_mode,
        "threads": threads,
        "dataset_split": {
            "template_index_by_subject": template_idx,
            "query_indices_by_subject": query_idx,
        },
        "warmup_count": _WARMUP_COUNT,
        "query_encrypted": query_encrypted,
        "n_impostor_per_query": n_impostor_per_query,
        "random_seed": 0,
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    header = [
        "run_id",
        "case",
        "subj_template",
        "subj_query",
        "embed_ms",
        "ipfs_cat_ms",
        "he_eval_ms",
        "decrypt_ms",
        "end_to_end_ms",
        "score",
        "decision",
        "tau",
    ]
    if query_encrypted:
        header.insert(5, "query_encrypt_ms")

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()

        for subj in range(40):
            for q_idx in query_idx[subj]:
                t_embed_start = time.perf_counter_ns()
                q = get_embedding(q_idx)
                t_embed_end = time.perf_counter_ns()
                embed_ms = _ms(t_embed_start, t_embed_end)

                comparisons = [("genuine", subj)]
                for _ in range(n_impostor_per_query):
                    other = subj
                    while other == subj:
                        other = rng.randrange(40)
                    comparisons.append(("impostor", other))

                for case, tmpl_subj in comparisons:
                    t_start = time.perf_counter_ns()

                    t_ipfs_start = time.perf_counter_ns()
                    ct_bytes = cat_bytes(template_cid[tmpl_subj])
                    t_ipfs_end = time.perf_counter_ns()

                    t_he_start = time.perf_counter_ns()
                    ct = ts.ckks_vector_from(ctx, ct_bytes)

                    query_encrypt_ms = None
                    if query_encrypted:
                        t_qe_start = time.perf_counter_ns()
                        q_ct = encrypt_vector(ctx, q)
                        t_qe_end = time.perf_counter_ns()
                        query_encrypt_ms = _ms(t_qe_start, t_qe_end)
                        ct_prod = ct * q_ct
                    else:
                        ct_prod = ct * q

                    ct_sum = ct_prod.sum()
                    t_he_end = time.perf_counter_ns()

                    t_dec_start = time.perf_counter_ns()
                    score_vals = ct_sum.decrypt()
                    score = float(score_vals[0])
                    t_dec_end = time.perf_counter_ns()

                    expected = float(np.dot(template_emb[tmpl_subj], q))
                    if abs(score - expected) > 1e-3:
                        print(f"error=score_mismatch expected={expected:.6g} got={score:.6g}")
                        return 1

                    decision = "accept" if score >= tau else "reject"
                    t_end = time.perf_counter_ns()

                    row = {
                        "run_id": run_id,
                        "case": case,
                        "subj_template": tmpl_subj,
                        "subj_query": subj,
                        "embed_ms": f"{embed_ms:.3f}",
                        "ipfs_cat_ms": f"{_ms(t_ipfs_start, t_ipfs_end):.3f}",
                        "he_eval_ms": f"{_ms(t_he_start, t_he_end):.3f}",
                        "decrypt_ms": f"{_ms(t_dec_start, t_dec_end):.3f}",
                        "end_to_end_ms": f"{_ms(t_start, t_end):.3f}",
                        "score": f"{score:.6g}",
                        "decision": decision,
                        "tau": f"{tau:.6g}",
                    }
                    if query_encrypted:
                        row["query_encrypt_ms"] = f"{query_encrypt_ms:.3f}"

                    writer.writerow(row)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmarks")
    parser.add_argument("--mode", choices=["smoke", "auth-bench"], help="Benchmark mode")
    parser.add_argument("--tau", type=float, default=0.30, help="Decision threshold")
    parser.add_argument(
        "--ipfs",
        choices=["pinned", "unpinned"],
        default="unpinned",
        help="IPFS pinning mode",
    )
    parser.add_argument("--threads", type=int, default=1, help="Thread count hint")
    parser.add_argument("--query-encrypted", action="store_true", help="Use CT-CT for queries")
    parser.add_argument(
        "--n_impostor_per_query",
        type=int,
        default=1,
        help="Impostor templates per query",
    )
    args = parser.parse_args()

    if args.mode == "smoke":
        return _smoke()
    if args.mode == "auth-bench":
        return _auth_bench(
            tau=args.tau,
            ipfs_mode=args.ipfs,
            threads=args.threads,
            query_encrypted=args.query_encrypted,
            n_impostor_per_query=args.n_impostor_per_query,
        )

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
