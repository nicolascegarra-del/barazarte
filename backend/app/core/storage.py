"""Almacenamiento de objetos (MinIO, compatible S3)."""

import json
import logging
from functools import lru_cache
from io import BytesIO
from typing import Protocol

from minio import Minio

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ObjectStorage(Protocol):
    def put(self, key: str, data: bytes, content_type: str) -> None: ...

    def delete(self, key: str) -> None: ...


class MinioStorage:
    def __init__(self) -> None:
        settings = get_settings()
        self._bucket = settings.minio_bucket_name
        self._client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def ensure_bucket(self) -> None:
        """Crea el bucket si no existe y habilita lectura anonima de objetos."""
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self._bucket}/*"],
                }
            ],
        }
        self._client.set_bucket_policy(self._bucket, json.dumps(policy))

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(
            self._bucket, key, BytesIO(data), length=len(data), content_type=content_type
        )

    def delete(self, key: str) -> None:
        self._client.remove_object(self._bucket, key)


@lru_cache
def get_storage() -> ObjectStorage:
    return MinioStorage()


def public_url(key: str) -> str:
    settings = get_settings()
    base = settings.minio_public_base_url.rstrip("/")
    return f"{base}/{settings.minio_bucket_name}/{key}"
