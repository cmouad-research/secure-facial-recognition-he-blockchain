# Privacy–Performance Trade-offs in Homomorphic Facial Authentication: CT–PT and CT–CT Matching with Blockchain Governance

## Overview

This repository contains the prototype implementation and experimental framework developed for the study:

**"Privacy–Performance Trade-offs in Homomorphic Facial Authentication: CT–PT and CT–CT Matching with Blockchain Governance."**

The framework combines deep facial embeddings, CKKS homomorphic encryption, blockchain-based governance, and logical key-management functions to investigate privacy-preserving facial authentication.

The main objective of the study is to compare two homomorphic matching strategies:

- **Ciphertext–Plaintext (CT–PT):** the enrolled biometric template remains encrypted while the authentication query is processed in plaintext during homomorphic evaluation.
- **Ciphertext–Ciphertext (CT–CT):** both the enrolled template and the authentication query are encrypted before similarity computation.

The blockchain acts as a governance and audit layer rather than as a biometric storage or matching component. It records enrollment metadata, authentication requests, key-version information, and final authentication decisions while biometric templates and plaintext similarity scores remain off-chain.

The prototype is evaluated using a filtered subset of the Labeled Faces in the Wild (LFW) dataset containing **5,985 images from 423 identities**.

The study specifically investigates the additional computational cost of extending encryption from the enrolled biometric reference to the authentication query while keeping the biometric, cryptographic, and blockchain-governance workflow unchanged.

---

## System Architecture

The proposed framework separates biometric processing, homomorphic matching, blockchain-based governance, and logical key management into distinct functional components.

This separation makes it possible to evaluate the computational behavior of CT–PT and CT–CT matching independently from blockchain-governance overhead.

### 1. Biometric Processing

Facial images are transformed into 512-dimensional embeddings using InsightFace with an ArcFace-based recognition model.

The biometric-processing stage is responsible for:

- face detection and alignment;
- ArcFace embedding extraction;
- 512-dimensional feature representation;
- embedding normalization.

No blockchain operation is involved in feature extraction.

ArcFace feature extraction requires approximately **220 ms on average** in the experimental environment and is measured separately from the post-embedding authentication pipeline.

---

### 2. Homomorphic Matching

Biometric templates are protected using the CKKS approximate homomorphic encryption scheme implemented with TenSEAL.

The framework evaluates two matching configurations.

#### CT–PT Matching

In CT–PT mode:

- the enrolled reference embedding is encrypted;
- the authentication query remains in plaintext;
- similarity computation is performed between an encrypted reference and a plaintext query.

This mode reduces homomorphic-computation overhead while protecting the persistent enrolled biometric reference.

However, the query embedding remains available in plaintext to the matching environment.

#### CT–CT Matching

In CT–CT mode:

- the enrolled reference embedding is encrypted;
- the authentication query is also encrypted;
- similarity computation is performed between two ciphertext operands.

This configuration provides additional query confidentiality at the cost of additional homomorphic computation.

The privacy benefit of CT–CT assumes that the matching environment does not have access to the corresponding CKKS secret key.

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
- protected-template hashes;
- logical key-version information;
- authentication request identifiers;
- request states;
- timestamps;
- authentication decisions;
- cryptographic hashes associated with decision information.

The blockchain does **not** store:

- facial images;
- plaintext facial embeddings;
- encrypted biometric-template payloads;
- plaintext query embeddings;
- plaintext similarity scores.

The blockchain therefore provides:

- authentication traceability;
- tamper-evident logging;
- enrollment governance;
- decision auditing;
- identity-state management;
- logical key-version tracking.

---

### 4. Logical Key Lifecycle Management

The proposed architecture defines a logical Key Lifecycle Management (KLM) boundary responsible for CKKS key handling and controlled score decryption.

The intended architecture separates public encryption and evaluation material from the secret key. However, this separation is **not physically or hardware-enforced in the current experimental prototype**.

Three distinct key-related elements are involved:

1. the CKKS cryptographic context;
2. blockchain key-version metadata;
3. the Ethereum account used to submit governance transactions.

#### CKKS Cryptographic Context

The CKKS context contains the cryptographic material required for encryption, homomorphic evaluation, and score decryption.

In the current experimental implementation, the CKKS context is serialized with the secret key included using:

```python
save_secret_key=True
```

The benchmark variant also embeds this context in the enrollment artifact.

Consequently, the resulting experimental artifacts contain sufficient cryptographic material for decryption and do **not** provide independent secret-key isolation.

This design is suitable for controlled experimentation but should not be interpreted as production-grade key custody.

#### Blockchain Key-Version Metadata

