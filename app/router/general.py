from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from ..database import get_db
from ..models import WaterLog, EnergyLog, User
from ..auth import get_current_user
from fastapi import HTTPException
from sqlalchemy import func

router = APIRouter()


@router.get("/summary", response_model=dict)
def get_usage_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Fetch user
        user = db.query(User).filter(User.username == current_user).first()

        # Query total water usage
        total_water_used = (
            db.query(func.sum(WaterLog.qty_litres))
            .filter(WaterLog.user_id == user.id)
            .scalar() or 0
        )

        # Query total energy usage
        total_energy_used = (
            db.query(func.sum(EnergyLog.qty))
            .filter(EnergyLog.user_id == user.id)
            .scalar() or 0
        )

        # Build the response
        return {
            "total_water_used": total_water_used,
            "total_energy_used": total_energy_used,
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error fetching usage summary: {str(e)}",
        )