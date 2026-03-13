import json
import time
from web3 import Web3

class ChainClient:
    def __init__(self, rpc_url: str, abi_path: str, address_path: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        with open(abi_path, "r") as f:
            abi = json.load(f)["abi"]

        with open(address_path, "r") as f:
            addr = f.read().strip()

        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(addr),
            abi=abi
        )

        self.admin = self.w3.eth.accounts[0]
        self.w3.eth.default_account = self.admin

    def request_auth(self, req_id: bytes, user_id_hash: bytes, query_cid_hash: bytes) -> float:
        t0 = time.perf_counter()
        tx = self.contract.functions.requestAuth(req_id, user_id_hash, query_cid_hash).transact(
            {"from": self.admin}
        )
        self.w3.eth.wait_for_transaction_receipt(tx)
        return (time.perf_counter() - t0) * 1000.0

    def decide(self, req_id: bytes, accepted: bool, score_pt_hash: bytes) -> float:
        t0 = time.perf_counter()
        tx = self.contract.functions.decide(req_id, accepted, score_pt_hash).transact(
            {"from": self.admin}
        )
        self.w3.eth.wait_for_transaction_receipt(tx)
        return (time.perf_counter() - t0) * 1000.0
    def enroll(self, user_id_hash: bytes, cid_hash: bytes, key_version: int) -> float:
        t0 = time.perf_counter()
        tx = self.contract.functions.enroll(user_id_hash, cid_hash, key_version).transact(
            {"from": self.admin}
        )
        self.w3.eth.wait_for_transaction_receipt(tx)
        return (time.perf_counter() - t0) * 1000.0