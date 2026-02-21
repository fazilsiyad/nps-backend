from datetime import datetime, timedelta

def calculate_sla_deadline(urgency: str) -> datetime:
    """
    Returns the deadline datetime based on urgency SLA mapping.
    Low -> 72 hours
    Medium -> 48 hours
    High -> 24 hours
    Critical -> 4 hours
    Risk -> Immediate (0 hours)
    """
    now = datetime.utcnow()
    
    sla_map = {
        "Low": timedelta(hours=72),
        "Medium": timedelta(hours=48),
        "High": timedelta(hours=24),
        "Critical": timedelta(hours=4),
        "Risk": timedelta(minutes=15) # 15 minutes mapped to immediate
    }
    
    return now + sla_map.get(urgency, timedelta(hours=48))
