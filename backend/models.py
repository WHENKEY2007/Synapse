"""
Synapse Knowledge Base - Data Models & Pydantic Schemas
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# Anomaly and Finding Types
AnomalyType = Literal['Contradiction', 'Stale', 'Duplicate', 'Unsupported']
SeverityLevel = Literal['High', 'Medium', 'Low']
FindingStatus = Literal['pending', 'approved', 'rejected', 'quarantined']
ActionType = Literal['Approved', 'Rejected', 'Quarantined', 'Rolled back', 'Auto-healed']

class Source(BaseModel):
    id: str
    name: str
    type: str  # Notion, Confluence, Google Drive
    documents_count: int
    status: str = "connected"
    last_synced: str = "Just now"

class Document(BaseModel):
    id: str
    title: str
    source: str
    owner: str  # Engineering, Security, People, Compliance, Marketing
    path: str
    updated: str
    status: str = "healthy"  # healthy, pending, updated, quarantined
    text: str

class Finding(BaseModel):
    id: str
    title: str
    source: str
    path: str
    type: AnomalyType
    confidence: int = Field(ge=0, le=100)
    severity: SeverityLevel
    owner: str
    updated: str
    current: str
    proposed: str
    evidence: str
    evidence_text: str
    reason: str
    status: FindingStatus = "pending"
    quarantine: bool = False
    evidence_source: Optional[str] = None
    applied_text: Optional[str] = None

class HistoryEvent(BaseModel):
    id: str
    issue_id: str
    title: str
    action: ActionType
    before: str
    after: str
    note: str
    evidence: str
    actor: str = "Alex Sterling"
    time: str
    rollback_of: Optional[str] = None

class AuditRun(BaseModel):
    id: str
    timestamp: str
    scope: str
    documents_checked: int
    findings_count: int
    applied_count: int
    status: str = "Completed"

class PolicySettings(BaseModel):
    threshold: int = Field(default=95, ge=80, le=100)
    auto_heal: bool = False
    last_audit: str = "12 minutes ago"

class ReviewDecisionRequest(BaseModel):
    action: Literal['Approved', 'Rejected', 'Quarantined']
    correction: Optional[str] = None
    note: Optional[str] = None
    verified: bool = False
    actor: str = "Alex Sterling"

class EvaluationScenario(BaseModel):
    name: str
    group: str
    type: str
    confidence: int
    owner: str
    quarantine: bool = False
    status: str = "pending"
    expected: bool

class EvaluationResult(BaseModel):
    name: str
    group: str
    expected_route: str
    actual_route: str
    passed: bool

class OverviewResponse(BaseModel):
    health_score: float
    total_documents: int
    open_issues: int
    pending_count: int
    threshold: int
    auto_heal: bool
    last_audit: str
    categories: dict
    recent_activity: List[dict]
    sources: List[Source]
