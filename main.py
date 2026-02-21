from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict

from database import engine, Base, get_db
import models, schemas
import services.routing_engine as routing_engine
from services.escalation_engine import check_sla_breaches, check_risk_escalations
import services.ai_engine

# Initialize DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agentic AI NPS Support Orchestrator",
    description="Intelligent AI backend for managing and auto-resolving NPS support tickets.",
    version="1.0.0"
)

# === CORS Setup ===
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Dashboard Setup ===
# Using APScheduler to mock background Celery tasks
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()

@scheduler.scheduled_job('interval', minutes=5)
def scheduled_escalation_job():
    # Setup independent DB session for cron job
    from database import SessionLocal
    db = SessionLocal()
    try:
        check_sla_breaches(db)
        check_risk_escalations(db)
    finally:
        db.close()

scheduler.start()

# === API Endpoints ===

from fastapi.responses import RedirectResponse

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")

@app.post("/submit-ticket", response_model=schemas.TicketResponse)
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    """
    Receives a new ticket, classifies it via AI, orchestrates routing, 
    and handles auto-resolution if applicable.
    """
    try:
        processed_ticket = routing_engine.process_new_ticket_submission(ticket, db)
        return processed_ticket
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ticket creation failed: {str(e)}")

@app.get("/tickets/{ticket_id}", response_model=schemas.TicketFullDetails)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """
    Fetches the full details of a specific ticket, including SLAs, classification, and logs.
    """
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@app.get("/dashboard/summary", response_model=schemas.AdminDashboardOverview)
def get_admin_dashboard_summary(db: Session = Depends(get_db)):
    """
    Aggregation metrics for Admin Dashboard.
    """
    total = db.query(models.Ticket).count()
    open_tickets = db.query(models.Ticket).filter(models.Ticket.status.in_(["OPEN", "IN_PROGRESS"])).count()
    resolved = db.query(models.Ticket).filter(models.Ticket.status == "RESOLVED").count()
    ai_resolved = db.query(models.Ticket).filter(models.Ticket.status == "AI_RESOLVED").count()
    escalated = db.query(models.Ticket).filter(models.Ticket.status == "ESCALATED").count()
    
    # Calculate percentage
    total_resolved = resolved + ai_resolved
    percentage_ai = (ai_resolved / total_resolved * 100) if total_resolved > 0 else 0.0

    # We can join to SLA tracking
    breaches = db.query(models.SLATracking).filter(models.SLATracking.escalation_status == "ESCALATED").count()

    return {
        "total_tickets": total,
        "open_tickets": open_tickets,
        "resolved_tickets": total_resolved,
        "ai_resolved_percentage": round(percentage_ai, 2),
        "sla_breached": breaches,
        "escalated_tickets": escalated
    }

@app.get("/department/{department_name}/queue", response_model=List[schemas.DepartmentQueueResponse])
def get_department_queue(department_name: str, db: Session = Depends(get_db)):
    """
    Gets the list of tickets queued for a specific department.
    """
    queue = db.query(models.DepartmentQueue).join(models.Ticket).filter(
        models.DepartmentQueue.department_name.ilike(f"%{department_name}%"),
        models.Ticket.status.in_(["OPEN", "IN_PROGRESS", "ESCALATED"])
    ).all()
    return queue

# Mock Hackathon Endpoint
@app.post("/simulate-cron")
def simulate_cron_tasks(db: Session = Depends(get_db)):
    """
    Trigger escalation checking manually for demo purposes.
    """
    check_sla_breaches(db)
    check_risk_escalations(db)
    return {"status": "Escalation check complete"}
