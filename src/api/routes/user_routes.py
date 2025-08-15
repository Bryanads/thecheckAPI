

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
import datetime
import os
from dotenv import load_dotenv
from src.db.queries import (
    get_user_by_email,
    create_user,
    get_user_by_id,
    update_user_last_login,
    update_user_profile
)

load_dotenv()
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'SUPER_SECRET_DEV_KEY_DONT_USE_IN_PROD')

router = APIRouter(prefix="/users", tags=["users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    surf_level: str | None = None
    goofy_regular_stance: str | None = None
    preferred_wave_direction: str | None = None
    bio: str | None = None
    profile_picture_url: str | None = None

class LoginRequest(BaseModel):
    email: str
    password: str

class UpdateProfileRequest(BaseModel):
    name: str | None = None
    surf_level: str | None = None
    goofy_regular_stance: str | None = None
    preferred_wave_direction: str | None = None
    bio: str | None = None
    profile_picture_url: str | None = None

@router.post("/register")
async def register_user(request: RegisterRequest):
    data = request.dict()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    surf_level = data.get('surf_level')
    goofy_regular_stance = data.get('goofy_regular_stance')
    preferred_wave_direction = data.get('preferred_wave_direction')
    bio = data.get('bio')
    profile_picture_url = data.get('profile_picture_url')

    if not all([name, email, password]):
        raise HTTPException(status_code=400, detail="Name, email, and password are required")

    existing_user = await get_user_by_email(email)
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    hashed_password = pwd_context.hash(password)

    try:
        user_id = await create_user(
            name, email, hashed_password, surf_level, goofy_regular_stance,
            preferred_wave_direction, bio, profile_picture_url
        )
        return {"message": "User registered successfully", "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {e}")

@router.post("/login")
async def login_user(request: LoginRequest):
    data = request.dict()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        raise HTTPException(status_code=400, detail="Email and password are required")

    user = await get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not pwd_context.verify(password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        await update_user_last_login(user['user_id'])
    except Exception as e:
        print(f"Warning: Could not update last login for user {user['user_id']}: {e}")

    token_payload = {
        'user_id': str(user['user_id']),
        'email': user['email'],
        'exp': (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)).timestamp()
    }
    token = jwt.encode(token_payload, SECRET_KEY, algorithm='HS256')

    return {"message": "Login successful", "token": token, "user_id": user['user_id']}

@router.get("/profile/{user_id}")
async def get_user_profile(user_id: str):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = {k: v for k, v in user.items() if k != 'password_hash'}
    return user_data

@router.put("/profile/{user_id}")
async def update_user_profile_endpoint(user_id: str, request: UpdateProfileRequest):
    update_fields = {k: v for k, v in request.dict().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        await update_user_profile(user_id, update_fields)
        updated_user = await get_user_by_id(user_id)
        user_data = {k: v for k, v in updated_user.items() if k != 'password_hash'}
        return {"message": "Profile updated successfully", "user": user_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {e}")