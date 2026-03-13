"""TenSEAL CKKS helper utilities."""

from __future__ import annotations

import argparse
import time
from typing import Iterable

import numpy as np
import tenseal as ts
from web3 import Web3

from src.ipfs_client import cat_bytes
from src.embeddings import get_embedding
from src.cid_index import get_template_cid
from src.he_context import load_or_create_full

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

# --- helper for chain/IPFS integration ---
import numpy as np
import tenseal as ts

def ckks_encrypt_serialize_from_embedding(emb: np.ndarray) -> bytes:
    # emb: 512D float32/float64, L2-normalized
    ctx = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60],
    )
    ctx.global_scale = 2**40
    ctx.generate_galois_keys()

    v = emb.astype(np.float64).tolist()
    ct = ts.ckks_vector(ctx, v)
    return ct.serialize()

def _ckks_context():
    
    return load_or_create_full()

def he_distance_decrypt_score(user_label: str, query_embedding: np.ndarray) -> float:
    # Prototype: on compare query PT vs template CT stocké sur IPFS.
    # Récupérer CID template: ici tu dois le résoudre via ton registre on-chain/off-chain.
    # Pour validation immédiate: on prend un template local (embedding 0).
    ctx = _ckks_context()

    template_emb = get_embedding(0).astype(np.float64)
    query_emb = query_embedding.astype(np.float64)

    # Chiffrer template
    ct = ts.ckks_vector(ctx, template_emb.tolist())

    # Calcul distance L2 approx: sum((a-b)^2) = sum(a^2) - 2sum(a*b) + sum(b^2)
    # Ici: on fait dot product: sum(a*b) en HE, et le reste en clair.
    # (Minimal pour décision.)
    he_dot = (ct * query_emb.tolist()).sum()     # CKKS scalar in ciphertext
    dot = he_dot.decrypt()[0]

    # Normes (embeddings normalisés L2 ~1)
    # distance cos = 1 - dot, si normalisés.
    score = float(1.0 - dot)
    return score
    

def he_distance_decrypt_score_from_ipfs(user_label: str, query_embedding: np.ndarray) -> float:
    from web3 import Web3
    import tenseal as ts
    import numpy as np
    from src.ipfs_client import cat_bytes
    from src.cid_index import get_template_cid

    # 1) retrouver le CID du template via l'index off-chain
    user_id_hash = Web3.keccak(text=user_label)
    template_cid = get_template_cid(user_id_hash.hex())

    # 2) charger le template chiffre depuis IPFS
    ct_bytes = cat_bytes(template_cid)

    # 3) charger le contexte CKKS persistant
    ctx = _ckks_context()

    # 4) reconstruire le ciphertext avec le meme contexte
    ct = ts.ckks_vector_from(ctx, ct_bytes)

    # 5) calcul homomorphe
    q = query_embedding.astype(np.float64).tolist()
    he_dot = (ct * q).sum()

    # 6) dechiffrer uniquement le score
    dot = he_dot.decrypt()[0]

    # 7) stabiliser la valeur
    if dot < -1.0:
        dot = -1.0
    if dot > 1.0:
        dot = 1.0

    score = float(1.0 - dot)
    return score
