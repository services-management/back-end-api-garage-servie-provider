# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordRequestForm
# from sqlalchemy.orm import Session
# from datetime import timedelta, datetime
# from src.config.settings import settings
# from src.config.database import get_db
# from src.controller import UserController # <-- new import
# from src.routers.auth import create_access_token
# from src.schemas.user_shema import Token
# from jose import JWTError, jwt

# router = APIRouter()
# user_controller = UserController()
# # ... keep create_access_token as-is ...

# @router.post("/login", response_model=Token)
# async def login_for_access_token(
#     form_data: OAuth2PasswordRequestForm = Depends(),
#     db: Session = Depends(get_db),
# ):
#     user = user_controller.authenticate(db, form_data.username, form_data.password)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user.username}, expires_delta=access_token_expires
#     )
#     return {"access_token": access_token, "token_type": "bearer"}