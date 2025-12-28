from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import database
import schemas
import models
import auth_utils
from services.email_service import EmailService
import os

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse)
async def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    # Check if user already exists
    db_user = auth_utils.get_user(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = auth_utils.get_password_hash(user.password)
    db_user = models.Users(
        name=user.name,
        email=user.email,
        password_hash=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    # Authenticate user
    user = auth_utils.get_user(db, email=form_data.username)
    if not user or not auth_utils.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Handle role serialization (Enum vs String)
    role_value = user.role.value if hasattr(user.role, "value") else user.role
    
    access_token = auth_utils.create_access_token(
        data={"sub": user.email, "role": role_value},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": role_value
    }

@router.post("/forgot-password")
async def forgot_password(
    request: schemas.PasswordResetRequest, 
    db: Session = Depends(database.get_db)
):
    """
    Initiate password reset process. Sends an email with a reset token.
    """
    user = auth_utils.get_user(db, email=request.email)
    
    # We return 200 OK even if user is not found to prevent email enumeration attacks
    if not user:
        return {"message": "If the email exists, a password reset link has been sent."}
    
    # Generate a short-lived token for password reset (15 minutes)
    reset_token_expires = timedelta(minutes=15)
    reset_token = auth_utils.create_access_token(
        data={"sub": user.email, "type": "password_reset"},
        expires_delta=reset_token_expires
    )
    
    # Send email
    reset_link = f"http://localhost:5173/reset-password?token={reset_token}"
    await EmailService.send_email(
        to_email=user.email,
        subject="Password Reset Request",
        body=f"Click the link to reset your password: {reset_link}"
    )
    
    return {"message": "If the email exists, a password reset link has been sent."}

@router.post("/reset-password")
async def reset_password(
    request: schemas.PasswordResetConfirm,
    db: Session = Depends(database.get_db)
):
    """
    Verify token and reset user password.
    """
    email = auth_utils.verify_reset_token(request.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    user = auth_utils.get_user(db, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.password_hash = auth_utils.get_password_hash(request.new_password)
    db.commit()
    
    return {"message": "Password reset successfully"}