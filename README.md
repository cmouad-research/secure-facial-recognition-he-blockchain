# A Comparative Evaluation of CT–PT and CT–CT Homomorphic Matching for Blockchain-Governed Facial Authentication

## Overview

This repository contains the prototype implementation and experimental framework developed for the study:

**"A Comparative Evaluation of CT–PT and CT–CT Homomorphic Matching for Blockchain-Governed Facial Authentication."**

The framework combines deep facial embeddings, CKKS homomorphic encryption, blockchain-based governance, and logical key lifecycle management to investigate privacy-preserving facial authentication.

The main objective of the study is to compare two homomorphic matching strategies:

- **Ciphertext–Plaintext (CT–PT):** the enrolled biometric template remains encrypted while the authentication query is processed in plaintext during homomorphic evaluation.
- **Ciphertext–Ciphertext (CT–CT):** both the enrolled template and the authentication query are encrypted before similarity computation.

The blockchain acts as a governance and audit layer rather than as a biometric storage or matching component. It records enrollment metadata, authentication requests, key-version information, and final authentication decisions while biometric templates remain off-chain.

The prototype is evaluated using a filtered subset of the Labeled Faces in the Wild (LFW) dataset containing **5,985 images from 423 identities**.

---

## System Architecture

The proposed framework separates biometric processing, homomorphic matching, blockchain-based governance, and key management into distinct functional components.

### 1. Biometric Processing

Facial images are transformed into 512-dimensional embeddings using InsightFace with an ArcFace-based recognition model.

The biometric processing stage is responsible for:

- face detection and alignment;
- ArcFace embedding extraction;
- 512-dimensional feature representation;
- embedding normalization.

No blockchain operation is involved in feature extraction.

---

### 2. Homomorphic Matching

Biometric templates are protected using the CKKS approximate homomorphic encryption scheme implemented with TenSEAL.

The framework evaluates two matching configurations.

#### CT–PT Matching

In CT–PT mode:

- the enrolled reference embedding is encrypted;
- the authentication query remains in plaintext;
- similarity computation is performed between a ciphertext template and a plaintext query.

This mode reduces homomorphic computation overhead while protecting the enrolled biometric database.

#### CT–CT Matching

In CT–CT mode:

- the enrolled reference embedding is encrypted;
- the authentication query is also encrypted;
- similarity computation is performed entirely between ciphertext operands.

This configuration provides stronger query confidentiality at the cost of additional homomorphic computation.

---

### 3. Blockchain Governance

The blockchain forms a separate governance plane and does not perform biometric matching.

The control-plane smart contract governs three principal operations:

- `enroll()` — registration of enrollment metadata;
- `requestAuth()` — registration of an authentication request;
- `decide()` — recording of the final authentication decision.

The blockchain stores governance metadata rather than biometric templates.

Depending on the operation, recorded information includes:

- hashed user identifiers;
- protected-template metadata;
- key-version information;
- authentication request identifiers;
- timestamps;
- authentication decisions;
- cryptographic hashes associated with decision information.

**No plaintext facial embedding or biometric template is stored on-chain.**

The blockchain therefore provides:

- authentication traceability;
- tamper-evident logging;
- enrollment governance;
- decision auditing;
- key-version tracking.

---

### 4. Logical Key Lifecycle Management

The experimental architecture includes a logical Key Lifecycle Management (KLM) boundary responsible for CKKS key material.

In the current prototype, the KLM represents a **logical trust boundary** rather than a production-grade hardware-isolated key-management system.

The current implementation does not claim:

- HSM-backed secret-key isolation;
- Trusted Execution Environment protection;
- distributed key custodianship;
- automated production-grade key rotation.

Key-version metadata is nevertheless represented in the blockchain governance layer, providing the architectural basis for future key rotation and revocation mechanisms.

---

## Homomorphic Encryption Parameters

The following CKKS configuration is used throughout the evaluation:

| Parameter | Value |
|---|---:|
| Scheme | CKKS |
| Polynomial modulus degree | 8192 |
| Coefficient modulus | [60, 40, 40, 60] |
| Global scale | 2^40 |
| Embedding dimension | 512 |

CKKS is used because facial embeddings consist of real-valued feature vectors and similarity computation requires approximate numerical operations.

---

## Repository Structure

The principal components of the repository are organized as follows:

