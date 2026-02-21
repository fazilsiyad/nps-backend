from database import SessionLocal
from models import Ticket, TicketClassification, SLATracking, DepartmentQueue
import services.ai_engine as ai_engine
import services.whatsapp_service as whatsapp_service
import services.sla_engine as sla_engine
import schemas

def process_new_ticket_submission(ticket_data: schemas.TicketCreate, db) -> Ticket:
    """
    Core orchestrator flow for processing a newly submitted ticket.
    """
    # 1. Create Base Ticket
    new_ticket = Ticket(
        user_id=ticket_data.user_id,
        pran=ticket_data.pran,
        mobile_number=ticket_data.mobile_number,
        description=ticket_data.description
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    # 2. Call AI Engine for Classification
    classification_data = ai_engine.classify_ticket(ticket_data.description)
    
    # Calculate Risk Scoring / Fraud Detection Logic
    fraud_panic_words = ["stolen", "hack", "fraud", "unauthorized"]
    panic_boost = any(word in ticket_data.description.lower() for word in fraud_panic_words)
    
    # Sentiment-based Urgency Boosting
    sentiment = float(classification_data.get("sentiment_score", 0.5))
    urgency = classification_data.get("urgency", "Medium")
    if sentiment < 0.2 and urgency in ["Low", "Medium"]:
        urgency = "High" # Boost urgency if sentiment is extremely negative
    if panic_boost or classification_data.get("risk", False):
         urgency = "Risk"

    # Save Classification
    classification = TicketClassification(
        ticket_id=new_ticket.id,
        department=classification_data.get("department", "IT Support"),
        urgency=urgency,
        auto_resolve=classification_data.get("auto_resolve", False),
        risk=classification_data.get("risk", False) or panic_boost,
        sentiment_score=sentiment,
        # Agentic JSON fields
        answer=classification_data.get("answer", "Thank you, your ticket has been logged."),
        is_resolved=bool(classification_data.get("isResolved", False)),
        should_file=bool(classification_data.get("shouldFile", False)),
        extracted_data=classification_data.get("extractedData", None),
        actions=classification_data.get("actions", None),
        suggestions=classification_data.get("suggestions", None),
        rich_content=classification_data.get("richContent", None),
        overlay=classification_data.get("overlay", None)
    )
    db.add(classification)

    # 3. Handle Auto-Resolution Path
    if classification.auto_resolve and not classification.risk:
        new_ticket.status = "AI_RESOLVED"
        resolution_msg = ai_engine.generate_auto_resolve_message(ticket_data.description)
        whatsapp_service.send_whatsapp_message(
            new_ticket.mobile_number, 
            f"Hello from NPS Support!\nYour Issue: {ticket_data.description}\n\n🤖 Automated Solution:\n{resolution_msg}"
        )
        db.commit()
        db.refresh(new_ticket)
        # Ensure we return the dynamically generated AI data attached to the classification
        return new_ticket

    # 4. Routing & SLA Assignment Path (Complex Queries)
    deadline = sla_engine.calculate_sla_deadline(urgency)
    
    sla = SLATracking(
        ticket_id=new_ticket.id,
        urgency_level=urgency,
        deadline=deadline
    )
    db.add(sla)
    
    queue = DepartmentQueue(
        department_name=classification.department,
        ticket_id=new_ticket.id
    )
    db.add(queue)
    
    # Notify User it's being handled
    whatsapp_service.send_whatsapp_message(
        new_ticket.mobile_number, 
        f"Thank you for contacting NPS Support.\nYour ticket (ID: {new_ticket.id[:8]}) has been routed to the {classification.department} department. We will assist you shortly."
    )

    db.commit()
    db.refresh(new_ticket)
    return new_ticket

