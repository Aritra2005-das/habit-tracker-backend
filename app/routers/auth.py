"""
Authentication router
Handles user registration and login endpoints with JWT tokens
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models import User
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    """User registration request model"""
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    """User login request model"""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Authentication response with tokens"""
    accessToken: str
    refreshToken: str
    user: dict


class TokenRefreshRequest(BaseModel):
    """Token refresh request model"""
    refreshToken: str


@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
) -> AuthResponse:
    """
    Register new user with email and password
    
    Args:
        request: Registration request with email, password, and name
        db: Database session
        
    Returns:
        AuthResponse with access token, refresh token, and user info
        
    Raises:
        HTTPException: If email already exists or validation fails
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_valid, error_msg = AuthService.validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Hash password and create user
    hashed_password = AuthService.hash_password(request.password)
    new_user = User(
        email=request.email,
        password_hash=hashed_password,
        name=request.name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate tokens
    access_token, refresh_token = AuthService.create_tokens(new_user.id)
    
    return AuthResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        user={
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name
        }
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
) -> AuthResponse:
    """
    Login user with email and password
    
    Args:
        request: Login request with email and password
        db: Database session
        
    Returns:
        AuthResponse with access token, refresh token, and user info
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not AuthService.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate tokens
    access_token, refresh_token = AuthService.create_tokens(user.id)
    
    return AuthResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    )


@router.post("/refresh", response_model=dict)
async def refresh_token(request: TokenRefreshRequest) -> dict:
    """
    Refresh access token using refresh token
    
    Args:
        request: Request with refresh token
        
    Returns:
        New access token
        
    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    payload = AuthService.verify_token(request.refreshToken)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("sub")
    new_access_token = AuthService.create_access_token({"sub": user_id})
    
    return {"accessToken": new_access_token}


@router.post("/logout")
async def logout() -> dict:
    """
    Logout user (token invalidation handled client-side)
    
    Returns:
        Success message
    """
    return {"message": "Logged out successfully"}