The blockchain governance layer records a logical `keyVersion` associated with each enrollment.

In the current prototype:

```text
keyVersion = 1
```

The smart contract does not generate, store, or manage CKKS secret keys.

The key-version field provides a metadata foundation for future key renewal and template migration, but automated key rotation and template re-encryption are not implemented in the current prototype.

#### Ethereum Transaction Account

Governance transactions are submitted through the first account exposed by the local Ethereum-compatible RPC node.

The local Hardhat environment provides pre-funded and unlocked development accounts.

This configuration is appropriate for a controlled development environment but does not constitute production-grade blockchain account or private-key management.

#### Production-Oriented Key Management

The current prototype does not implement:

- HSM-backed secret-key isolation;
- Trusted Execution Environment protection;
- distributed key custodianship;
- protected external keystores;
- production-grade transaction signing;
- automated CKKS key rotation;
- automated biometric-template migration;
- hardware-backed decryption services.

These capabilities remain future extensions.

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
│   ├── roc_eer_noipfs.py
│   ├── plot_threshold_selection.py
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

Encrypted enrolled templates remain protected during similarity evaluation.

In CT–CT mode, the authentication query is also encrypted before matching.

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

The blockchain is used for governance and auditability rather than biometric storage or similarity computation.

The prototype uses a local Ethereum-compatible network deployed through Hardhat.

---

## Authentication Workflow

The authentication process is summarized as follows:

```text
Query facial image
        ↓
Face detection and alignment
        ↓
ArcFace feature extraction
        ↓
512-dimensional normalized embedding
        ↓
Matching mode selection
        ↓
   CT–PT or CT–CT
        ↓
Homomorphic similarity evaluation
        ↓
Encrypted scalar similarity score
        ↓
Logical KLM boundary
        ↓
Final-score decryption
        ↓
Threshold evaluation
        ↓
Accept / Reject decision
        ↓
Blockchain decision recording
```

In both modes, the homomorphic evaluator produces an encrypted scalar similarity score.

Only the final scalar score is intended to be decrypted through the logical KLM boundary.

The complete enrolled biometric embedding is not decrypted during homomorphic matching.

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
Enrollment references:          423
Authentication query images:  5,562
```

The deterministic enrollment procedure ensures that the same reference image is used across experimental configurations.

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
Genuine trials:    5,562
Impostor trials:   5,562
Total trials:     11,124
```

Thus, genuine and impostor trials are balanced.

The same authentication-trial definitions are used across CT–PT and CT–CT configurations to support a controlled comparison.

---

## Threshold Operating-Point Analysis

Authentication decisions are produced by comparing the decrypted similarity score against an operational threshold.

Four candidate operating points were evaluated:

```text
τ = 0.15
τ = 0.20
τ = 0.25
τ = 0.30
```

The measured CT–PT single-worker results were:

| Threshold | FAR | FRR | Accuracy |
|---:|---:|---:|---:|
| 0.15 | 7.25% | 3.92% | 94.42% |
| 0.20 | 2.19% | 6.31% | 95.75% |
| 0.25 | 0.56% | 9.80% | 94.82% |
| 0.30 | 0.18% | 14.67% | 92.57% |

Among the four evaluated discrete operating points:

```text
τ = 0.20
```

provides the highest observed authentication accuracy.

The threshold was therefore retained as the common operating point for reporting CT–PT and CT–CT performance.

### Important Methodological Note

The threshold analysis was performed using the same experimental score distribution used for reporting biometric performance.

Therefore, this procedure should be interpreted as an:

```text
operating-point analysis
```

rather than as independent threshold calibration on a held-out validation dataset.

No separate calibration split was used.

Consequently, `τ = 0.20` should not be interpreted as an independently validated threshold for unseen identities or different acquisition conditions.

---

## Biometric Performance

At the retained operating threshold:

```text
τ = 0.20
```

the reported performance is approximately:

| Metric | Result |
|---|---:|
| FAR | 2.19% |
| FRR | 6.31% |
| Accuracy | 95.75% |
| AUC | 0.9843 |
| EER | 4.71% |

ROC analysis yields:

```text
AUC:            0.9843
EER:            4.71%
EER threshold:  approximately 0.1697
```

The EER threshold and the selected operational threshold serve different purposes.

The EER threshold identifies the operating point at which FAR and FRR are approximately equal.

The operational threshold:

```text
τ = 0.20
```

was selected from the four explicitly evaluated operating points because it produced the highest observed authentication accuracy while providing a lower FAR than `τ = 0.15`.

CT–PT and CT–CT exhibit comparable biometric performance at the reported precision.

---

## Experimental Configurations

