#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(fileURLToPath(new URL("../../..", import.meta.url)));
const commands = [
  ["runtime-config", "verify:runtime-config"],
  ["licflow3-inventory", "verify:licflow3:inventory"],
  ["licflow3-no-duplicates", "verify:licflow3:no-duplicates"],
  ["licflow3-cloud-contract", "verify:licflow3:cloud-contract"],
  ["licflow3-route-map", "verify:licflow3:route-map"],
  ["licflow3-no-secrets", "verify:licflow3:no-secrets"],
  ["licflow3-no-db-commit", "verify:licflow3:no-db-commit"],
  ["licflow3-no-db-copy", "verify:licflow3:no-db-copy"],
  ["customer-setup-plan-provisioning", "verify:customer-setup:plan-provisioning"],
  ["customer-setup-no-secrets", "verify:customer-setup:no-secrets"],
];
const pnpm = process.platform === "win32" ? "pnpm.cmd" : "pnpm";
const results = [];

function run(label, args) {
  const started = Date.now();
  const result = spawnSync(pnpm, ["--dir", "apps/terminal-de-venta-system", "run", args], {
    cwd: repoRoot,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
  const stdout = String(result.stdout || "");
  const stderr = String(result.stderr || "");
  const record = {
    label,
    command: `${pnpm} --dir apps/terminal-de-venta-system run ${args}`,
    exitCode: result.status ?? 1,
    durationMs: Date.now() - started,
    stdoutTail: stdout.slice(-2500),
    stderrTail: stderr.slice(-2500),
  };
  results.push(record);
  console.log(JSON.stringify(record));
  if (record.exitCode !== 0) return false;
  return true;
}

for (const [label, scriptName] of commands) {
  if (!run(label, scriptName)) {
    console.error(JSON.stringify({
      ok: false,
      verifier: "verify-cloud-center-local-runtime-gate-01",
      gate: "G5A",
      resultCode: "CLOUD_CENTER_LOCAL_RUNTIME_SUBGATE_FAILED",
      failedSubgate: label,
      results,
    }, null, 2));
    process.exit(1);
  }
}

const workerCheck = spawnSync(process.execPath, ["--check", "apps/terminal-de-venta-system/infra/cloudflare/licflow3-worker/src/worker.js"], {
  cwd: repoRoot,
  encoding: "utf8",
  stdio: ["ignore", "pipe", "pipe"],
});
const workerRecord = {
  label: "worker-syntax",
  command: "node --check apps/terminal-de-venta-system/infra/cloudflare/licflow3-worker/src/worker.js",
  exitCode: workerCheck.status ?? 1,
  stdoutTail: String(workerCheck.stdout || "").slice(-2500),
  stderrTail: String(workerCheck.stderr || "").slice(-2500),
};
results.push(workerRecord);
console.log(JSON.stringify(workerRecord));
if (workerRecord.exitCode !== 0) {
  console.error(JSON.stringify({
    ok: false,
    verifier: "verify-cloud-center-local-runtime-gate-01",
    gate: "G5A",
    resultCode: "CLOUD_CENTER_WORKER_SYNTAX_FAILED",
    results,
  }, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({
  ok: true,
  verifier: "verify-cloud-center-local-runtime-gate-01",
  generatedAt: new Date().toISOString(),
  gate: "G5A",
  resultCode: "PASS_CLOUD_CENTER_LOCAL_RUNTIME_CONTRACT",
  subgates: results,
}, null, 2));
