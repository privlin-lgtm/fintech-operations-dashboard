from enum import StrEnum


class KycStatus(StrEnum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class RiskTier(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CustomerStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class AccountType(StrEnum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CARD = "card"
    LOAN = "loan"


class AccountStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"
    FROZEN = "frozen"


class TransactionDirection(StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"


class TransactionChannel(StrEnum):
    ACH = "ach"
    CARD = "card"
    WIRE = "wire"
    INTERNAL = "internal"


class TransactionStatus(StrEnum):
    INITIATED = "initiated"
    PENDING = "pending"
    SETTLED = "settled"
    FAILED = "failed"
    REVERSED = "reversed"


class CaseType(StrEnum):
    DISPUTE = "dispute"
    FRAUD = "fraud"
    AML_REVIEW = "aml_review"


class CaseStatus(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    PENDING_EXTERNAL = "pending_external"
    ESCALATED = "escalated"
    CLOSED_RESOLVED = "closed_resolved"
    CLOSED_NO_ACTION = "closed_no_action"


class CasePriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(StrEnum):
    HIGH_RISK_TXN = "high_risk_txn"
    VELOCITY = "velocity"
    SANCTIONS_MATCH = "sanctions_match"
    LOGIN_ANOMALY = "login_anomaly"
    MANUAL_WATCHLIST = "manual_watchlist"


class AlertSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(StrEnum):
    NEW = "new"
    UNDER_REVIEW = "under_review"
    ESCALATED = "escalated"
    DISMISSED = "dismissed"


class ReportType(StrEnum):
    CASE_VOLUME = "case_volume"
    SLA_COMPLIANCE = "sla_compliance"
    ALERT_DISPOSITION = "alert_disposition"
    ANALYST_PRODUCTIVITY = "analyst_productivity"
    AUDIT_TRAIL = "audit_trail"


class ReportCadence(StrEnum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