Both CT–PT and CT–CT modes are evaluated under three benchmark concurrency configurations:

```text
1 worker
4 workers
8 workers
```

This produces six experimental configurations:

```text
CT–PT, 1 worker
CT–PT, 4 workers
CT–PT, 8 workers

CT–CT, 1 worker
CT–CT, 4 workers
CT–CT, 8 workers
```

The worker-count parameter controls the number of **concurrent authentication workers used by the benchmark**.

It does not configure the internal number of threads assigned to an individual CKKS operation.

Therefore, the experiment evaluates application-level authentication concurrency rather than internal TenSEAL/SEAL multithreading.

Each experimental configuration processes:

```text
11,124 authentication trials
```

---

## Homomorphic Matching Performance

For the single-worker configuration, the measured mean homomorphic-evaluation latency is approximately:

| Matching mode | Mean HE latency |
|---|---:|
| CT–PT | 26.35 ms |
| CT–CT | 37.31 ms |

The increase from CT–PT to CT–CT is approximately:

```text
41.6%
```

at the homomorphic-processing stage.

This additional cost results from encrypting and processing both matching operands rather than evaluating an encrypted enrolled reference against a plaintext query.

The two modes otherwise use the same biometric and blockchain-governance workflow.

---

## Post-Embedding Authentication Latency

Latency values reported after facial feature extraction are referred to as:

```text
post-embedding authentication latency
```

rather than full end-to-end facial-authentication latency.

This distinction is important because ArcFace feature extraction is measured separately.

For the single-worker configurations:

| Mode | Mean post-embedding latency |
|---|---:|
| CT–PT | 112.02 ms |
| CT–CT | 125.47 ms |

CT–CT therefore introduces an increase of approximately:

```text
12%
```

in post-embedding authentication latency.

Although the homomorphic-processing stage increases by approximately 41.6%, the increase in the complete post-embedding authentication stage is smaller because blockchain-governance operations account for a substantial part of the processing time.

ArcFace feature extraction requires approximately:

```text
220 ms
```

on average and is measured separately.

---

## Blockchain Governance Overhead

Blockchain latency is measured separately from homomorphic computation.

Each authentication attempt contains two governance transactions:

1. authentication-request registration through `requestAuth()`;
2. final decision recording through `decide()`.

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

Blockchain governance therefore contributes approximately:

```text
82 ms per authentication attempt
```

in the local experimental deployment.

The measured governance overhead provides functionality independent of biometric similarity computation, including:

- authentication-request traceability;
- tamper-evident decision recording;
- identity-state management;
- key-version tracking;
- auditability.

---

## Interpretation of Blockchain Latency

The blockchain-governance procedure is identical for CT–PT and CT–CT.

Both modes invoke the same:

```text
requestAuth()
decide()
```

smart-contract operations.

The small observed differences between CT–PT and CT–CT blockchain latencies should therefore not be interpreted as an intrinsic blockchain cost of ciphertext–ciphertext matching.

They are attributed to normal runtime variability in:

- local transaction execution;
- Python processing;
- operating-system scheduling;
- the experimental blockchain environment.

---

## Experimental Blockchain Environment

The blockchain evaluation is performed using a local Ethereum-compatible Hardhat deployment.

The reported governance latency therefore characterizes execution under controlled experimental conditions.

The measurements do **not** include:

- network propagation between geographically distributed nodes;
- distributed validator coordination;
- production blockchain congestion;
- multi-validator consensus latency;
- geographically distributed network delays.

The blockchain results should therefore not be directly extrapolated to a decentralized production deployment.

---

## Security Interpretation

The two matching modes provide different privacy–performance trade-offs.

### CT–PT

CT–PT protects the enrolled biometric reference through CKKS encryption while providing lower homomorphic-computation latency.

However, the query embedding remains available in plaintext to the matching environment.

An adversary capable of observing the matching process may therefore obtain the query representation.

### CT–CT

CT–CT encrypts both the enrolled biometric reference and the authentication query before similarity evaluation.

The matching engine can therefore perform the similarity computation without requiring access to either plaintext operand.

This provides additional query confidentiality against an adversary observing the homomorphic evaluation process, provided that the corresponding CKKS secret key remains inaccessible.

CT–CT requires additional ciphertext processing and therefore introduces additional computation compared with CT–PT.

### Secret-Key Assumption

The confidentiality properties of both CT–PT and CT–CT depend on the secrecy of the CKKS decryption key.

The proposed architecture models secret-key separation through a logical KLM boundary.

However, the current experimental implementation serializes a CKKS context containing the secret key.

Consequently:

