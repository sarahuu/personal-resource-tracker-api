import calendar
import pandas as pd

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import extract, func, desc
from fastapi.responses import StreamingResponse
from io import BytesIO
from datetime import datetime, timedelta

from ..database import get_db
from ..models import EnergyLog, User
from ..schemas import EnergyLogCreate, EnergyLogList, EnergyLogResponse, GenSummaryResponse
from ..auth import get_current_user

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
        energy_logs = db.query(EnergyLog).filter(EnergyLog.user_id == user.id).order_by(desc(EnergyLog.date)).all()
        return {'result':energy_logs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving energy logs: {str(e)}")


@router.post("/", response_model=EnergyLogResponse)
def create_energy_log(
    energy_log: EnergyLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
            user_id=user.id,
            date=energy_log.date,
            qty=energy_log.qty,
            unit=energy_log.unit,
        )
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating energy log: {str(e)}")


@router.get("/logs-by-month", response_model=list)
def get_energy_logs_grouped_by_month(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) ,
):
    try:
        user = db.query(User).filter(User.username == current_user).first()
        current_year = datetime.now().year


        logs = (
            db.query(
                extract("month", EnergyLog.date).label("month"),
                func.sum(EnergyLog.qty).label("total_qty"),
                func.count(EnergyLog.id).label("log_count")
            )
            .filter(EnergyLog.user_id == user.id) 
            .filter(extract("year", EnergyLog.date) == current_year)
            .group_by(extract("month", EnergyLog.date))
            .order_by(extract("month", EnergyLog.date))
            .all()
        )

        grouped_logs = [{"name": calendar.month_name[i][:3], "qty": 0} for i in range(1, 13)]

        for log in logs:
            month_name = calendar.month_name[int(log.month)][:3]
            for entry in grouped_logs:
                if entry["name"] == month_name:
                    entry["qty"] = log.total_qty

        return grouped_logs

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving energy logs: {str(e)}")


@router.get("/logs-by-week", response_model=list)
def get_energy_logs_grouped_by_current_week(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        user = db.query(User).filter(User.username == current_user).first()

        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        logs = (
            db.query(
                extract("dow", EnergyLog.date).label("day_of_week"),
                func.sum(EnergyLog.qty).label("total_qty")
            )
            .filter(EnergyLog.user_id == user.id)
            .filter(EnergyLog.date >= start_of_week.date())
            .filter(EnergyLog.date <= end_of_week.date())
            .group_by(extract("dow", EnergyLog.date))
            .order_by(extract("dow", EnergyLog.date))
            .all()
        )

        grouped_logs = [{"name": day, "qty": 0} for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]]
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

@router.get("/summary", response_model=GenSummaryResponse)
def get_energy_logs_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        user = db.query(User).filter(User.username == current_user).first()

        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

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
                EnergyLog.date >= start_of_week.date(),
                EnergyLog.date <= today.date(),
            )
            .scalar() or 0
        )
        total_this_month = (
            db.query(func.sum(EnergyLog.qty))
            .filter(
                EnergyLog.user_id == user.id,
                EnergyLog.date >= start_of_month.date(),
                EnergyLog.date <= today.date(),
            )
            .scalar() or 0
        )

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


@router.get("/export-energy-logs-excel")
def export_energy_logs_excel(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        user = db.query(User).filter(User.username == current_user).first()
        # Fetch energy logs from the database
        logs = db.query(EnergyLog).filter(EnergyLog.user_id == user.id).all()

        if not logs:
            raise HTTPException(status_code=404, detail="No water logs found.")

        data = [{"Date": log.date, "Quantity": log.qty, "Unit":log.unit.value} for log in logs]
        df = pd.DataFrame(data)

        excel_file = BytesIO()
        df.to_excel(excel_file, index=False, engine="openpyxl")
        excel_file.seek(0) 

        return StreamingResponse(
            excel_file, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=energy_logs.xlsx"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting logs: {str(e)}")