```text
secure-facial-recognition-he-blockchain/
│
├── src/
│   ├── embeddings.py
│   ├── he_ckks.py
│   ├── he_context.py
│   ├── chain_client.py
│   ├── chain_utils.py
│   ├── bench_no_ipfs.py
│   ├── analyze.py
│   └── ...
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
│   ├── processed/
│   └── figures/
│
├── docs/
├── requirements.txt
├── LICENSE
├── CITATION.cff
└── README.md
```

Legacy scripts from earlier development iterations may remain in the repository but are not part of the experimental configuration reported in the current manuscript.

---

## Main Components

### Facial Embeddings

Facial representations are generated using InsightFace / ArcFace.

Each detected face is represented by a normalized:

```text
512-dimensional embedding
```

Relevant implementation:

```text
src/embeddings.py
```

---

### CKKS Homomorphic Encryption

The CKKS implementation is based on TenSEAL.

Relevant files include:

```text
src/he_ckks.py
src/he_context.py
```

Encrypted templates remain protected during similarity evaluation.

---

### Blockchain Control Plane

The governance plane is implemented through an Ethereum-compatible Solidity smart contract.

Smart contract:

```text
control-plane/contracts/ControlPlane.sol
```

Relevant client-side components include:

```text
src/chain_client.py
src/chain_utils.py
```

The blockchain is used for governance and auditability rather than biometric storage.

---

## Dataset

Experiments use the LFW dataset loaded through scikit-learn with:

```python
fetch_lfw_people(
    min_faces_per_person=5,
    resize=0.5
)
```

After filtering, the resulting evaluation dataset contains:

```text
5,985 facial images
423 identities
```

The experiment does **not** use the official LFW 6,000-pair verification protocol.

Instead, a dedicated enrollment/authentication protocol is constructed from the filtered dataset.

---

## Enrollment Protocol

For each identity, image indices are sorted and the image associated with the lowest dataset index is deterministically selected as the enrollment reference.

The remaining images of the same identity are used as authentication queries.

Therefore:

```text
Enrollment references: 423
Authentication query images: 5,562
```

The deterministic enrollment procedure ensures that the same reference image is used across all experimental configurations.

---

## Authentication Trial Generation

Each non-enrollment query generates exactly two authentication trials.

### Genuine Trial

The query is compared with the enrolled template belonging to the same identity.

### Impostor Trial

The same query is compared with one enrolled template belonging to a different identity.

The impostor evaluation is therefore **not exhaustive**: each query is compared with one non-matching identity rather than with all remaining enrolled identities.

The resulting evaluation set contains:

```text
Genuine trials:   5,562
Impostor trials:  5,562
Total trials:    11,124
```

Thus, genuine and impostor trials are balanced.

The same predefined trial set is reused across CT–PT and CT–CT configurations to ensure a fair comparison.

---

## Authentication Threshold

Authentication decisions are produced by comparing the decrypted similarity score against an operational threshold:

```text
τ = 0.20
```

A threshold analysis was performed at:

```text
τ = 0.15
τ = 0.20
τ = 0.25
τ = 0.30
```

The measured CT–PT results were:

| Threshold | FAR | FRR | Accuracy |
|---:|---:|---:|---:|
| 0.15 | 7.25% | 3.92% | 94.42% |
| 0.20 | 2.19% | 6.31% | 95.75% |
| 0.25 | 0.56% | 9.80% | 94.82% |
| 0.30 | 0.18% | 14.67% | 92.57% |

Among the evaluated discrete operating points, `τ = 0.20` provides the highest authentication accuracy while substantially reducing the false acceptance rate compared with `τ = 0.15`.

The ROC analysis additionally produced:

```text
EER:            4.25%
EER threshold:  0.1744
AUC:            0.9855
```

The EER threshold and the operational threshold serve different purposes.

The EER threshold identifies the point at which FAR and FRR are approximately balanced, whereas `τ = 0.20` is retained as the operational point to favor a lower false acceptance rate.

---

## Experimental Configurations

Both CT–PT and CT–CT modes are evaluated under three benchmark concurrency configurations:

```text
1 worker
4 workers
8 workers
```

The thread-count parameter controls the number of **concurrent authentication workers used by the benchmark**.

It does not configure the internal number of threads assigned to an individual CKKS operation.

Therefore, the experiment evaluates application-level authentication concurrency rather than internal TenSEAL/SEAL multithreading.

---

## Homomorphic Matching Performance

For the single-worker configuration, the measured mean homomorphic evaluation latency is approximately:

| Matching mode | Mean HE latency |
|---|---:|
| CT–PT | 26.35 ms |
| CT–CT | 37.31 ms |

CT–CT therefore introduces additional homomorphic processing overhead because both operands are encrypted.

