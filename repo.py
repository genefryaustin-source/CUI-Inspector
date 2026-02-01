import hashlib
from pathlib import Path

REPO_DIR = Path("data") / "repo"
REPO_DIR.mkdir(parents=True, exist_ok=True)

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def object_relpath(sha256_hex: str) -> str:
    return f"objects/{sha256_hex[:2]}/{sha256_hex}"

def write_object(data: bytes):
    sha = sha256_bytes(data)
    rel = object_relpath(sha)
    path = REPO_DIR / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(data)
    return sha, rel, len(data)

def read_object(rel: str) -> bytes:
    return (REPO_DIR / rel).read_bytes()

def verify_object(rel: str, expected_sha: str):
    data = read_object(rel)
    actual = sha256_bytes(data)
    return (actual == expected_sha), actual
