-- Claim-slot integrity hardening for concurrent Customer Setup device claims.
-- Adds the exact prepared slot identity to each claim and a uniqueness guard so
-- two concurrent claims cannot successfully attach to the same slot.
ALTER TABLE customer_device_claims ADD COLUMN claim_slot_id TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS ux_customer_device_claims_setup_surface_slot
  ON customer_device_claims(setup_id, surface, claim_slot_id);

CREATE INDEX IF NOT EXISTS idx_customer_device_claims_claim_slot
  ON customer_device_claims(claim_slot_id);
