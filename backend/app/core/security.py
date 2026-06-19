from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from jose import jwt, JWTError

# Workaround for compatibility between passlib and bcrypt 4.0.0+ in Python 3.11+
import bcrypt
if not hasattr(bcrypt, "__about__"):
    class BcryptAbout:
        __version__ = bcrypt.__version__
    bcrypt.__about__ = BcryptAbout
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

import httpx
from jose import jwk

_jwks_cache = None

def get_jwks(supabase_url: str, force_refresh: bool = False) -> Optional[dict]:
    global _jwks_cache
    if _jwks_cache is not None and not force_refresh:
        return _jwks_cache
    try:
        # Construct the well-known JWKS URL
        jwks_url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        resp = httpx.get(jwks_url, timeout=5.0)
        if resp.status_code == 200:
            _jwks_cache = resp.json()
            return _jwks_cache
    except Exception as e:
        logger.error(f"Failed to fetch Supabase JWKS from {supabase_url}: {str(e)}")
    return None

def decode_access_token(token: str) -> Optional[str]:
    # 1. Try decoding with JWKS if it's an asymmetric token (e.g. ES256) or has a kid
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
        kid = header.get("kid")
        if kid and settings.SUPABASE_URL:
            # First try with cached keys
            jwks = get_jwks(settings.SUPABASE_URL)
            key_data = None
            if jwks:
                key_data = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
            
            # If not found in cache, force refresh
            if not key_data:
                jwks = get_jwks(settings.SUPABASE_URL, force_refresh=True)
                if jwks:
                    key_data = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
            
            if key_data:
                public_key = jwk.construct(key_data)
                decoded = jwt.decode(
                    token,
                    public_key,
                    algorithms=[alg],
                    options={"verify_aud": False}
                )
                return decoded.get("sub")
    except Exception as e:
        logger.debug(f"JWKS token verification failed: {str(e)}")

    # 2. Try decoding with Supabase JWT Secret if configured (HS256)
    if settings.SUPABASE_JWT_SECRET:
        try:
            decoded = jwt.decode(
                token, 
                settings.SUPABASE_JWT_SECRET, 
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
            return decoded.get("sub")
        except Exception as e:
            logger.debug(f"Supabase JWT decode failed: {str(e)}")

    # 3. Local HS256 Fallback
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token["sub"]
    except JWTError:
        return None

