from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import EnergyLog, User
from ..schemas import EnergyLogCreate, EnergyLogList, EnergyLogResponse
from ..auth import get_current_user
from datetime import datetime, timedelta
from sqlalchemy import extract, func
import calendar

router = APIRouter()
@router.get("/", response_model=EnergyLogList)
def get_all_energy_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch all energy logs for the authenticated user.
    """
    try:
        user = db.query(User).filter(User.username == current_user).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
            )
        # Query all energy logs for the user
        energy_logs = db.query(EnergyLog).filter(EnergyLog.user_id == user.id).all()
        return {'result':energy_logs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving energy logs: {str(e)}")


@router.post("/", response_model=EnergyLogResponse)
def create_energy_log(
    energy_log: EnergyLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Fetch the current user
):

    try:
        # Create and save the log for the current user
        user = db.query(User).filter(User.username == current_user).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
            )
        
        db_log = EnergyLog(
            user_id=user.id,  # Associate the log with the current user
            date=energy_log.date,
            qty=energy_log.qty,
            unit=energy_log.unit,
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log
    except Exception as e:
        db.rollback()  # Rollback the transaction if any error occurs
        raise HTTPException(status_code=400, detail=f"Error creating energy log: {str(e)}")


@router.get("/logs-by-month", response_model=list)
def get_energy_logs_grouped_by_month(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) , # Fetch the current user
):
    try:
        user = db.query(User).filter(User.username == current_user).first()
        today = datetime.now()

        # Get the current year
        current_year = datetime.now().year


        logs = (
            db.query(
                extract("month", EnergyLog.date).label("month"),
                func.sum(EnergyLog.qty).label("total_qty"),
                func.count(EnergyLog.id).label("log_count")
            )
            .filter(EnergyLog.user_id == user.id)  # Filter by current user
            .filter(extract("year", EnergyLog.date) == current_year)  # Filter by current year
            .group_by(extract("month", EnergyLog.date))  # Group by month
            .order_by(extract("month", EnergyLog.date))  # Sort by month
            .all()
        )

        # Initialize all months with a default value of 0
        grouped_logs = [{"name": calendar.month_name[i][:3], "qty": 0} for i in range(1, 13)]

        # Update with actual values from the query
        for log in logs:
            month_name = calendar.month_name[int(log.month)][:3]
            # Find the index corresponding to the month and update the qty value
            for entry in grouped_logs:
                if entry["name"] == month_name:
                    entry["qty"] = log.total_qty

        return grouped_logs

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving energy logs: {str(e)}")


@router.get("/logs-by-week", response_model=list)
def get_energy_logs_grouped_by_current_week(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # Fetch the current user
):
    try:
        user = db.query(User).filter(User.username == current_user).first()

        # Calculate the start and end of the current week
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        end_of_week = start_of_week + timedelta(days=6)  # Sunday

            # Group by day of the week for the current week
        logs = (
            db.query(
                extract("dow", EnergyLog.date).label("day_of_week"),  # Day of the week (0=Sunday, 1=Monday, ...)
                func.sum(EnergyLog.qty).label("total_qty")
            )
            .filter(EnergyLog.user_id == user.id)  # Filter by user
            .filter(EnergyLog.date >= start_of_week)  # Start of the current week
            .filter(EnergyLog.date <= end_of_week)  # End of the current week
            .group_by(extract("dow", EnergyLog.date))  # Group by day of the week
            .order_by(extract("dow", EnergyLog.date))  # Sort by day of the week
            .all()
        )

        # Initialize all days of the week with a default value of 0
        grouped_logs = [{"name": day, "qty": 0} for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]]

        # Update the list with actual values from the query
        for log in logs:
            day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][int(log.day_of_week) - 1]  # Map day number to name
            for entry in grouped_logs:
                if entry["name"] == day_name:
                    entry["qty"] = log.total_qty

        return grouped_logs

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving water logs: {str(e)}")


@router.delete("/{log_id}", status_code=204)
def delete_energy_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        user = db.query(User).filter(User.username == current_user).first()
        # Retrieve the energy log to ensure it exists and belongs to the current user
        energy_log = db.query(EnergyLog).filter(EnergyLog.id == log_id, EnergyLog.user_id == user.id).first()
        if not energy_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Energy log not found or does not belong to the current user.",
            )
        
        db.delete(energy_log)
        db.commit()
        return {"message": "Energy log deleted successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"An error occurred while deleting the energy log: {str(e)}",
        )

@router.get("/summary", response_model=dict)
def get_energy_logs_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        user = db.query(User).filter(User.username == current_user).first()

        # Calculate date ranges
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        # Query totals
        total_today = (
            db.query(func.sum(EnergyLog.qty))
            .filter(
                EnergyLog.user_id == user.id,
                func.date(EnergyLog.date) == today.date(),
            )
            .scalar() or 0
        )
        total_this_week = (
            db.query(func.sum(EnergyLog.qty))
            .filter(
                EnergyLog.user_id == user.id,
                EnergyLog.date >= start_of_week,
                EnergyLog.date <= today,
            )
            .scalar() or 0
        )
        total_this_month = (
            db.query(func.sum(EnergyLog.qty))
            .filter(
                EnergyLog.user_id == user.id,
                EnergyLog.date >= start_of_month,
                EnergyLog.date <= today,
            )
            .scalar() or 0
        )

        # Build the response
        return {
            "today": total_today,
            "this_week": total_this_week,
            "this_month": total_this_month,
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error fetching energy log summary: {str(e)}",
        )
