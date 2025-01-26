from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from ..database import get_db
from sqlalchemy.orm import Session
from ..models import User
from ..auth import verify_password, hash_password, JWTBearer, verify_access_token, oauth2_scheme
from ..schemas import UserCreate, UserResponse, UserLogin, Token, VerifyAccessToken
from sqlalchemy import or_

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if the username already exists
    existing_user = db.query(User).filter(or_(User.username == user.username, User.email==user.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username or email already registered",
        )
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=400,
            detail = "Password and Confirm Password are different"
        )
    # Hash the password and create a new user
    hashed_password = hash_password(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_password, first_name=user.first_name, last_name=user.last_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Refresh the instance to return it
    return new_user


@router.post("/token", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()

    # Check if the user exists and the password is correct
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    authorize = JWTBearer()
    # Create a JWT token
    access_token = authorize.create_access_token(user.username)
    return {"access_token": access_token, "token_type": "bearer", "username":user.username}


@router.get("/verify-token", response_model=VerifyAccessToken)
def verify_token(token: str= Depends(oauth2_scheme)):
    """
    Verifies the JWT token passed in the authorization header.
    The token is extracted using OAuth2PasswordBearer.
    """
    try:
        # Decode and verify the token
        decoded_token = verify_access_token(token)
        if not decoded_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Return success message with the decoded token
        return {"message": "Token is valid", "username": decoded_token}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )