import base64
import hashlib
import hmac
import time

def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or hashlib.sha256(f"{time.time_ns()}:{password}".encode()).digest()[:16]
    derived = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32, maxmem=64 * 1024 * 1024)
    return f"scrypt$16384$8$1${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(derived).decode()}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt, expected = encoded.split("$", 5)
        if algorithm != "scrypt": return False
        derived = hashlib.scrypt(password.encode(), salt=base64.urlsafe_b64decode(salt), n=int(n), r=int(r), p=int(p), dklen=32, maxmem=64 * 1024 * 1024)
        return hmac.compare_digest(base64.urlsafe_b64encode(derived).decode(), expected)
    except (TypeError, ValueError): return False
