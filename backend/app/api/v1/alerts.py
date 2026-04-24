from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from uuid import UUID
import uuid
from app.core.database import get_db
from app.core.security import get_project_id
from app.models.alerts import AlertRule, AlertFired
from app.schemas.alerts import AlertRuleCreate, AlertRuleResponse, AlertRuleUpdate, AlertFiredResponse

router = APIRouter()

@router.post("/alerts/rules", response_model=AlertRuleResponse, status_code=201)
async def create_alert_rule(
    rule: AlertRuleCreate,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    db_rule = AlertRule(
        id=uuid.uuid4(),
        project_id=UUID(project_id),
        name=rule.name,
        metric_type=rule.metric_type,
        condition=rule.condition,
        threshold=rule.threshold,
        window_minutes=rule.window_minutes,
        notification_channel=rule.notification_channel,
        cooldown_minutes=rule.cooldown_minutes,
    )
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    return db_rule

@router.get("/alerts/rules", response_model=list[AlertRuleResponse])
async def list_alert_rules(
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertRule).where(AlertRule.project_id == UUID(project_id))
    )
    return result.scalars().all()

@router.put("/alerts/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: str,
    update: AlertRuleUpdate,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertRule).where(
            and_(AlertRule.id == UUID(rule_id), AlertRule.project_id == UUID(project_id))
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)
    return rule

@router.delete("/alerts/rules/{rule_id}", status_code=204)
async def delete_alert_rule(
    rule_id: str,
    project_id: str = Depends(get_project_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertRule).where(
            and_(AlertRule.id == UUID(rule_id), AlertRule.project_id == UUID(project_id))
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    await db.delete(rule)
    await db.commit()

@router.get("/alerts/history", response_model=list[AlertFiredResponse])
async def get_alert_history(
    project_id: str = Depends(get_project_id),
    status: str = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(AlertFired).where(AlertFired.project_id == UUID(project_id))
    if status:
        query = query.where(AlertFired.status == status)
    query = query.order_by(desc(AlertFired.triggered_at)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
