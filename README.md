# Privacy-Preserving Facial Authentication with Homomorphic Encryption, IPFS, and Blockchain Governance

## Overview
This repository contains the prototype implementation used to evaluate a privacy-preserving facial authentication framework based on:

- facial embeddings with InsightFace
- CKKS homomorphic encryption with TenSEAL
- decentralized encrypted storage with IPFS
- blockchain-based governance and audit logging

## Repository Structure

- `src/` : Python source code for embedding extraction, homomorphic encryption, IPFS integration, benchmarking, and analysis
- `control-plane/` : blockchain smart contract and deployment artifacts
- `figures/` : architecture and workflow figures used in the paper
- `docs/` : supplementary technical documentation

## Main Components

- `src/embeddings.py` : facial embedding extraction
- `src/he_ckks.py` : CKKS encryption and encrypted similarity evaluation
- `src/ipfs_client.py` : IPFS interaction layer
- `src/bench.py` : benchmarking framework
- `src/analyze.py` : result aggregation and analysis
- `src/chain_client.py` : blockchain interaction layer
- `control-plane/contracts/ControlPlane.sol` : governance smart contract

## Reproducibility

### 1. Create Python environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
### 2. Run enrollment
```bash
python -m src.chain_enroll_ipfs
```
###3. Run authentication
```bash
python -m src.chain_auth_ipfs
```
###4. Run benchmark
```bash
python -m src.bench --mode auth-bench --ipfs pinned --threads 1 --tau 0.30
```
###5. Analyze results
```bash
python -m src.analyze
```
Notes: 
The prototype uses software-based logical key isolation. No HSM or TEE was used in the experimental implementation.
