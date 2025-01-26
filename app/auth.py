from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, HTTPAuthorizationCredentials, HTTPBearer

from datetime import datetime, timedelta
from .config import settings
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends, Request
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid token or expired token.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")
        
    def _create_token(self,
            token_type: str,
            lifetime: timedelta,
            sub: str,
        ) -> str:
            payload = {}
            expire = datetime.utcnow() + lifetime
            payload["type"] = token_type
            payload["exp"] = expire  # 4
            payload["iat"] = datetime.utcnow()  # 5
            payload["sub"] = str(sub)  # 6

            return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)



    def create_access_token(self,sub: str) -> str:
        return self._create_token(
            token_type="access_token",
            lifetime=timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)), 
            sub=sub,
        )



    # Function to decode JWT token
    def decode_jwt_token(self,token: str):
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except:
            return {}
        
    def verify_jwt(self, jwtoken: str) -> bool:
        isTokenValid: bool = False

        try:
            payload = self.decode_jwt_token(jwtoken)
        except:
            payload = None
        if payload:
            isTokenValid = True
        return isTokenValid
        

def verify_access_token(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

jwt_bearer_scheme = JWTBearer()
# Dependency to get the current user from the token
def get_current_user(token: str = Depends(jwt_bearer_scheme)):
    username = verify_access_token(token)
    return username


# Hash a password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Verify a password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)




