import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();

const requiredFiles = [
  "app/layout.tsx",
  "app/page.tsx",
  "app/dashboard/page.tsx",
  "app/workers/page.tsx",
  "app/hiring/page.tsx",
  "app/visa/page.tsx",
  "app/documents/page.tsx",
  "app/contacts/page.tsx",
  "app/approvals/page.tsx",
  "app/evidence/page.tsx",
  "components/AppShell.tsx",
  "components/StatusBadge.tsx",
  "features/dashboard/mockData.ts",
  "lib/api.ts",
  "lib/constants.ts",
  "types/index.ts",
];

const missing = requiredFiles.filter((file) => !existsSync(join(root, file)));

if (missing.length > 0) {
  console.error(`Missing frontend files:\n${missing.join("\n")}`);
  process.exit(1);
}

const sensitivePatterns = [
  /\d{6}-\d{7}/,
  /M\d{7,}/,
  /010-\d{3,4}-\d{4}/,
];

for (const file of requiredFiles) {
  const body = readFileSync(join(root, file), "utf8");
  const leaked = sensitivePatterns.find((pattern) => pattern.test(body));

  if (leaked) {
    console.error(`Potential unmasked sensitive data in ${file}: ${leaked}`);
    process.exit(1);
  }
}

console.log("Frontend skeleton validation passed.");
