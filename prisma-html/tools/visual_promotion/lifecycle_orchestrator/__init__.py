"""Thin lifecycle coordinator over existing PRISMA visual authorities."""

from .orchestrator import (
    LifecycleOrchestratorError,
    advance_transition,
    diagnose,
    inspect_lifecycle,
    load_receipt,
    rollback_registration,
    supersede_lifecycle,
)

__all__ = [
    "LifecycleOrchestratorError",
    "advance_transition",
    "diagnose",
    "inspect_lifecycle",
    "load_receipt",
    "rollback_registration",
    "supersede_lifecycle",
]
