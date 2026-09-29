#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = [
    ROOT / "infra" / "cloudflare" / "licflow3-worker" / "migrations" / "0001_licflow3_core.sql",
    ROOT / "infra" / "cloudflare" / "licflow3-worker" / "migrations" / "0002_customer_setup.sql",
    ROOT / "infra" / "cloudflare" / "licflow3-worker" / "migrations" / "0003_plan_based_provisioning.sql",
    ROOT / "infra" / "cloudflare" / "licflow3-worker" / "migrations" / "0004_customer_device_claim_integrity.sql",
    ROOT / "infra" / "cloudflare" / "licflow3-worker" / "migrations" / "0005_replacement_slot_reuse.sql",
]


def require(condition: bool, code: str, details=None) -> None:
    if not condition:
        raise AssertionError(json.dumps({"code": code, "details": details or {}}, sort_keys=True))


def schema(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def scalar(conn: sqlite3.Connection, sql: str, params=()):
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else None


def main() -> None:
    checks = []
    migration_sql = "\n".join(path.read_text(encoding="utf-8") for path in MIGRATIONS)

    with tempfile.TemporaryDirectory(prefix="prisma-cloud-center-g4-") as td:
        db_path = Path(td) / "graph.sqlite"
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys=ON")
        conn.executescript(migration_sql)

        # Migration contract.
        require("claim_slot_id" in schema(conn, "customer_device_claims"), "CLAIM_SLOT_COLUMN_MISSING")
        indexes = {row[1] for row in conn.execute("PRAGMA index_list(customer_device_claims)")}
        require("ux_customer_device_claims_setup_surface_slot_active" in indexes, "CLAIM_SLOT_UNIQUE_INDEX_MISSING")
        checks.append("schema_claim_slot_integrity")

        # Seed one fully connected valid Customer Setup graph.
        conn.execute(
            "INSERT INTO tenants(slug, display_name, status, plan) VALUES(?,?,?,?)",
            ("g4-tenant", "G4 Tenant", "active", "TABLET_PC_MANAGED"),
        )
        conn.execute(
            "INSERT INTO licenses(license_id, tenant_slug, status, plan, activation_status) VALUES(?,?,?,?,?)",
            ("g4-license", "g4-tenant", "active", "TABLET_PC_MANAGED", "active"),
        )
        conn.execute(
            "INSERT INTO license_plans(plan_id, plan_name, max_tablet_devices, max_pc_devices, max_mobile_devices, max_total_devices, allowed_surfaces_json, features_json, setup_mode, claim_mode, requires_manual_approval, expiration_policy, grace_policy, renewal_policy) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("TABLET_PC_MOBILE_MANAGED", "Tablet + PC + Mobile Managed", 1, 1, 1, 3, '["tablet","pc","mobile"]', "[]", "setup_link_code_qr", "auto_generated_claim_slots", 0, "setup_bundle_30_days", "offline_grace_policy", "renew_license_assignment"),
        )
        conn.execute(
            "INSERT INTO license_assignments(license_assignment_id, license_id, setup_bundle_id, customer_id, tenant_id, tenant_slug, business_id, plan_id, status) VALUES(?,?,?,?,?,?,?,?,?)",
            ("g4-assignment", "g4-license", "g4-bundle", "g4-customer", "g4-tenant-id", "g4-tenant", "g4-business", "TABLET_PC_MANAGED", "assigned"),
        )
        conn.execute(
            "INSERT INTO customer_setups(setup_id, setup_code, setup_url, qr_payload, customer_id, tenant_id, tenant_slug, business_id, business_name, package_code, plan_code, status, expires_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("g4-setup", "G4-SETUP", "https://test.invalid/G4-SETUP", "G4", "g4-customer", "g4-tenant-id", "g4-tenant", "g4-business", "G4 Business", "PRISMA_TRIPLE_DEVICE_STARTER", "TABLET_PC_MOBILE_MANAGED", "active", "2099-01-01T00:00:00Z"),
        )
        for surface in ("tablet", "pc", "mobile"):
            conn.execute(
                "INSERT INTO customer_setup_slots(setup_id, surface, label, allowed, claimed) VALUES(?,?,?,?,?)",
                ("g4-setup", surface, surface, 1, 0),
            )
        conn.execute(
            "INSERT INTO customer_setup_bundles(setup_bundle_id, setup_id, setup_code, setup_link, setup_qr_payload, customer_id, tenant_id, tenant_slug, business_id, business_name, license_id, license_assignment_id, plan_id, operator_action_count, manual_device_claim_required, audit_event_id, status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("g4-bundle", "g4-setup", "G4-SETUP", "https://test.invalid/G4-SETUP", "G4", "g4-customer", "g4-tenant-id", "g4-tenant", "g4-business", "G4 Business", "g4-license", "g4-assignment", "TABLET_PC_MOBILE_MANAGED", 1, 0, "g4-provision", "active"),
        )
        conn.execute(
            "INSERT INTO customer_device_claim_slots(slot_id, setup_bundle_id, setup_id, customer_id, license_id, plan_id, surface, slot_index, claim_code, expires_at, status, audit_event_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            ("g4-slot-tablet-1", "g4-bundle", "g4-setup", "g4-customer", "g4-license", "TABLET_PC_MOBILE_MANAGED", "tablet", 1, "G4-SETUP-TABLET-01", "2099-01-01T00:00:00Z", "AVAILABLE", "g4-provision"),
        )
        conn.execute(
            "INSERT INTO audit_events(event_id, tenant_slug, event_type, payload_json) VALUES(?,?,?,?)",
            ("g4-audit", "g4-tenant", "customer_setup.create", "{}"),
        )
        conn.execute(
            "INSERT INTO audit_events(event_id, tenant_slug, event_type, payload_json) VALUES(?,?,?,?)",
            ("g4-provision", "g4-tenant", "customer_setup.plan_based_provision", "{}"),
        )
        conn.commit()

        # Valid graph checks.
        orphan_claims = scalar(conn, "SELECT COUNT(*) FROM customer_device_claims WHERE claim_slot_id IS NULL")
        dangling_claims = scalar(
            conn,
            "SELECT COUNT(*) FROM customer_device_claims c "
            "LEFT JOIN customer_setups s ON s.setup_id=c.setup_id "
            "LEFT JOIN customer_device_claim_slots cs ON cs.slot_id=c.claim_slot_id "
            "LEFT JOIN licenses l ON l.license_id=cs.license_id "
            "LEFT JOIN license_plans p ON p.plan_id=cs.plan_id "
            "WHERE c.status='claimed' AND (s.setup_id IS NULL OR cs.slot_id IS NULL OR l.license_id IS NULL OR p.plan_id IS NULL)",
        )
        dangling_bundles = scalar(
            conn,
            "SELECT COUNT(*) FROM customer_setup_bundles b "
            "LEFT JOIN customer_setups s ON s.setup_id=b.setup_id "
            "LEFT JOIN licenses l ON l.license_id=b.license_id "
            "LEFT JOIN license_assignments a ON a.license_assignment_id=b.license_assignment_id "
            "WHERE s.setup_id IS NULL OR l.license_id IS NULL OR a.license_assignment_id IS NULL",
        )
        dangling_slots = scalar(
            conn,
            "SELECT COUNT(*) FROM customer_device_claim_slots cs "
            "LEFT JOIN customer_setup_bundles b ON b.setup_bundle_id=cs.setup_bundle_id "
            "LEFT JOIN licenses l ON l.license_id=cs.license_id "
            "LEFT JOIN license_plans p ON p.plan_id=cs.plan_id "
            "WHERE b.setup_bundle_id IS NULL OR l.license_id IS NULL OR p.plan_id IS NULL",
        )
        counter_mismatches = scalar(
            conn,
            "SELECT COUNT(*) FROM customer_setup_slots ss "
            "WHERE ss.claimed != (SELECT COUNT(*) FROM customer_device_claims c WHERE c.setup_id=ss.setup_id AND c.surface=ss.surface AND c.status='claimed') "
            "OR ss.claimed > ss.allowed OR ss.claimed < 0",
        )
        require(orphan_claims == 0, "VALID_GRAPH_ORPHAN_CLAIM", {"orphan_claims": orphan_claims})
        require(dangling_claims == 0, "VALID_GRAPH_DANGLING_CLAIM", {"dangling_claims": dangling_claims})
        require(dangling_bundles == 0, "VALID_GRAPH_DANGLING_BUNDLE", {"dangling_bundles": dangling_bundles})
        require(dangling_slots == 0, "VALID_GRAPH_DANGLING_SLOT", {"dangling_slots": dangling_slots})
        require(counter_mismatches == 0, "VALID_GRAPH_COUNTER_MISMATCH", {"counter_mismatches": counter_mismatches})

        tenant_ownership_violations = scalar(
            conn,
            "SELECT COUNT(*) FROM licenses l LEFT JOIN tenants t ON t.slug=l.tenant_slug "
            "WHERE t.slug IS NULL OR l.tenant_slug != t.slug",
        )
        tenant_ownership_violations += scalar(
            conn,
            "SELECT COUNT(*) FROM license_assignments a LEFT JOIN tenants t ON t.slug=a.tenant_slug "
            "WHERE t.slug IS NULL OR a.tenant_slug != t.slug",
        )
        tenant_ownership_violations += scalar(
            conn,
            "SELECT COUNT(*) FROM customer_setups s LEFT JOIN tenants t ON t.slug=s.tenant_slug "
            "WHERE t.slug IS NULL OR s.tenant_slug != t.slug",
        )
        tenant_ownership_violations += scalar(
            conn,
            "SELECT COUNT(*) FROM customer_setup_bundles b LEFT JOIN tenants t ON t.slug=b.tenant_slug "
            "WHERE t.slug IS NULL OR b.tenant_slug != t.slug",
        )
        audit_link_violations = scalar(
            conn,
            "SELECT COUNT(*) FROM customer_setup_bundles b "
            "LEFT JOIN audit_events e ON e.event_id=b.audit_event_id AND e.tenant_slug=b.tenant_slug "
            "WHERE b.audit_event_id IS NULL OR e.event_id IS NULL",
        )
        audit_link_violations += scalar(
            conn,
            "SELECT COUNT(*) FROM customer_device_claim_slots cs "
            "LEFT JOIN customer_setup_bundles b ON b.setup_bundle_id=cs.setup_bundle_id "
            "LEFT JOIN audit_events e ON e.event_id=cs.audit_event_id AND e.tenant_slug=b.tenant_slug "
            "WHERE cs.audit_event_id IS NULL OR e.event_id IS NULL",
        )
        replaced_active_violations = scalar(
            conn,
            "SELECT COUNT(*) FROM customer_device_claims c "
            "JOIN customer_device_claim_slots cs ON cs.slot_id=c.claim_slot_id "
            "WHERE c.status='replaced' AND cs.status='CLAIMED' AND cs.device_id=c.device_id",
        )
        require(tenant_ownership_violations == 0, "VALID_GRAPH_TENANT_OWNERSHIP", {"tenant_ownership_violations": tenant_ownership_violations})
        require(audit_link_violations == 0, "VALID_GRAPH_AUDIT_LINKAGE", {"audit_link_violations": audit_link_violations})
        require(replaced_active_violations == 0, "VALID_GRAPH_REPLACED_DEVICE_ACTIVE", {"replaced_active_violations": replaced_active_violations})
        checks.extend([
            "valid_graph_claims",
            "valid_graph_bundles",
            "valid_graph_slots",
            "valid_graph_counters",
            "valid_graph_tenant_ownership",
            "valid_graph_audit_linkage",
            "valid_graph_replaced_not_active",
        ])

        # Corruption drills: each invariant must detect a deliberately broken graph.
        conn.execute(
            "INSERT INTO customer_device_claims(claim_id, setup_id, setup_code, tenant_slug, surface, device_id, status, claim_slot_id) VALUES(?,?,?,?,?,?,?,?)",
            ("g4-bad-null-slot", "g4-setup", "G4-SETUP", "g4-tenant", "pc", "bad-device", "claimed", None),
        )
        require(
            scalar(conn, "SELECT COUNT(*) FROM customer_device_claims WHERE claim_slot_id IS NULL") == 1,
            "CORRUPTION_DRILL_NULL_CLAIM_SLOT_NOT_DETECTED",
        )
        conn.execute("DELETE FROM customer_device_claims WHERE claim_id='g4-bad-null-slot'")
        checks.append("corruption_drill_claim_without_slot")

        conn.execute(
            "INSERT INTO customer_setup_bundles(setup_bundle_id, setup_id, setup_code, setup_link, setup_qr_payload, customer_id, tenant_id, tenant_slug, business_id, business_name, license_id, license_assignment_id, plan_id, status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("g4-orphan-bundle", "missing-setup", "G4-BAD", "x", "x", "g4-customer", "g4-tenant-id", "g4-tenant", "g4-business", "G4", "missing-license", "missing-assignment", "TABLET_PC_MOBILE_MANAGED", "active"),
        )
        require(
            scalar(
                conn,
                "SELECT COUNT(*) FROM customer_setup_bundles b "
                "LEFT JOIN customer_setups s ON s.setup_id=b.setup_id "
                "LEFT JOIN licenses l ON l.license_id=b.license_id "
                "LEFT JOIN license_assignments a ON a.license_assignment_id=b.license_assignment_id "
                "WHERE s.setup_id IS NULL OR l.license_id IS NULL OR a.license_assignment_id IS NULL",
            ) == 1,
            "CORRUPTION_DRILL_ORPHAN_BUNDLE_NOT_DETECTED",
        )
        conn.execute("DELETE FROM customer_setup_bundles WHERE setup_bundle_id='g4-orphan-bundle'")
        checks.append("corruption_drill_orphan_bundle")

        conn.execute(
            "UPDATE customer_setup_slots SET claimed=1 WHERE setup_id='g4-setup' AND surface='tablet'"
        )
        require(
            scalar(
                conn,
                "SELECT COUNT(*) FROM customer_setup_slots ss "
                "WHERE ss.claimed != (SELECT COUNT(*) FROM customer_device_claims c WHERE c.setup_id=ss.setup_id AND c.surface=ss.surface AND c.status='claimed') "
                "OR ss.claimed > ss.allowed OR ss.claimed < 0",
            ) == 1,
            "CORRUPTION_DRILL_COUNTER_NOT_DETECTED",
        )
        conn.rollback()
        checks.append("corruption_drill_aggregate_counter")

        # Active claim-slot uniqueness must be enforced by the partial unique index.
        try:
            conn.execute(
                "INSERT INTO customer_device_claims(claim_id, setup_id, setup_code, tenant_slug, surface, device_id, status, claim_slot_id) VALUES(?,?,?,?,?,?,?,?)",
                ("g4-dup-active-slot", "g4-setup", "G4-SETUP", "g4-tenant", "tablet", "g4-dup-device", "claimed", "g4-slot-tablet-1"),
            )
        except sqlite3.IntegrityError:
            checks.append("corruption_drill_duplicate_active_claim_slot_blocked")
        else:
            raise AssertionError("CORRUPTION_DRILL_DUPLICATE_ACTIVE_SLOT_NOT_BLOCKED")

        # A replaced claim may not leave its physical slot active for the same device.
        conn.execute("INSERT INTO customer_device_claims(claim_id, setup_id, setup_code, tenant_slug, surface, device_id, status, claim_slot_id) VALUES(?,?,?,?,?,?,?,?)",
                     ("g4-replaced-device", "g4-setup", "G4-SETUP", "g4-tenant", "tablet", "g4-replaced-device", "replaced", "g4-slot-tablet-1"))
        conn.execute("UPDATE customer_device_claim_slots SET status='CLAIMED', device_id='g4-replaced-device' WHERE slot_id='g4-slot-tablet-1'")
        require(
            scalar(
                conn,
                "SELECT COUNT(*) FROM customer_device_claims c JOIN customer_device_claim_slots cs ON cs.slot_id=c.claim_slot_id "
                "WHERE c.status='replaced' AND cs.status='CLAIMED' AND cs.device_id=c.device_id",
            ) == 1,
            "CORRUPTION_DRILL_REPLACED_ACTIVE_NOT_DETECTED",
        )
        checks.append("corruption_drill_replaced_claim_left_active")

        conn.close()

    print(json.dumps({
        "ok": True,
        "verifier": "verify-cloud-center-d1-graph-integrity-01",
        "generatedAt": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "gate": "G4",
        "resultCode": "PASS_CLOUD_CENTER_D1_GRAPH_INTEGRITY_SOURCE_AND_LOCAL_FIXTURE",
        "checks": checks,
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({
            "ok": False,
            "verifier": "verify-cloud-center-d1-graph-integrity-01",
            "gate": "G4",
            "resultCode": str(exc),
        }, indent=2))
        raise
