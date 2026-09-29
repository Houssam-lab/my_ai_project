"""
Unified Contracts & Data Models — Hard Currency Engine (HCE)
Définit les structures de données typées, protocoles et contrats d'échange
pour l'ensemble des modules d'audit, de conformité et d'arbitrage.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum


class CorridorType(str, Enum):
    FR_PDP = "FR_PDP"
    FR_VULN_SECTOR = "FR_VULN_SECTOR"
    BE_PEPPOL = "BE_PEPPOL"
    EU_CBAM = "EU_CBAM"
    SAUDI_ZATCA = "SAUDI_ZATCA"
    EU_EAA = "EU_EAA"
    GLOBAL_AI_LABS = "GLOBAL_AI_LABS"
    FR_DEV_AGENCY = "FR_DEV_AGENCY"
    HIGH_VAL_EXPORT = "HIGH_VAL_EXPORT"
    INTL_GRANTS = "INTL_GRANTS"


class AnomalySeverity(str, Enum):
    CRITICAL = "CRITIQUE"
    MAJOR = "MAJEUR"
    MEDIUM = "MOYEN"
    MINOR = "MINEUR"
    INFO = "INFO"


@dataclass(frozen=True)
class AnomalyRecord:
    line_number: int
    entity_identifier: str
    error_code: str
    message: str
    severity: AnomalySeverity = AnomalySeverity.MAJOR
    suggested_fix: str = ""

    def to_dict(self) -> dict[str, object]:
        d: dict[str, object] = dict(asdict(self))
        d["severity"] = self.severity.value
        return d


@dataclass
class AuditSummary:
    corridor: CorridorType
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicate_records: int = 0
    compliance_rate: float = 0.0
    execution_time_ms: float = 0.0
    anomalies: list[AnomalyRecord] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)

    def calculate_rate(self) -> float:
        if self.total_records > 0:
            self.compliance_rate = round((self.valid_records / self.total_records) * 100.0, 2)
        else:
            self.compliance_rate = 100.0
        self.invalid_records = self.total_records - self.valid_records
        return self.compliance_rate

    def to_dict(self) -> dict[str, object]:
        return {
            "corridor": self.corridor.value,
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "duplicate_records": self.duplicate_records,
            "compliance_rate": self.compliance_rate,
            "execution_time_ms": round(self.execution_time_ms, 2),
            "anomalies_count": len(self.anomalies),
            "anomalies": [a.to_dict() for a in self.anomalies],
            "metadata": self.metadata,
        }


def flag_duplicate(
    line_errors: list[str], seen: dict[str, int], line_no: int, keys: list[str]
) -> None:
    """Définition unique du doublon, commune à tous les corridors.

    Une ligne est un doublon si elle partage **l'identifiant d'entreprise** (SIREN, BCE)
    **ou** le couple (nom, code postal) avec une ligne antérieure. L'identifiant d'abord :
    « Boulangerie Martin » et « Boulangerie Martin SAS » ont le même SIREN mais pas le même
    nom normalisé. Chaque clé retient la première ligne qui l'a portée.
    """
    first = next((seen[key] for key in keys if key in seen), None)
    if first is not None:
        line_errors.append(f"DOUBLON_AVEC_LIGNE_{first}")
    for key in keys:
        seen.setdefault(key, line_no)


@dataclass(frozen=True)
class FinancialArbitrage:
    corridor: CorridorType
    entity_name: str
    baseline_cost_eur: float
    optimized_cost_eur: float
    net_savings_eur: float
    penalty_avoided_eur: float = 0.0
    unit_savings_eur: float = 0.0
    roi_multiple: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return dict(asdict(self))