> The current prototype demonstrates the intended architectural separation and the privacy–performance trade-off between CT–PT and CT–CT, but it does not provide production-grade independent secret-key isolation.

A production deployment should isolate secret-key operations through mechanisms such as:

- Hardware Security Modules (HSMs);
- Trusted Execution Environments (TEEs);
- dedicated key-management services;
- distributed or threshold-key custody.

---

## ISO/IEC 24745 Alignment

The security analysis considers biometric-information protection objectives described in ISO/IEC 24745, including:

- confidentiality;
- irreversibility;
- unlinkability;
- renewability.

The study does **not** claim formal compliance with ISO/IEC 24745.

Instead, the implemented protection mechanisms are discussed in relation to the biometric protection objectives defined by the standard.

### Confidentiality

The enrolled biometric reference remains encrypted during homomorphic matching in both CT–PT and CT–CT.

CT–CT additionally encrypts the authentication query.

### Irreversibility

Protected biometric references are retained as CKKS ciphertexts rather than plaintext embeddings.

Recovering the underlying protected representation without the required secret-key material relies on the security assumptions of the CKKS scheme.

### Unlinkability

CKKS encryption is probabilistic, meaning that independent encryptions of the same embedding can produce different ciphertext representations.

However, persistent governance identifiers are intentionally retained for auditability.

The current prototype should therefore not be interpreted as providing complete cross-context unlinkability.

### Renewability

The blockchain records logical key-version metadata that could support future cryptographic-context renewal and template migration.

However, operational key rotation and automatic template re-encryption are not implemented in the current prototype.

---

## Reproducibility

The experimental protocol is designed to ensure that CT–PT and CT–CT are compared under equivalent conditions.

The following elements remain fixed across configurations:

- filtered LFW dataset;
- deterministic enrollment references;
- authentication query set;
- genuine trial definitions;
- impostor trial definitions;
- CKKS parameters;
- ArcFace representation;
- operational threshold;
- blockchain-governance workflow.

The experimental variables are:

```text
Matching mode:
    CT–PT
    CT–CT

Application-level concurrency:
    1 worker
    4 workers
    8 workers
```

This design enables a controlled comparison of the computational behavior of the two homomorphic matching configurations.

---

## Main Experimental Scripts

The principal scripts associated with the current evaluation include:

```text
src/bench_no_ipfs.py
src/roc_eer_noipfs.py
src/plot_threshold_selection.py
```

These scripts support:

- CT–PT evaluation;
- CT–CT evaluation;
- latency analysis;
- threshold operating-point analysis;
- ROC generation;
- AUC computation;
- EER computation.

Additional utility and legacy development scripts may also remain in the repository.

---

## Experimental Results

Experimental outputs are stored under:

```text
results/
```

Relevant directories may include:

```text
results/raw/
results/processed/
results/figures/
```

Generated experimental outputs include:

- raw authentication measurements;
- CT–PT results;
- CT–CT results;
- blockchain-governance measurements;
- threshold-analysis results;
- ROC curves;
- processed summaries;
- manuscript figures.

Representative figures include:

```text
results/figures/roc_ctpt_ctct.pdf
results/figures/roc_ctpt_ctct.png
results/figures/threshold_selection_final.pdf
results/figures/threshold_selection_final.png
```

---

## Privacy–Performance Trade-off

The experimental results indicate that CT–PT and CT–CT should be interpreted as complementary operating modes rather than as competing alternatives.

### CT–PT Advantages

- encrypted enrolled biometric reference;
- lower homomorphic-processing latency;
- lower post-embedding authentication latency.

### CT–PT Limitation

- authentication query remains available in plaintext to the matching environment.

### CT–CT Advantages

- encrypted enrolled biometric reference;
- encrypted authentication query;
- additional query confidentiality during matching.

### CT–CT Limitation

- greater homomorphic-processing cost.

For the single-worker configuration:

```text
CT–PT HE latency: 26.35 ms
CT–CT HE latency: 37.31 ms
```

which corresponds to approximately:

```text
41.6% additional homomorphic-processing latency
```

for CT–CT.

However, the post-embedding authentication latency increases from:

```text
112.02 ms
```

to:

```text
125.47 ms
```

which corresponds to approximately:

```text
12% additional post-embedding latency
```

This illustrates the distinction between the cost of homomorphic computation itself and the cost of the complete post-embedding authentication workflow.

---

## Scope and Limitations

The current repository represents a research prototype.

Important limitations include:

