from web3 import Web3
import math

def cid_to_bytes32(cid: str) -> bytes:
    return Web3.keccak(text=cid)

def score_commit(req_id: bytes, score: float) -> bytes:
    if score is None or (isinstance(score, float) and (math.isnan(score) or math.isinf(score))):
        score = 0.0

    if score < 0.0:
        score = 0.0
    if score > 2.0:
        score = 2.0

    score_scaled = int(round(score * 1_000_000))
    return Web3.solidity_keccak(["bytes32", "uint64"], [req_id, score_scaled])

def make_req_id(user_id_hash: bytes, query_cid_hash: bytes, nonce: int, ts: int) -> bytes:
    return Web3.solidity_keccak(
        ["bytes32", "bytes32", "uint64", "uint64"],
        [user_id_hash, query_cid_hash, nonce, ts],
    )
