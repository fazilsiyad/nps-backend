from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

# =======================
# Request / Input Schemas
# =======================

class TicketCreate(BaseModel):
    user_id: str
    pran: str
    mobile_number: str
    description: str

# =======================
# Response / Output Schemas
# =======================


class AgentAction(BaseModel):
    label: str
    type: Literal["reply", "navigate", "overlay"]
    value: str
    variant: Optional[Literal["default", "outline", "destructive"]] = "default"
    model_config = ConfigDict(from_attributes=True)

class RichContent(BaseModel):
    type: str
    data: Dict[str, Any]
    model_config = ConfigDict(from_attributes=True)

class TicketExtractedData(BaseModel):
    priority: str
    keywords: List[str]
    model_config = ConfigDict(from_attributes=True)

class TicketClassificationResponse(BaseModel):
    answer: str = ""
    is_resolved: bool = Field(default=False, alias="isResolved")
    should_file: bool = Field(default=False, alias="shouldFile")
    extracted_data: Optional[TicketExtractedData] = Field(default=None, alias="extractedData")
    actions: Optional[List[AgentAction]] = None
    suggestions: Optional[List[str]] = None
    rich_content: Optional[RichContent] = Field(default=None, alias="richContent")
    overlay: Optional[RichContent] = None

    department: Optional[str] = "General"
    urgency: Optional[str] = "Low"
    auto_resolve: Optional[bool] = False
    risk: Optional[bool] = False
    sentiment_score: Optional[float] = 0.5
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class SLATrackingResponse(BaseModel):
    urgency_level: str
    deadline: datetime
    escalation_status: str
    model_config = ConfigDict(from_attributes=True)

class DepartmentQueueResponse(BaseModel):
    department_name: str
    assigned_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WhatsAppLogResponse(BaseModel):
    recipient_number: str
    message: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class EscalationLogResponse(BaseModel):
    escalated_to: str
    reason: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TicketResponse(BaseModel):
    id: str
    user_id: str
    pran: str
    mobile_number: str
    description: str
    status: str
    created_at: datetime
    classification: Optional[TicketClassificationResponse] = None
    sla: Optional[SLATrackingResponse] = None
    queue: Optional[DepartmentQueueResponse] = None
    model_config = ConfigDict(from_attributes=True)

class TicketFullDetails(TicketResponse):
    escalation_logs: List[EscalationLogResponse] = []
    whatsapp_logs: List[WhatsAppLogResponse] = []
    model_config = ConfigDict(from_attributes=True)

# Dashboard Schemas
class AdminDashboardOverview(BaseModel):
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    ai_resolved_percentage: float
    sla_breached: int
    escalated_tickets: int

class DepartmentDashboardOverview(BaseModel):
    department: str
    pending_tickets: int
    overdue_tickets: int
    high_priority_tickets: int
    resolved_today: int
