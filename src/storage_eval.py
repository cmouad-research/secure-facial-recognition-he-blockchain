from src.he_ckks import make_context, encrypt_vector, ciphertext_bytes
from src.embeddings import get_embedding
import numpy as np

N = 10  # nombre d’échantillons test

ctx = make_context()
sizes = []

for i in range(N):
    emb = get_embedding(i)
    ct = encrypt_vector(ctx, emb)
    ct_bytes = ciphertext_bytes(ct)
    sizes.append(len(ct_bytes))

avg_size = sum(sizes) / len(sizes)

print("Average ciphertext size (bytes):", avg_size)
print("Average ciphertext size (KB):", avg_size / 1024)
