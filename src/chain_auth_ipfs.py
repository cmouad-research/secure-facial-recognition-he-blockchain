import json
import time
from web3 import Web3

from src.chain_utils import cid_to_bytes32, make_req_id, score_commit
from src.ipfs_client import add_bytes
from src.embeddings import get_embedding
from src.he_ckks import ckks_encrypt_serialize_from_embedding, he_distance_decrypt_score_from_ipfs

RPC_URL = "http://127.0.0.1:8545"
CP_ADDR = open("control-plane/DEPLOYED_ADDRESS").read().strip()

with open("control-plane/abi/ControlPlane.json") as f:
    abi = json.load(f)["abi"]

w3 = Web3(Web3.HTTPProvider(RPC_URL))
cp = w3.eth.contract(address=Web3.to_checksum_address(CP_ADDR), abi=abi)

admin = w3.eth.accounts[0]
w3.eth.default_account = admin

def main():
    user_label = "lfw_s01"
    user_id_hash = Web3.keccak(text=user_label)

    emb_q = get_embedding(1)

    query_bytes = ckks_encrypt_serialize_from_embedding(emb_q)
    query_cid = add_bytes(query_bytes)
    query_cid_hash = cid_to_bytes32(query_cid)

    nonce = int(time.time()) & 0xFFFFFFFF
    ts = int(time.time())
    req_id = make_req_id(user_id_hash, query_cid_hash, nonce, ts)

    t0 = time.perf_counter()
    tx = cp.functions.requestAuth(req_id, user_id_hash, query_cid_hash).transact()
    w3.eth.wait_for_transaction_receipt(tx)
    chain_request_ms = (time.perf_counter() - t0) * 1000.0

    score = he_distance_decrypt_score_from_ipfs(user_label=user_label, query_embedding=emb_q)
    accepted = (score <= 0.30)

    score_pt_hash = score_commit(req_id, score)

    t1 = time.perf_counter()
    tx2 = cp.functions.decide(req_id, accepted, score_pt_hash).transact()
    w3.eth.wait_for_transaction_receipt(tx2)
    chain_decide_ms = (time.perf_counter() - t1) * 1000.0

    print("user_label:", user_label)
    print("query_cid:", query_cid)
    print("req_id:", req_id.hex())
    print("score:", score)
    print("accepted:", accepted)
    print("chain_request_ms:", round(chain_request_ms, 3))
    print("chain_decide_ms:", round(chain_decide_ms, 3))
    print("chain_total_ms:", round(chain_request_ms + chain_decide_ms, 3))

if __name__ == "__main__":
    main()
