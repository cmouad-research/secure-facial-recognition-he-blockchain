import json
from web3 import Web3

from src.chain_utils import cid_to_bytes32
from src.cid_index import set_template
from src.ipfs_client import add_bytes
from src.he_ckks import ckks_encrypt_serialize_from_embedding
from src.embeddings import get_embedding

RPC_URL = "http://127.0.0.1:8545"
CP_ADDR = open("control-plane/DEPLOYED_ADDRESS").read().strip()

with open("control-plane/abi/ControlPlane.json") as f:
    abi = json.load(f)["abi"]

w3 = Web3(Web3.HTTPProvider(RPC_URL))
cp = w3.eth.contract(address=Web3.to_checksum_address(CP_ADDR), abi=abi)

admin = w3.eth.accounts[0]
w3.eth.default_account = admin

def main():
    user_label = "orl_s01"
    user_id_hash = Web3.keccak(text=user_label)

    emb = get_embedding(0)
    payload_bytes = ckks_encrypt_serialize_from_embedding(emb)

    cid = add_bytes(payload_bytes)
    cid_hash = cid_to_bytes32(cid)

    set_template(
        user_id_hash.hex(),
        template_cid=cid,
        template_cid_hash_hex=cid_hash.hex(),
        key_version=1,
    )

    tx = cp.functions.enroll(user_id_hash, cid_hash, 1).transact({"from": admin})
    w3.eth.wait_for_transaction_receipt(tx)

    rec = cp.functions.getUser(user_id_hash).call()
    print("user_label:", user_label)
    print("cid:", cid)
    print("cid_hash_hex:", cid_hash.hex())
    print("UserRec:", rec)

if __name__ == "__main__":
    main()
