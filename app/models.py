from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum
from .database import Base
import enum
from datetime import datetime
from sqlalchemy.orm import relationship

class WaterUnit(enum.Enum):
    LITRE = "litre"
    BUCKET = "bucket"
    CUP = "cup"

class WaterCategory(enum.Enum):
    BATHING = "bathing"
    DRINKING = "drinking"
    WASHING = "washing"
    COOKING = "cooking"
    OTHER = "other"

class EnergyUnit(enum.Enum):
    KWH = "kwh"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(Date, default=datetime.utcnow)
    water_logs = relationship("WaterLog", back_populates="user")
    energy_logs = relationship("EnergyLog", back_populates="user")


class WaterLog(Base):
    __tablename__ = "water_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    qty = Column(Float)
    qty_litres = Column(Float)
    unit = Column(Enum(WaterUnit), nullable=False)
    category = Column(Enum(WaterCategory), nullable=False)
    date = Column(Date)
    created_at = Column(Date, default=datetime.today())
    user = relationship("User", back_populates="water_logs")

class EnergyLog(Base):
    __tablename__ = "energy_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    qty = Column(Float)
    unit = Column(Enum(EnergyUnit), nullable=False)
    date = Column(Date)
    created_at = Column(Date, default=datetime.today())
    user = relationship("User", back_populates="energy_logs")
