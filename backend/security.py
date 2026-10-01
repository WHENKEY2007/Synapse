"""
Synapse Knowledge Base - Security & Authentication Engine
Implements PBKDF2-SHA256 password hashing, standard HMAC-SHA256 JWT tokens,
and Role-Based Access Control (RBAC).
"""

import os
import hmac
import hashlib
import base64
import json
import time
from typing import Optional, Dict, Any, List
from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

JWT_SECRET = os.getenv("SYNAPSE_JWT_SECRET", "synapse-production-secret-key-2026-png4-secure")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 86400  # 24 hours

security_bearer = HTTPBearer(auto_error=False)

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def _b64url_decode(data_str: str) -> bytes:
    padding = '=' * (4 - (len(data_str) % 4)) if len(data_str) % 4 != 0 else ''
    return base64.urlsafe_b64decode((data_str + padding).encode('utf-8'))

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Generate salted PBKDF2-SHA256 password hash."""
    if not salt:
        salt = os.urandom(16).hex()
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return hashed, salt

def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verify password against stored salt and hash."""
    computed, _ = hash_password(password, salt)
    return hmac.compare_digest(computed, hashed)

def create_jwt_token(payload: Dict[str, Any], secret: str = JWT_SECRET) -> str:
    """Create a standard HS256 signed JSON Web Token."""
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    header_bytes = json.dumps(header, separators=(',', ':')).encode('utf-8')
    header_b64 = _b64url_encode(header_bytes)

    claims = dict(payload)
    if "exp" not in claims:
        claims["exp"] = int(time.time()) + TOKEN_EXPIRY_SECONDS
    if "iat" not in claims:
        claims["iat"] = int(time.time())

    payload_bytes = json.dumps(claims, separators=(',', ':')).encode('utf-8')
    payload_b64 = _b64url_encode(payload_bytes)

    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(secret.encode('utf-8'), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_jwt_token(token: str, secret: str = JWT_SECRET) -> Dict[str, Any]:
    """Validate and decode a signed HS256 JSON Web Token."""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Invalid JWT token format.")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    expected_sig = hmac.new(secret.encode('utf-8'), signing_input, hashlib.sha256).digest()

    provided_sig = _b64url_decode(sig_b64)
    if not hmac.compare_digest(expected_sig, provided_sig):
        raise ValueError("Invalid token signature.")

    payload_bytes = _b64url_decode(payload_b64)
    payload = json.loads(payload_bytes.decode('utf-8'))

    if "exp" in payload and payload["exp"] < time.time():
        raise ValueError("Token has expired.")

    return payload

def get_current_user(auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)) -> Dict[str, Any]:
    """Dependency to extract user identity from Authorization Bearer header, with demo fallback."""
    if not auth or not auth.credentials:
        # Default fallback for demo / UI local exploration
        return {
            "email": "alex.sterling@synapse.internal",
            "name": "Alex Sterling",
            "role": "Admin",
            "is_authenticated": False
        }
    try:
        payload = decode_jwt_token(auth.credentials)
        return {
            "email": payload.get("sub"),
            "name": payload.get("name", "User"),
            "role": payload.get("role", "Reviewer"),
            "is_authenticated": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired credentials: {str(e)}"
        )

def require_roles(allowed_roles: List[str]):
    """Role-Based Access Control decorator/dependency."""
    def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        role = user.get("role")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires one of roles {allowed_roles}. Current role: {role}"
            )
        return user
    return role_checker
