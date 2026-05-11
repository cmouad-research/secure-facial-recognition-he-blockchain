"""Embeddings utilities for LFW faces using ArcFace/InsightFace."""

from __future__ import annotations

import argparse
from typing import Optional

import numpy as np
from sklearn.datasets import fetch_lfw_people

try:
    import cv2  # type: ignore
except Exception as exc:  # pragma: no cover - import guard
    raise ImportError("opencv-python is required for image resizing") from exc

try:
    from insightface.app import FaceAnalysis  # type: ignore
except Exception as exc:  # pragma: no cover - import guard
    raise ImportError("insightface is required for ArcFace embeddings") from exc

_DATASET_IMAGES: Optional[np.ndarray] = None
_FACE_APP = None


def _load_dataset_images() -> np.ndarray:
    global _DATASET_IMAGES
    if _DATASET_IMAGES is None:
        dataset = fetch_lfw_people(min_faces_per_person=5, resize=0.5)
        _DATASET_IMAGES = dataset.images
    return _DATASET_IMAGES


def _load_face_app():
    global _FACE_APP
    if _FACE_APP is None:
        _FACE_APP = FaceAnalysis(
            name="buffalo_l",
            providers=["CPUExecutionProvider"],
        )
        _FACE_APP.prepare(ctx_id=-1, det_size=(640, 640))
    return _FACE_APP


def _get_recognition_model(app: FaceAnalysis):
    model = getattr(app, "models", {}).get("recognition")
    if model is None:
        raise RuntimeError("Recognition model not loaded in FaceAnalysis app")
    return model


def _preprocess_image(gray_img: np.ndarray, size: int = 112) -> np.ndarray:
    if gray_img.ndim != 2:
        raise ValueError(f"Expected 2D grayscale image, got shape {gray_img.shape}")
    if np.max(gray_img) <= 1.0:
        img_u8 = np.clip(gray_img * 255.0, 0, 255).astype(np.uint8)
    else:
        img_u8 = np.clip(gray_img, 0, 255).astype(np.uint8)
    rgb = np.stack([img_u8, img_u8, img_u8], axis=-1)
    rgb = cv2.resize(rgb, (size, size), interpolation=cv2.INTER_LINEAR)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return bgr


def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    vec = vec.astype(np.float32, copy=False)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.astype(np.float32, copy=False)


def get_embedding_from_image(image: np.ndarray) -> np.ndarray:
    """Return L2-normalized 512-D ArcFace embedding for a grayscale image array."""
    img_bgr = _preprocess_image(np.asarray(image), size=112)

    app = _load_face_app()
    faces = app.get(img_bgr)
    if faces:
        face = max(faces, key=lambda f: f.det_score)
        embedding = getattr(face, "normed_embedding", None)
        if embedding is None:
            embedding = face.embedding
        embedding = np.asarray(embedding)
    else:
        model = _get_recognition_model(app)
        embedding = model.get_feat(img_bgr)
        if embedding.ndim > 1:
            embedding = embedding[0]

    embedding = _l2_normalize(embedding)
    if embedding.shape[0] != 512:
        raise ValueError(f"Unexpected embedding dimension: {embedding.shape}")
    return embedding.astype(np.float32, copy=False)


def get_embedding(index: int | None = None, image: np.ndarray | None = None) -> np.ndarray:
    """Return L2-normalized 512-D ArcFace embedding from a dataset index or image array."""
    if image is not None:
        return get_embedding_from_image(image)
    if index is None:
        raise ValueError("Either index or image must be provided")

    images = _load_dataset_images()
    if not (0 <= index < images.shape[0]):
        raise IndexError(f"index out of range: {index}")
    return get_embedding_from_image(images[index])


def _self_test() -> int:
    emb = get_embedding(0)
    print(f"dim={emb.shape[0]}")
    print(f"l2_norm={np.linalg.norm(emb):.6f}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="LFW ArcFace embedding utility")
    parser.add_argument("--self-test", action="store_true", help="Run a quick self-test")
    args = parser.parse_args()

    if args.self_test:
        return _self_test()

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
