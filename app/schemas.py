from pydantic import BaseModel
from typing import List
from datetime import date as date_o
from .models import WaterUnit, WaterCategory, EnergyUnit


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    username: str
    password: str
    confirm_password: str

class UserResponse(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str


    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    username: str

class VerifyAccessToken(BaseModel):
    message: str
    username: str

class WaterLogCreate(BaseModel):
    qty: float
    unit: WaterUnit
    category: WaterCategory
    date: date_o

class WaterLogResponse(BaseModel):
    id: int
    qty: float
    qty_litres: float
    unit: WaterUnit
    category: WaterCategory
    date: date_o


class EnergyLogCreate(BaseModel):
    qty: float
    unit: EnergyUnit
    date: date_o

class EnergyLogResponse(BaseModel):
    id: int
    qty: float
    unit: EnergyUnit
    date: date_o


class EnergyLogList(BaseModel):
    result:List[EnergyLogResponse]

class WaterLogList(BaseModel):
    result:List[WaterLogResponse]
    class Config:
        orm_mode = True

class GenSummaryResponse(BaseModel):
    today:float
    this_week:float
    this_month:float
