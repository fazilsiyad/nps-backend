import datetime
from sqlalchemy.orm import Session
from models import Ticket, SLATracking, EscalationLog, TicketClassification
from services.whatsapp_service import send_whatsapp_message

def check_sla_breaches(db: Session):
    """
    Background Task / Cron Job function to check for missed deadlines.
    We identify tickets that have surpassed their SLA deadline and have not been resolved.
    """
    now = datetime.datetime.utcnow()
    
    # Get all unresolved tickets with SLA
    breached_tickets = db.query(Ticket).join(SLATracking).filter(
        Ticket.status.in_(["OPEN", "IN_PROGRESS"]),
        SLATracking.deadline < now,
        SLATracking.escalation_status == "NO_BREACH"
    ).all()

    for ticket in breached_tickets:
        escalate_to_manager(ticket, db, reason=f"SLA deadline breached. Deadline was {ticket.sla.deadline}")

def check_risk_escalations(db: Session):
    """
    Immediate escalation for tickets classified as Risk.
    """
    risk_tickets = db.query(Ticket).join(TicketClassification).filter(
        Ticket.status == "OPEN",
        TicketClassification.risk == True
    ).all()
    
    # We shouldn't escalate them multiple times if they are already escalated.
    # In a broader implementation, we'd join on EscalationLog to ensure they haven't been picked up yet.
    # We will just mark status as ESCALATED once caught here.
    for ticket in risk_tickets:
         escalate_to_manager(ticket, db, reason="High Risk / Fraud Suspected", risk=True)

def escalate_to_manager(ticket: Ticket, db: Session, reason: str, risk: bool = False):
    """
    Handles the escalation logic: tracking logs, updating DB, and sending alerts.
    """
    manager_phone = "whatsapp:+14155238886" # Default manager Twilio Sandbox number
    esc_log = EscalationLog(
        ticket_id=ticket.id,
        escalated_to="Tier_2_Manager" if not risk else "Compliance_Risk_Queue",
        reason=reason
    )
    db.add(esc_log)
    
    ticket.status = "ESCALATED"
    if ticket.sla:
        ticket.sla.escalation_status = "ESCALATED"
        
    db.commit()

    # Notify via WhatsApp
    alert_msg = f"🚨 URGENT ESCALATION 🚨\nTicket ID: {ticket.id[:8]}\nReason: {reason}\nDepartment: {ticket.classification.department}\nPlease address immediately."
    send_whatsapp_message(manager_phone, alert_msg)
    
    # Notify user of delay/escalation
    user_msg = f"We apologize for the delay in resolving your ticket ({ticket.id[:8]}). It has been escalated to our senior management team and we will respond shortly."
    send_whatsapp_message(ticket.mobile_number, user_msg)
    