The two modes nevertheless preserve essentially the same authentication workflow and blockchain governance procedure.

---

## Blockchain Governance Overhead

Blockchain latency is measured separately from homomorphic computation.

Each authentication attempt contains two governance transactions:

1. authentication request registration;
2. final decision recording.

The resulting mean governance latency is:

| Configuration | Request registration | Decision recording | Total governance |
|---|---:|---:|---:|
| CT–PT, 1 worker | 39.68 ms | 41.69 ms | 81.37 ms |
| CT–PT, 4 workers | 39.19 ms | 41.79 ms | 80.98 ms |
| CT–PT, 8 workers | 39.02 ms | 41.71 ms | 80.73 ms |
| CT–CT, 1 worker | 40.54 ms | 43.25 ms | 83.79 ms |
| CT–CT, 4 workers | 40.04 ms | 42.63 ms | 82.67 ms |
| CT–CT, 8 workers | 39.82 ms | 42.76 ms | 82.59 ms |

The governance overhead remains relatively stable across matching modes and worker configurations.

This indicates that blockchain cost is largely independent of whether CT–PT or CT–CT homomorphic matching is selected.

The blockchain latency represents the cost of:

- request traceability;
- auditability;
- tamper-evident decision recording;
- governance metadata management.

It is not part of the biometric similarity computation itself.

---

## Latency Terminology

Latency values reported after feature extraction are referred to as:

```text
post-embedding authentication latency
```

rather than full end-to-end facial authentication latency.

This distinction is important because ArcFace feature extraction is measured separately and is not included in the post-embedding latency values.

For the single-worker configurations, the mean post-embedding authentication latency is approximately:

| Mode | Mean post-embedding latency |
|---|---:|
| CT–PT | 112.02 ms |
| CT–CT | 125.47 ms |

---

## Security Interpretation

The two matching modes provide different privacy/performance trade-offs.

### CT–PT

CT–PT protects the enrolled biometric database while providing lower homomorphic computation latency.

However, the query embedding remains available in plaintext during the matching stage.

### CT–CT

CT–CT encrypts both the enrolled template and the authentication query.

It therefore provides stronger query confidentiality but requires additional ciphertext processing.

The blockchain governance procedure remains the same in both modes.

---

## Reproducibility

The experimental protocol is designed to ensure that CT–PT and CT–CT are compared under equivalent conditions.

The following elements remain fixed across configurations:

- filtered LFW dataset;
- enrollment references;
- genuine trial definitions;
- impostor trial definitions;
- authentication threshold;
- CKKS parameters;
- blockchain governance workflow.

Only the homomorphic matching mode and benchmark concurrency configuration are varied.

---

## Scope and Limitations

The current repository represents a research prototype.

Important limitations include:

- blockchain evaluation is performed in an experimental deployment rather than a geographically distributed production network;
- the KLM is modeled as a logical trust boundary;
- hardware-backed secret-key isolation is not implemented;
- automated production-grade key rotation is not implemented;
- key-version metadata is supported architecturally, but complete key-rotation workflows remain future work;
- the impostor protocol uses one impostor comparison per query rather than exhaustive comparison against all enrolled identities.

These limitations should be considered when interpreting the experimental results.

---

## Legacy IPFS Components

Earlier versions of this research investigated IPFS-based storage for encrypted biometric templates.

IPFS is **not part of the experimental architecture evaluated in the current manuscript**.

Legacy IPFS-related scripts may remain in the repository for research history and reproducibility of previous experiments, but they should not be interpreted as components of the current CT–PT/CT–CT evaluation.

Where possible, legacy components should be moved to a dedicated directory such as:

```text
legacy/ipfs/
```

or:

```text
archive/ipfs/
```

to avoid confusion with the current implementation.

---

## Research Objective

The current study investigates whether blockchain-governed facial authentication can retain practical biometric and computational performance while protecting facial templates through homomorphic encryption.

The primary contributions evaluated by this repository are:

1. comparison of CT–PT and CT–CT homomorphic facial matching;
2. measurement of the security-performance trade-off between the two modes;
3. integration of blockchain-based enrollment and authentication governance;
4. decomposition of homomorphic, governance, and post-embedding authentication latency;
5. evaluation of biometric performance using FAR, FRR, accuracy, ROC, EER, and AUC.

---

## Citation

If you use this repository or its experimental results in academic work, please cite the associated study using the metadata provided in:

```text
CITATION.cff
```

The repository should be cited together with the version or commit corresponding to the published experimental results.
