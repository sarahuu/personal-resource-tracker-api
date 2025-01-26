from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import WaterLog, User, WaterUnit
from ..schemas import WaterLogCreate, WaterLogResponse, WaterLogList
from ..auth import get_current_user
from datetime import datetime, timedelta
from sqlalchemy import extract, func, desc
from typing import Optional
import calendar

router = APIRouter()

@router.get("/", response_model=WaterLogList)
def get_all_water_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch all water logs for the authenticated user.
    """
    try:
        user = db.query(User).filter(User.username == current_user).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
            )
        # Query all water logs for the user
        water_logs = db.query(WaterLog).filter(WaterLog.user_id == user.id).order_by(desc(WaterLog.date)).all()
        return {'result':water_logs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving water logs: {str(e)}")


@router.post("/", response_model=WaterLogResponse)
def create_water_log(
    water_log: WaterLogCreate,
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
        if water_log.unit==WaterUnit.BUCKET:
            qty_litres = water_log.qty*19
        elif water_log.unit==WaterUnit.CUP:
            qty_litres = water_log.qty*0.236
        else:
            qty_litres = water_log.qty
        
        db_log = WaterLog(
            user_id=user.id,  # Associate the log with the current user
            date=water_log.date,
            qty=water_log.qty,
            qty_litres=qty_litres,
            unit=water_log.unit,
            category=water_log.category
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log
    except Exception as e:
        db.rollback()  # Rollback the transaction if any error occurs
        raise HTTPException(status_code=400, detail=f"Error creating water log: {str(e)}")


@router.get("/logs-by-month", response_model=list)
def get_water_logs_grouped_by_month(
    pie: Optional[bool] = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) , # Fetch the current user
):
    try:
        result = []

        user = db.query(User).filter(User.username == current_user).first()
        today = datetime.now()

        # Get the current year
        current_year = datetime.now().year


        if pie:
            # Group by category for the current month
            current_month = today.month
            logs = (
                db.query(
                    WaterLog.category.label("category"),  # Group by category
                    func.sum(WaterLog.qty_litres).label("total_qty")
                )
                .filter(WaterLog.user_id == user.id)  # Filter by user
                .filter(extract("year", WaterLog.date) == current_year)  # Filter by year
                .filter(extract("month", WaterLog.date) == current_month)  # Filter by month
                .group_by(WaterLog.category)  # Group by category
                .all()
            )
            grouped_logs = {}
            for log in logs:
                result.append({'category':log.category, 'total_qty': log.total_qty})
            return result

        else:
            # Query to group logs by month and count totals
            logs = (
                db.query(
                    extract("month", WaterLog.date).label("month"),
                    func.sum(WaterLog.qty_litres).label("total_qty"),
                    func.count(WaterLog.id).label("log_count")
                )
                .filter(WaterLog.user_id == user.id)  # Filter by current user
                .filter(extract("year", WaterLog.date) == current_year)  # Filter by current year
                .group_by(extract("month", WaterLog.date))  # Group by month
                .order_by(extract("month", WaterLog.date))  # Sort by month
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
        raise HTTPException(status_code=400, detail=f"Error retrieving water logs: {str(e)}")


@router.get("/logs-by-week", response_model=list)
def get_water_logs_grouped_by_current_week(
    pie: Optional[bool] = False,  # Flag to toggle grouping by category
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # Fetch the current user
):
    try:
        result=[]
        user = db.query(User).filter(User.username == current_user).first()

        # Calculate the start and end of the current week
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        end_of_week = start_of_week + timedelta(days=6)  # Sunday

        if pie:
            # Group by category for the current week
            logs = (
                db.query(
                    WaterLog.category.label("category"),  # Group by category
                    func.sum(WaterLog.qty_litres).label("total_qty")
                )
                .filter(WaterLog.user_id == user.id)  # Filter by user
                .filter(WaterLog.date >= start_of_week)  # Start of the current week
                .filter(WaterLog.date <= end_of_week)  # End of the current week
                .group_by(WaterLog.category)  # Group by category
                .all()
            )

            grouped_logs = {}
            for log in logs:
                result.append({'category':log.category, 'total_qty': log.total_qty})
            return result
        else:
            # Group by day of the week for the current week
            logs = (
                db.query(
                    extract("dow", WaterLog.date).label("day_of_week"),  # Day of the week (0=Sunday, 1=Monday, ...)
                    func.sum(WaterLog.qty_litres).label("total_qty")
                )
                .filter(WaterLog.user_id == user.id)  # Filter by user
                .filter(WaterLog.date >= start_of_week)  # Start of the current week
                .filter(WaterLog.date <= end_of_week)  # End of the current week
                .group_by(extract("dow", WaterLog.date))  # Group by day of the week
                .order_by(extract("dow", WaterLog.date))  # Sort by day of the week
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
def delete_water_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        user = db.query(User).filter(User.username == current_user).first()

        # Retrieve the water log to ensure it exists and belongs to the current user
        water_log = db.query(WaterLog).filter(WaterLog.id == log_id, WaterLog.user_id == user.id).first()
        if not water_log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Water log not found or does not belong to the current user.",
            )
        
        db.delete(water_log)
        db.commit()
        return {"message": "Water log deleted successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"An error occurred while deleting the water log: {str(e)}",
        )
    

@router.get("/summary", response_model=dict)
def get_water_logs_summary(
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
            db.query(func.sum(WaterLog.qty_litres))
            .filter(
                WaterLog.user_id == user.id,
                func.date(WaterLog.date) == today.date(),
            )
            .scalar() or 0
        )
        total_this_week = (
            db.query(func.sum(WaterLog.qty_litres))
            .filter(
                WaterLog.user_id == user.id,
                WaterLog.date >= start_of_week,
                WaterLog.date <= today,
            )
            .scalar() or 0
        )
        total_this_month = (
            db.query(func.sum(WaterLog.qty_litres))
            .filter(
                WaterLog.user_id == user.id,
                WaterLog.date >= start_of_month,
                WaterLog.date <= today,
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
            detail=f"Error fetching water log summary: {str(e)}",
        )