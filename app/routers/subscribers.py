from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.subscriber import Subscriber
from app.models.plan import Plan
from app.schemas.subscriber import SubscriberCreate, SubscriberUpdate, SubscriberResponse
from app.services.nomba import create_virtual_account
from app.services.billing import calculate_next_billing_date


router = APIRouter()


@router.get("/", response_model=List[SubscriberResponse])
def get_subscribers(status: str = None, db: Session = Depends(get_db)):
    query = db.query(Subscriber)
    if status:
        query = query.filter(Subscriber.status == status)
    return query.all()


@router.get("/{subscriber_id}", response_model=SubscriberResponse)
def get_subscriber(subscriber_id: int, db: Session = Depends(get_db)):
    subscriber = db.query(Subscriber).filter(Subscriber.id == subscriber_id).first()
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    return subscriber


@router.post("/", response_model=SubscriberResponse, status_code=201)
def create_subscriber(data: SubscriberCreate, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == data.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if not plan.is_active:
        raise HTTPException(status_code=400, detail="This plan is no longer active")

    nomba_result = create_virtual_account(
        account_name=data.name,
        email=data.email,
    )

    next_billing = calculate_next_billing_date(plan.billing_cycle)

    new_subscriber = Subscriber(
        name=data.name,
        email=data.email,
        phone=data.phone,
        plan_id=plan.id,
        status="active",
        amount=plan.price,
        next_billing_date=next_billing,
        nomba_virtual_account_id=nomba_result["account_id"],
        nomba_account_number=nomba_result["account_number"],
        nomba_bank_name=nomba_result["bank_name"],
    )

    db.add(new_subscriber)
    db.commit()
    db.refresh(new_subscriber)
    return new_subscriber


@router.put("/{subscriber_id}", response_model=SubscriberResponse)
def update_subscriber(subscriber_id: int, data: SubscriberUpdate, db: Session = Depends(get_db)):
    subscriber = db.query(Subscriber).filter(Subscriber.id == subscriber_id).first()
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    update_data = data.model_dump(exclude_unset=True)

    if "plan_id" in update_data:
        new_plan = db.query(Plan).filter(Plan.id == update_data["plan_id"]).first()
        if not new_plan:
            raise HTTPException(status_code=404, detail="New plan not found")
        update_data["amount"] = new_plan.price

    for field, value in update_data.items():
        setattr(subscriber, field, value)

    db.commit()
    db.refresh(subscriber)
    return subscriber


@router.post("/{subscriber_id}/cancel")
def cancel_subscriber(subscriber_id: int, db: Session = Depends(get_db)):
    subscriber = db.query(Subscriber).filter(Subscriber.id == subscriber_id).first()
    if not subscriber:
        raise HTTPException(status_code=404, detail="Subscriber not found")

    subscriber.status = "cancelled"
    db.commit()
    return {"message": f"Subscription for {subscriber.name} cancelled"}