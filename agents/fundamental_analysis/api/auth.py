"""
API authentication module.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from config.settings import API_SECRET_KEY, API_ALGORITHM, API_TOKEN_EXPIRE_MINUTES
from database.operations import db_ops

logger = logging.getLogger("stock_analyzer.api.auth")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Models
class Token(BaseModel):
    """Token model."""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None


class User(BaseModel):
    """User model."""
    username: str
    email: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    """User in database model."""
    hashed_password: str


def verify_password(plain_password, hashed_password):
    """
    Verify a password against a hash.
    
    Args:
        plain_password (str): The plain text password.
        hashed_password (str): The hashed password.
        
    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Get a password hash.
    
    Args:
        password (str): The password to hash.
        
    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def get_user(username: str):
    """
    Get a user from the database.
    
    Args:
        username (str): The username to look up.
        
    Returns:
        UserInDB: The user if found, None otherwise.
    """
    user_doc = db_ops.find_one("users", {"username": username})
    if user_doc:
        return UserInDB(**user_doc)
    return None


def authenticate_user(username: str, password: str):
    """
    Authenticate a user.
    
    Args:
        username (str): The username.
        password (str): The password.
        
    Returns:
        UserInDB: The user if authentication succeeds, False otherwise.
    """
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create an access token.
    
    Args:
        data (dict): The data to encode.
        expires_delta (timedelta, optional): The expiration time delta. Defaults to None.
        
    Returns:
        str: The encoded access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, API_SECRET_KEY, algorithm=API_ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current user from a token.
    
    Args:
        token (str, optional): The token. Defaults to Depends(oauth2_scheme).
        
    Raises:
        HTTPException: If credentials can't be validated.
        
    Returns:
        User: The current user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, API_SECRET_KEY, algorithms=[API_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    Get the current active user.
    
    Args:
        current_user (User, optional): The current user. Defaults to Depends(get_current_user).
        
    Raises:
        HTTPException: If the user is disabled.
        
    Returns:
        User: The current active user.
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def register_user(username: str, email: str, password: str):
    """
    Register a new user.
    
    Args:
        username (str): The username.
        email (str): The email.
        password (str): The password.
        
    Returns:
        bool: True if registration succeeds, False otherwise.
    """
    try:
        # Check if user already exists
        existing_user = db_ops.find_one("users", {"username": username})
        if existing_user:
            return False
        
        # Create new user
        hashed_password = get_password_hash(password)
        user_doc = {
            "username": username,
            "email": email,
            "disabled": False,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow()
        }
        
        result = db_ops.insert_one("users", user_doc)
        return result is not None
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        return False