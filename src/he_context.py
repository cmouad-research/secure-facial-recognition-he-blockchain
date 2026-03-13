from pathlib import Path
import tenseal as ts

KEYDIR = Path("results/keys")
FULL_CTX = KEYDIR / "ckks_full.ctx"

def create_ctx():
    ctx = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60],
    )
    ctx.global_scale = 2**40
    ctx.generate_galois_keys()
    ctx.generate_relin_keys()
    return ctx

def load_or_create_full():
    KEYDIR.mkdir(parents=True, exist_ok=True)
    if FULL_CTX.exists():
        return ts.context_from(FULL_CTX.read_bytes())
    ctx = create_ctx()
    FULL_CTX.write_bytes(ctx.serialize(save_secret_key=True))
    return ctx
