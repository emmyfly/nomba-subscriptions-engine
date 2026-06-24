from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanUpdate, PlanResponse


router = APIRouter()


@router.get("/", response_model=List[PlanResponse])
def get_plans(db: Session = Depends(get_db)):
    plans = db.query(Plan).all()
    return plans


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/", response_model=PlanResponse, status_code=201)
def create_plan(plan_data: PlanCreate, db: Session = Depends(get_db)):
    valid_cycles = ["weekly", "monthly", "quarterly", "annual"]
    if plan_data.billing_cycle not in valid_cycles:
        raise HTTPException(
            status_code=400,
            detail=f"billing_cycle must be one of: {valid_cycles}"
        )

    new_plan = Plan(**plan_data.model_dump())
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return new_plan


@router.put("/{plan_id}", response_model=PlanResponse)
def update_plan(plan_id: int, plan_data: PlanUpdate, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    update_data = plan_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/{plan_id}")
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    db.delete(plan)
    db.commit()
    return {"message": f"Plan '{plan.name}' deleted successfully"}