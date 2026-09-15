"""Local-first QA validators for model, program, architecture, and exports."""

from .accessibility import accessibility_qa, qa_accessibility, validate_accessibility
from .architecture import architecture_qa, qa_architecture, validate_architecture
from .dwg import dwg_qa, validate_dwg
from .ifc import create_minimal_ifc, ifc_qa, validate_ifc
from .model import model_qa, qa_model, validate_model
from .models import (
    QaCheck,
    QaCheckStatus,
    QaIssue,
    QaReport,
    QaResult,
    Severity,
    aggregate_result,
    render_report_markdown,
)
from .pdf import pdf_qa, validate_pdf
from .program import load_program_config, reconcile_program, validate_program
from .warnings import (
    WarningBaseline,
    WarningBaselineEntry,
    WarningDelta,
    WarningObservation,
    compare_warning_delta,
    compare_warnings,
    load_warning_baseline,
)

__all__ = [
    "QaCheck",
    "QaCheckStatus",
    "QaIssue",
    "QaReport",
    "QaResult",
    "Severity",
    "WarningBaseline",
    "WarningBaselineEntry",
    "WarningDelta",
    "WarningObservation",
    "accessibility_qa",
    "aggregate_result",
    "architecture_qa",
    "compare_warning_delta",
    "compare_warnings",
    "create_minimal_ifc",
    "dwg_qa",
    "ifc_qa",
    "load_program_config",
    "load_warning_baseline",
    "model_qa",
    "pdf_qa",
    "qa_accessibility",
    "qa_architecture",
    "qa_model",
    "reconcile_program",
    "render_report_markdown",
    "validate_accessibility",
    "validate_architecture",
    "validate_dwg",
    "validate_ifc",
    "validate_model",
    "validate_pdf",
    "validate_program",
]
