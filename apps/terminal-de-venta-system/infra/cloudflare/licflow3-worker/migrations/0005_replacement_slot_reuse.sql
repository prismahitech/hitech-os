-- Replacement-safe claim-slot uniqueness for existing Customer Setup databases.
-- Replaced claims retain claim_slot_id for audit/history, but only active claims
-- may reserve a physical claim slot.
DROP INDEX IF EXISTS ux_customer_device_claims_setup_surface_slot;

CREATE UNIQUE INDEX IF NOT EXISTS ux_customer_device_claims_setup_surface_slot_active
  ON customer_device_claims(setup_id, surface, claim_slot_id)
  WHERE status = 'claimed';
