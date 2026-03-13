import json
from web3 import Web3

RPC_URL = "http://127.0.0.1:8545"
CP_ADDR = open("control-plane/DEPLOYED_ADDRESS").read().strip()

with open("control-plane/abi/ControlPlane.json") as f:
    abi = json.load(f)["abi"]

w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = w3.eth.contract(address=Web3.to_checksum_address(CP_ADDR), abi=abi)

print("Connected:", w3.is_connected())
print("Admin:", contract.functions.admin().call())

acct = w3.eth.accounts[0]

tx = contract.functions.setVerifier(acct, True).transact({"from": acct})
w3.eth.wait_for_transaction_receipt(tx)

print("Verifier set.")
import hashlib

user_id = Web3.keccak(text="orl_s01")
cid_hash = Web3.keccak(text="QmExampleCID")
key_version = 1

tx = contract.functions.enroll(user_id, cid_hash, key_version).transact({"from": acct})
w3.eth.wait_for_transaction_receipt(tx)

print("Enrolled.")

print("UserRec:", contract.functions.getUser(user_id).call())

