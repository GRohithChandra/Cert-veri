import json
import os
from solcx import compile_standard, install_solc
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

GANACHE_URL = os.getenv("GANACHE_URL", "http://127.0.0.1:7545")
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

if not w3.is_connected():
    raise ConnectionError(f"Could not connect to Ganache at {GANACHE_URL}")

install_solc("0.8.0")

with open("contract/Certificate.sol", "r") as file:
    cert_sol = file.read()

compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"Certificate.sol": {"content": cert_sol}},
        "settings": {
            "outputSelection": {
                "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
            }
        },
    },
    solc_version="0.8.0",
)

bytecode = compiled_sol["contracts"]["Certificate.sol"]["CertificateRegistry"]["evm"]["bytecode"]["object"]
abi = compiled_sol["contracts"]["Certificate.sol"]["CertificateRegistry"]["abi"]

# Save ABI
os.makedirs("contract", exist_ok=True)
with open("contract/Certificate_abi.json", "w") as f:
    json.dump(abi, f, indent=4)

account = w3.eth.accounts[0]
CertificateRegistry = w3.eth.contract(abi=abi, bytecode=bytecode)

tx_hash = CertificateRegistry.constructor().transact({"from": account})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print("=" * 60)
print(f"Contract Deployed Successfully!")
print(f"Contract Address : {tx_receipt.contractAddress}")
print(f"Admin Account    : {account}")
print("=" * 60)
print("Copy this Contract Address into your .env file as CONTRACT_ADDRESS")