- blockchain evaluation is performed using a local single-node Hardhat deployment;
- distributed consensus is not evaluated;
- network propagation is not included in the reported blockchain latency;
- geographically distributed validator coordination is not evaluated;
- the KLM is modeled as a logical trust boundary;
- the experimental CKKS context is serialized with the secret key included;
- independent secret-key isolation is not implemented;
- hardware-backed key protection is not implemented;
- automated production-grade CKKS key rotation is not implemented;
- `keyVersion` is currently fixed to `1`;
- automated template migration is not implemented;
- automated template re-encryption is not implemented;
- governance transactions use an unlocked local development account;
- production-grade blockchain transaction signing is not implemented;
- the impostor protocol uses one impostor comparison per query rather than exhaustive comparison against all enrolled identities;
- the threshold is selected from the same experimental score distribution used for biometric evaluation;
- no independent threshold-calibration split is used;
- the evaluation uses a filtered LFW subset rather than the official LFW verification protocol;
- larger-scale biometric datasets remain to be evaluated;
- geographically distributed deployments remain future work.

These limitations should be considered when interpreting the experimental results.

---


---

## Research Contributions

The current study investigates whether blockchain-governed facial authentication can provide traceable authentication while protecting facial representations through homomorphic encryption.

The principal contributions evaluated by this repository are:

1. a unified blockchain-governed facial-authentication architecture supporting both CT–PT and CT–CT homomorphic matching;
2. a controlled comparison of CT–PT and CT–CT under identical biometric, cryptographic, and governance conditions;
3. a reproducible LFW-based protocol containing 5,985 images from 423 identities;
4. 5,562 genuine and 5,562 impostor trials, resulting in 11,124 authentication attempts per experimental configuration;
5. biometric evaluation using FAR, FRR, accuracy, ROC, AUC, and EER;
6. threshold operating-point analysis at `τ = 0.15`, `0.20`, `0.25`, and `0.30`;
7. latency decomposition separating homomorphic computation from blockchain-governance overhead;
8. evaluation under application-level concurrency settings of 1, 4, and 8 workers;
9. explicit analysis of the privacy–performance trade-off between CT–PT and CT–CT;
10. security analysis distinguishing the intended logical KLM architecture from the limitations of the experimental key-management implementation.

---

## Data Availability

The source code and experimental results supporting the study are publicly available through this repository.

The LFW dataset itself is **not redistributed** in this repository.

The dataset should be obtained from its original source or through the corresponding scikit-learn dataset interface.

The configuration used in this study is:

```python
fetch_lfw_people(
    min_faces_per_person=5,
    resize=0.5
)
```

To reproduce the reported experimental protocol, the same procedures should be used for:

- dataset filtering;
- deterministic enrollment-reference selection;
- genuine trial generation;
- impostor trial generation;
- ArcFace feature extraction;
- CKKS configuration;
- threshold operating-point analysis;
- CT–PT matching;
- CT–CT matching;
- blockchain-governance operations.

---

## Security Notice

This repository contains experimental research software and should not be deployed directly as a production biometric-authentication system.

CKKS contexts generated using:

```python
save_secret_key=True
```

contain secret cryptographic material.

Such experimental artifacts must not be treated as public-only cryptographic contexts.

Do not commit or distribute:

- production CKKS secret keys;
- real blockchain private keys;
- passwords;
- access tokens;
- credentials;
- sensitive biometric information.

A production-oriented implementation should use independent key custody, protected key storage, controlled decryption, and secure blockchain transaction signing.

---

## Publication

This repository accompanies the manuscript:

> **Privacy–Performance Trade-offs in Homomorphic Facial Authentication: CT–PT and CT–CT Matching with Blockchain Governance**

Authors:

- **Chaimaa MOUAD**


Ibn Tofail University.

The manuscript has been prepared for submission to the **Journal of Cybersecurity and Privacy**.

The repository may be updated following editorial or peer-review revisions.

For exact reproducibility of published results, the repository version or commit corresponding to the final publication should be used.

---

## Citation

If you use this repository, implementation, experimental protocol, or results in academic work, please cite the associated study.

Citation metadata is provided in:

```text
CITATION.cff
```

The citation information should be updated with the final publication details and DOI once available.

---

## License

Please refer to the:

```text
LICENSE
```

file for the terms governing use of the source code and associated material.

---

## Contact

**Chaimaa MOUAD**  
Ibn Tofail University  

Email:

```text
chaimaa.mouad@uit.ac.ma
```

---

## Disclaimer

This repository contains an experimental research prototype developed for evaluating privacy-preserving facial authentication using CKKS homomorphic encryption and blockchain-based governance.

It is not intended to serve directly as a production biometric-authentication, blockchain, or cryptographic key-management system without additional security engineering, independent secret-key isolation, deployment hardening, and validation.
