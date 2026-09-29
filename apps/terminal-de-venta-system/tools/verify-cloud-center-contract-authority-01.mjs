#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const toolsDir = path.dirname(fileURLToPath(import.meta.url));
const terminalRoot = path.resolve(toolsDir, "..");

function read(relativePath) {
  return fs.readFileSync(path.join(terminalRoot, relativePath), "utf8");
}
function readJson(relativePath) {
  return JSON.parse(read(relativePath));
}
function assert(condition, code, details = {}) {
  if (!condition) {
    const error = new Error(code);
    error.details = details;
    throw error;
  }
}
function pass(checks) {
  console.log(JSON.stringify({
    ok: true,
    verifier: "verify-cloud-center-contract-authority-01",
    generatedAt: new Date().toISOString(),
    gate: "G1",
    resultCode: "PASS_CLOUD_CENTER_CONTRACT_AUTHORITY_RECONCILED",
    checks
  }, null, 2));
}

function main() {
  const checks = [];
  const commercial = readJson("shared/licensing/plan-catalog.canonical.json");
  const commercialPlans = Array.isArray(commercial.plans) ? commercial.plans : [];
  const vendible = commercialPlans
    .filter((plan) => plan && plan.vendible === true)
    .map((plan) => String(plan.plan || "").trim())
    .filter(Boolean);

  const expectedCommercial = ["TABLET_SOLO", "TABLET_PRO", "TABLET_PC_MANAGED"];
  assert(JSON.stringify(vendible) === JSON.stringify(expectedCommercial),
    "COMMERCIAL_VENDIBLE_SET_DRIFT", { vendible, expectedCommercial });
  checks.push("commercial_vendible_set_is_canonical");

  assert(!vendible.includes("TABLET_PC_MOBILE_MANAGED"),
    "PROVISIONING_ONLY_PLAN_ENTERED_COMMERCIAL_CATALOG");
  checks.push("starter_plan_absent_from_commercial_catalog");

  const contract = read("shared/licensing/customer-setup-contract.ts");
  assert(contract.includes("export type CustomerSetupCommercialPlanId = \"TABLET_SOLO\" | \"TABLET_PRO\" | \"TABLET_PC_MANAGED\";"),
    "COMMERCIAL_PLAN_TYPE_NOT_EXPLICIT");
  assert(contract.includes("export type CustomerSetupProvisioningOnlyPlanId = typeof PRISMA_TRIPLE_DEVICE_STARTER_PLAN;"),
    "PROVISIONING_ONLY_PLAN_TYPE_NOT_EXPLICIT");
  assert(contract.includes("CustomerSetupPlanId = CustomerSetupCommercialPlanId | CustomerSetupProvisioningOnlyPlanId;"),
    "PLAN_DOMAIN_SPLIT_NOT_EXPLICIT");
  assert(contract.includes("commercialPlanId: CustomerSetupCommercialPlanId;"),
    "COMMERCIAL_PLAN_MAPPING_TYPE_MISSING");
  assert(contract.includes('planId: PRISMA_TRIPLE_DEVICE_STARTER_PLAN,\n    commercialPlanId: "TABLET_PC_MANAGED"'),
    "STARTER_COMMERCIAL_PLAN_MAPPING_DRIFT");
  assert(contract.includes("Canonical commercial license SKU persisted in licenses/tenants."),
    "COMMERCIAL_PLAN_PERSISTENCE_SEMANTICS_MISSING");
  assert(contract.includes("PLAN_BASED_PROVISIONING_CATALOG"),
    "PROVISIONING_CATALOG_MISSING");
  checks.push("shared_contract_semantic_split_explicit");

  const worker = read("infra/cloudflare/licflow3-worker/src/worker.js");
  assert(worker.includes("const DEFAULT_SETUP_PLAN = \"TABLET_PC_MOBILE_MANAGED\";"),
    "WORKER_DEFAULT_PROVISIONING_PLAN_DRIFT");
  for (const planId of ["TABLET_SOLO","TABLET_PRO","TABLET_PC_MANAGED","TABLET_PC_MOBILE_MANAGED"]) {
    assert(worker.includes(planId), "WORKER_PROVISIONING_PLAN_MISSING", { planId });
  }
  assert(worker.includes("provisioning package plan, not a vendible commercial SKU"),
    "WORKER_SEMANTIC_GUARDRAIL_MISSING");
  assert(worker.includes('commercialPlanId: "TABLET_PC_MOBILE_MANAGED"') === false,
    "INVALID_LITERAL_COMMERCIAL_PLAN_PROPERTY");
  assert(worker.includes('TABLET_PC_MOBILE_MANAGED: {') && worker.includes('commercialPlanId: "TABLET_PC_MANAGED"'),
    "WORKER_STARTER_COMMERCIAL_MAPPING_DRIFT");
  checks.push("worker_provisioning_catalog_semantics_explicit");

  for (const expectedMapping of [
    ["TABLET_SOLO", "TABLET_SOLO"],
    ["TABLET_PRO", "TABLET_PRO"],
    ["TABLET_PC_MANAGED", "TABLET_PC_MANAGED"],
    ["TABLET_PC_MOBILE_MANAGED", "TABLET_PC_MANAGED"]
  ]) {
    const [provisioningPlan, commercialPlan] = expectedMapping;
    const start = worker.indexOf(`${provisioningPlan}: {`);
    assert(start >= 0, "WORKER_PROVISIONING_PLAN_BLOCK_MISSING", { provisioningPlan });
    const end = worker.indexOf("\n  },", start);
    const block = worker.slice(start, end >= 0 ? end : start + 1200);
    assert(block.includes(`commercialPlanId: "${commercialPlan}"`), "WORKER_COMMERCIAL_PLAN_MAPPING_DRIFT", { provisioningPlan, commercialPlan });
  }
  checks.push("worker_commercial_plan_mapping_explicit");



  const store = read("Prisma Cloud Ctr/internal/py/command_center_store.py");
  assert(store.includes('if not isinstance(plan, dict) or not plan.get("vendible"):'),
    "CLOUD_CENTER_COMMERCIAL_SELECTOR_NOT_FILTERING_VENDIBLE");
  assert(store.includes("shared/licensing/plan-catalog.canonical.json"),
    "CLOUD_CENTER_COMMERCIAL_SELECTOR_SOURCE_DRIFT");
  assert(contract.includes("Canonical commercial license SKU persisted in licenses/tenants."),
    "SHARED_CONTRACT_COMMERCIAL_PERSISTENCE_SEMANTICS_MISSING");
  checks.push("shared_contract_declares_commercial_persistence_owner");
  checks.push("commercial_selector_derives_from_canonical_vendible_catalog");

  const docs = [
    ["docs/productization/PRISMA_CUSTOMER_SETUP_MULTI_DEVICE_CONTRACT.md", ["TABLET_PC_MOBILE_MANAGED"]],
    ["docs/productization/PRISMA_PLAN_BASED_CLIENT_ONBOARDING_MATRICES.md", ["TABLET_PC_MOBILE_MANAGED"]],
    ["docs/ops/PRISMA_SUPREME_OPERATIONS_MAP.md", ["TABLET_PC_MOBILE_MANAGED"]]
  ];
  for (const [relativePath, tokens] of docs) {
    const content = read(relativePath);
    for (const token of tokens) assert(content.includes(token), "PROVISIONING_DOC_MISSING_PLAN", { relativePath, token });
  }
  checks.push("provisioning_docs_reference_supported_plan");

  const migration = read("infra/cloudflare/licflow3-worker/migrations/0003_plan_based_provisioning.sql");
  assert(migration.includes("-- This table is NOT the commercial SKU/price authority"),
    "D1_PROVISIONING_TABLE_AUTHORITY_GUARDRAIL_MISSING");
  checks.push("d1_provisioning_registry_semantics_explicit");

  const semanticDoc = read("Prisma Cloud Ctr/PRISMA_CLOUD_CENTER_PLAN_AUTHORITY_SEMANTICS.md");
  for (const token of [
    "PROVISIONING_ONLY_PLAN",
    "commercialSku: TABLET_PC_MANAGED",
    "TABLET_PC_MOBILE_MANAGED",
    "plan-catalog.canonical.json",
    "Customer Setup"
  ]) assert(semanticDoc.includes(token), "SEMANTIC_CONTRACT_MISSING_TOKEN", { token });
  checks.push("semantic_contract_present");

  pass(checks);
}

try {
  main();
} catch (error) {
  console.error(JSON.stringify({
    ok: false,
    verifier: "verify-cloud-center-contract-authority-01",
    generatedAt: new Date().toISOString(),
    gate: "G1",
    resultCode: error.message || "CONTRACT_AUTHORITY_VERIFICATION_FAILED",
    details: error.details || {}
  }, null, 2));
  process.exit(1);
}
