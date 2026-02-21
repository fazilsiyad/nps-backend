import uuid
from sqlalchemy import Column, String, Text, Boolean, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base
import datetime

def generate_uuid():
    return str(uuid.uuid4())

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String(100), index=True)
    pran = Column(String(20), index=True)
    mobile_number = Column(String(15))
    description = Column(Text)
    status = Column(String(50), default="OPEN") # OPEN, IN_PROGRESS, RESOLVED, AI_RESOLVED, ESCALATED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    classification = relationship("TicketClassification", back_populates="ticket", uselist=False, cascade="all, delete-orphan")
    sla = relationship("SLATracking", back_populates="ticket", uselist=False, cascade="all, delete-orphan")
    escalation_logs = relationship("EscalationLog", back_populates="ticket", cascade="all, delete-orphan")
    whatsapp_logs = relationship("WhatsAppLog", back_populates="ticket")
    queue = relationship("DepartmentQueue", back_populates="ticket", uselist=False, cascade="all, delete-orphan")

class TicketClassification(Base):
    __tablename__ = "ticket_classification"

    id = Column(String, primary_key=True, default=generate_uuid)
    ticket_id = Column(String, ForeignKey("tickets.id", ondelete="CASCADE"))
    
    # Original Data
    department = Column(String(100), index=True, nullable=True)
    urgency = Column(String(50), index=True, nullable=True) # Low, Medium, High, Critical, Risk
    auto_resolve = Column(Boolean, default=False)
    risk = Column(Boolean, default=False)
    sentiment_score = Column(Numeric(3,2), nullable=True)
    
    # New Agentic UI Data
    answer = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False)
    should_file = Column(Boolean, default=False)
    extracted_data = Column(JSON, nullable=True)
    actions = Column(JSON, nullable=True)
    suggestions = Column(JSON, nullable=True)
    rich_content = Column(JSON, nullable=True)
    overlay = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    ticket = relationship("Ticket", back_populates="classification")

class SLATracking(Base):
    __tablename__ = "sla_tracking"

    id = Column(String, primary_key=True, default=generate_uuid)
    ticket_id = Column(String, ForeignKey("tickets.id", ondelete="CASCADE"))
    urgency_level = Column(String(50))
    deadline = Column(DateTime)
    escalation_status = Column(String(50), default="NO_BREACH") # NO_BREACH, BREACHED, ESCALATED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    ticket = relationship("Ticket", back_populates="sla")

class EscalationLog(Base):
    __tablename__ = "escalation_log"

    id = Column(String, primary_key=True, default=generate_uuid)
    ticket_id = Column(String, ForeignKey("tickets.id", ondelete="CASCADE"))
    escalated_to = Column(String(100))
    reason = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    ticket = relationship("Ticket", back_populates="escalation_logs")

class WhatsAppLog(Base):
    __tablename__ = "whatsapp_log"

    id = Column(String, primary_key=True, default=generate_uuid)
    ticket_id = Column(String, ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True)
    recipient_number = Column(String(15))
    message = Column(Text)
    status = Column(String(50), default="SENT")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    ticket = relationship("Ticket", back_populates="whatsapp_logs")

class DepartmentQueue(Base):
    __tablename__ = "department_queue"

    id = Column(String, primary_key=True, default=generate_uuid)
    department_name = Column(String(100), index=True)
    ticket_id = Column(String, ForeignKey("tickets.id", ondelete="CASCADE"), unique=True)
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    ticket = relationship("Ticket", back_populates="queue")
