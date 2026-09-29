-- Claim-slot integrity hardening for concurrent Customer Setup device claims.
-- Adds the exact prepared slot identity to each claim and a uniqueness guard so
-- two concurrent claims cannot successfully attach to the same slot.
ALTER TABLE customer_device_claims ADD COLUMN claim_slot_id TEXT;

-- Backfill legacy claims from the already-persisted slot/device relationship.
-- Rows that cannot be mapped remain null and must be surfaced by the integrity
-- verifier instead of being silently guessed.
UPDATE customer_device_claims
SET claim_slot_id = (
  SELECT slot_id
  FROM customer_device_claim_slots
  WHERE customer_device_claim_slots.setup_id = customer_device_claims.setup_id
    AND customer_device_claim_slots.surface = customer_device_claims.surface
    AND customer_device_claim_slots.device_id = customer_device_claims.device_id
  ORDER BY slot_index ASC
  LIMIT 1
)
WHERE claim_slot_id IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_customer_device_claims_setup_surface_slot
  ON customer_device_claims(setup_id, surface, claim_slot_id);

CREATE INDEX IF NOT EXISTS idx_customer_device_claims_claim_slot
  ON customer_device_claims(claim_slot_id);
