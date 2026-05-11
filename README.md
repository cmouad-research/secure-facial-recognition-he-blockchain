# Privacy-Preserving Facial Authentication using Homomorphic Encryption, IPFS, and Blockchain Governance

## Overview

This repository contains the prototype implementation and experimental framework developed for the study **"Privacy-Preserving Facial Authentication using Homomorphic Encryption and Blockchain-based Governance."**

The system proposes a privacy-preserving biometric authentication architecture that combines deep facial embeddings, CKKS homomorphic encryption, IPFS decentralized storage, and blockchain smart contracts for governance and audit logging.

The objective of this framework is to demonstrate that biometric authentication can be performed without exposing biometric templates or similarity scores, while still ensuring transparency, traceability, and auditability through blockchain-based governance.

## System Architecture

The framework follows a three-layer architecture:

### 1. Biometric Processing Layer

This layer is responsible for:

- Facial embedding extraction using InsightFace
- Homomorphic encryption of biometric templates
- Encrypted similarity computation

### 2. Storage Layer

Encrypted biometric templates are stored in IPFS, providing decentralized and content-addressed storage. Only encrypted vectors are stored. No plaintext biometric data is exposed.

### 3. Governance Layer

A blockchain smart contract acts as a control plane responsible for:

- Identity enrollment
- Authentication request registration
- Authentication decision validation
- Audit logging

The blockchain stores only metadata and cryptographic hashes, which preserves biometric privacy.

## Repository Structure

```text
fr-he-blockchain-authentication/
├── src/
│   ├── embeddings.py
│   ├── he_ckks.py
│   ├── he_context.py
│   ├── ipfs_client.py
│   ├── chain_client.py
│   ├── chain_utils.py
│   ├── chain_enroll_ipfs.py
│   ├── chain_auth_ipfs.py
│   ├── bench.py
│   └── analyze.py
│
├── control-plane/
│   ├── contracts/
│   │   └── ControlPlane.sol
│   ├── abi/
│   │   └── ControlPlane.json
│   └── DEPLOYED_ADDRESS
│
├── results/
│   ├── raw/
│   └── processed/
│
├── figures/
├── docs/
├── requirements.txt
├── LICENSE
├── CITATION.cff
└── README.md
```
## Main Components

### Facial Embeddings

Facial embeddings are extracted using InsightFace ArcFace, producing 512-dimensional feature vectors.

**File:** `src/embeddings.py`

### Homomorphic Encryption

Biometric templates are encrypted using the CKKS homomorphic encryption scheme implemented with TenSEAL.

#### Encryption Parameters

| Parameter | Value |
|-----------|-------|
| Scheme | CKKS |
| Polynomial modulus degree | 8192 |
| Coefficient modulus | [60, 40, 40, 60] |
| Global scale | 2^40 |
| Embedding dimension | 512 |

**Relevant files:**

- `src/he_ckks.py`
- `src/he_context.py`

### Decentralized Storage (IPFS)

Encrypted biometric templates are stored in IPFS. The blockchain stores only the hash of the corresponding IPFS CID.

**File:** `src/ipfs_client.py`

### Blockchain Governance Layer

The control plane is implemented using a Solidity smart contract.

Its main responsibilities include:

- Identity registration
- Authentication request logging
- Authentication decision validation
- Auditability of authentication operations

**Smart contract:** `control-plane/contracts/ControlPlane.sol`

**Blockchain interaction files:**

- `src/chain_client.py`
- `src/chain_utils.py`

## Experimental Evaluation

The repository includes a benchmarking framework used to evaluate:

- Biometric authentication accuracy
- Homomorphic computation latency
- Decentralized storage latency
- Blockchain governance overhead

**Benchmark tool:** `src/bench.py`  
**Result analysis:** `src/analyze.py`

## Dataset

Experiments were conducted using a controlled subset of the Labeled Faces in the Wild (LFW) dataset.

The dataset was loaded using:

```python
fetch_lfw_people(min_faces_per_person=5, resize=0.5)

### Evaluation Protocol

- 1 image is used for enrollment
- The remaining images are used for authentication queries

This configuration generates both:

- Genuine authentication attempts
- Impostor authentication attempts

## Research Objective

This repository supports experimentation on secure and privacy-preserving facial authentication by combining encrypted biometric processing, decentralized storage, and blockchain-based governance.

The framework is designed to demonstrate that it is possible to:

- Protect biometric templates from direct exposure
- Perform similarity computation over encrypted data
- Store encrypted templates in a decentralized storage layer
- Ensure accountability and auditability through blockchain governance

## Citation

If you use this repository in academic work, please cite the associated study using the provided `CITATION.cff` file.
