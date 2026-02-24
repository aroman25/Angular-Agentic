import { Annotation, StateGraph, START, END } from "@langchain/langgraph";
import { ChatOpenAI } from "@langchain/openai";
import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { tools, TARGET_DIR } from "./tools";
import fs from "fs-extra";
import path from "path";
import dotenv from "dotenv";
import { execSync } from "child_process";

dotenv.config();

const TEMPLATE_DIR = path.resolve(__dirname, '../../automate-angular-template');
const BLUEPRINT_PATH = path.resolve(__dirname, '../../ai-angular-blueprint.txt');
const INSTRUCTIONS_PATH = path.resolve(__dirname, '../../instructions.md');
const ORCHESTRATOR_SKILL_ROOT = path.resolve(
  __dirname,
  '../skills/angular-orchestrator-v20-v21',
);
const ORCHESTRATOR_SKILL_COMPAT_PATH = path.join(
  ORCHESTRATOR_SKILL_ROOT,
  'references/version-compatibility.md',
);
const ORCHESTRATOR_SKILL_PLANNER_PATH = path.join(
  ORCHESTRATOR_SKILL_ROOT,
  'references/planner-workorders.md',
);
const ORCHESTRATOR_SKILL_DEVELOPER_PATH = path.join(
  ORCHESTRATOR_SKILL_ROOT,
  'references/developer-execution.md',
);
const ORCHESTRATOR_SKILL_VALIDATOR_PATH = path.join(
  ORCHESTRATOR_SKILL_ROOT,
  'references/validator-audit.md',
);
const ORCHESTRATOR_SKILL_PATTERN_CATALOG_PATH = path.join(
  ORCHESTRATOR_SKILL_ROOT,
  'references/template-pattern-catalog.md',
);
const TEMPLATE_PATTERN_CATALOG_INDEX_PATH = path.join(
  TEMPLATE_DIR,
  'docs/agent-patterns/README.md',
);
const USER_STORY_PATH = path.resolve(__dirname, '../user-story.md');
const LAST_WORK_ORDER_PATH = path.resolve(__dirname, '../last-work-order.md');
const LAST_VALIDATION_PATH = path.resolve(__dirname, '../last-validation-feedback.md');
const TEMPLATE_COPY_IGNORES = new Set(["node_modules", "dist", ".angular", ".git"]);

// Token Tracking
let totalTokens = 0;
let promptTokens = 0;
let completionTokens = 0;

function trackTokens(response: any) {
  if (response?.response_metadata?.tokenUsage) {
    const usage = response.response_metadata.tokenUsage;
    totalTokens += usage.totalTokens || 0;
    promptTokens += usage.promptTokens || 0;
    completionTokens += usage.completionTokens || 0;
  }
}

function readTextIfExists(filePath: string): string {
  try {
    if (!fs.existsSync(filePath)) {
      return "";
    }
    return fs.readFileSync(filePath, "utf-8");
  } catch {
    return "";
  }
}

function detectAngularMajorVersionFromPackageJson(packageJsonPath: string): number | null {
  try {
    if (!fs.existsSync(packageJsonPath)) {
      return null;
    }
    const packageJson = fs.readJsonSync(packageJsonPath) as {
      dependencies?: Record<string, string>;
      devDependencies?: Record<string, string>;
    };
    const versionString =
      packageJson.dependencies?.["@angular/core"] ??
      packageJson.devDependencies?.["@angular/core"] ??
      "";
    const majorMatch = String(versionString).match(/(\d{2})/);
    if (!majorMatch?.[1]) {
      return null;
    }
    return Number(majorMatch[1]);
  } catch {
    return null;
  }
}

function buildAngularVersionContext(templatePackageJsonPath: string): string {
  const major = detectAngularMajorVersionFromPackageJson(templatePackageJsonPath);

  if (major === 20 || major === 21) {
    const zonelessNote =
      major === 21
        ? "Prefer zoneless-compatible patterns; do not assume Zone.js-based behavior."
        : "Do not require zoneless unless the template explicitly configures it.";
    return [
      `Angular target detected from template package.json: v${major}.`,
      "Prompt rules must stay compatible with Angular v20 and v21 unless the user story requires a narrower target.",
      zonelessNote,
      "Standalone components are default in both v20 and v21; do not require 'standalone: true'.",
    ].join(" ");
  }

  return [
    "Angular target major version could not be detected from template package.json.",
    "Assume v20/v21 compatibility and avoid version-fragile instructions.",
  ].join(" ");
}

function buildOrchestratorSkillContext(): string {
  const sections: Array<{ title: string; content: string }> = [
    { title: "Version Compatibility", content: readTextIfExists(ORCHESTRATOR_SKILL_COMPAT_PATH) },
    { title: "Template Pattern Catalog", content: readTextIfExists(ORCHESTRATOR_SKILL_PATTERN_CATALOG_PATH) },
    { title: "Template Pattern Examples Index", content: readTextIfExists(TEMPLATE_PATTERN_CATALOG_INDEX_PATH) },
    { title: "Planner Work Orders", content: readTextIfExists(ORCHESTRATOR_SKILL_PLANNER_PATH) },
    { title: "Developer Execution", content: readTextIfExists(ORCHESTRATOR_SKILL_DEVELOPER_PATH) },
    { title: "Validator Audit", content: readTextIfExists(ORCHESTRATOR_SKILL_VALIDATOR_PATH) },
  ].filter((section) => section.content.trim().length > 0);

  if (sections.length === 0) {
    return "No orchestrator skill pack content found.";
  }

  return sections
    .map((section) => `## ${section.title}\n${section.content.trim()}`)
    .join("\n\n");
}

function cleanupGeneratedAppProcesses(): void {
  if (process.platform !== "win32") {
    return;
  }

  try {
    const targetForMatch = TARGET_DIR.replace(/\\/g, "\\\\");
    const script = [
      `$target = '${targetForMatch}'`,
      "$procs = Get-CimInstance Win32_Process | Where-Object {",
      "  $_.CommandLine -and",
      "  $_.ProcessId -ne $PID -and",
      "  $_.CommandLine -like \"*$target*\" -and",
      "  ($_.Name -match 'node|esbuild')",
      "}",
      "foreach ($p in $procs) {",
      "  try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop } catch {}",
      "}",
    ].join("; ");

    execSync(`powershell -NoProfile -Command "${script.replace(/"/g, '\\"')}"`, {
      stdio: "pipe",
      timeout: 10000,
    });
  } catch {
    // Best effort only.
  }
}

function resetGeneratedAppPreservingNodeModules(): void {
  if (!fs.existsSync(TARGET_DIR)) return;

  const topLevelEntries = fs.readdirSync(TARGET_DIR);
  for (const entry of topLevelEntries) {
    if (entry === "node_modules") continue;
    const fullPath = path.join(TARGET_DIR, entry);
    try {
      fs.removeSync(fullPath);
    } catch {
      // Best effort cleanup; template copy will overwrite known files.
    }
  }
}

function shouldCopyTemplatePath(sourcePath: string): boolean {
  const relative = path.relative(TEMPLATE_DIR, sourcePath);
  if (!relative || relative === "") return true;

  const parts = relative.split(path.sep);
  return !parts.some((part) => TEMPLATE_COPY_IGNORES.has(part));
}

// 1. Setup Project Clone
async function setupProject() {
  console.log("Cloning template to fresh generated-app directory...");
  cleanupGeneratedAppProcesses();
  if (fs.existsSync(TARGET_DIR)) {
    try {
      fs.removeSync(TARGET_DIR);
    } catch (error) {
      try {
        const stamp = new Date().toISOString().replace(/[:.]/g, "-");
        const fallbackPath = `${TARGET_DIR}-stale-${stamp}`;
        console.warn(`Could not remove generated-app cleanly. Archiving to: ${fallbackPath}`);
        fs.moveSync(TARGET_DIR, fallbackPath, { overwrite: true });
      } catch (archiveError) {
        console.warn("Archive fallback also failed (likely folder root lock). Falling back to emptyDir on generated-app.");
        try {
          fs.emptyDirSync(TARGET_DIR);
        } catch {
          console.warn("emptyDir fallback failed (likely locked node_modules). Resetting generated-app while preserving node_modules.");
          resetGeneratedAppPreservingNodeModules();
        }
      }
    }
  }
  fs.copySync(TEMPLATE_DIR, TARGET_DIR, { filter: shouldCopyTemplatePath });
  
  // Install dependencies in the new cloned app
  console.log("Installing dependencies in generated-app...");
  const { execSync } = await import("child_process");
  execSync("npm install", { cwd: TARGET_DIR, stdio: "inherit" });
  console.log("Template ready!");
}

type DeterministicCommandResult = {
  command: string;
  ok: boolean;
  output: string;
};

type DeterministicValidationResult = {
  ok: boolean;
  report: string;
};

function requiresReactiveFormValidation(userStory: string, workOrder: string): boolean {
  const combined = `${userStory}\n${workOrder}`.toLowerCase();
  const mentionsForm = /\bform(s)?\b/.test(combined);
  const mentionsValidation =
    /\bvalidat(e|ion|ions|ing)\b/.test(combined) || /\berror message(s)?\b/.test(combined);

  return mentionsForm && mentionsValidation;
}

function extractRequiredSharedUiSelectors(text: string): string[] {
  const matches = Array.from(text.matchAll(/`(app-[a-z0-9-]+)`/gi)).map((match) =>
    (match[1] || "").toLowerCase(),
  );
  const aliases = new Map<string, string>([
    ["app-menu", "app-dropdown-menu"],
  ]);
  return Array.from(
    new Set(matches.map((selector) => aliases.get(selector) ?? selector)),
  );
}

function extractExplicitRouteDataPoints(text: string): string[] {
  const matches = Array.from(
    text.matchAll(/(?:route should be|redirect(?:ed)? to|accessible at)\s+[`'"]?(\/[a-z0-9\-\/]+)[`'"]?/gi),
  ).map((match) => (match[1] || "").toLowerCase());

  return Array.from(new Set(matches));
}

function extractFormFieldDataPoints(userStory: string): string[] {
  const lines = userStory.split(/\r?\n/);
  const fields = new Set<string>();
  let inFormFieldsSection = false;

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (/^\d+\.\s+form fields\b/i.test(line)) {
      inFormFieldsSection = true;
      continue;
    }

    if (inFormFieldsSection && /^\d+\.\s+/.test(line)) {
      break;
    }

    if (!inFormFieldsSection || !line.startsWith("-")) {
      continue;
    }

    const withoutBullet = line.replace(/^-+\s*/, "");
    const payload = withoutBullet.includes(":")
      ? withoutBullet.split(":").slice(1).join(":")
      : withoutBullet;

    for (const part of payload.split(",")) {
      const normalized = part
        .trim()
        .replace(/^[`'"]|[`'"]$/g, "")
        .replace(/\s+/g, " ")
        .replace(/[.;]$/, "")
        .toLowerCase();
      if (normalized) {
        fields.add(normalized);
      }
    }
  }

  return Array.from(fields);
}

function hasMarkdownHeading(markdown: string, headingRegex: RegExp): boolean {
  return markdown
    .split(/\r?\n/)
    .some((line) => /^\s{0,3}#{1,6}\s+/.test(line) && headingRegex.test(line));
}

function workOrderHasTemplatePatternReferences(workOrder: string): boolean {
  return /(?:template\s+)?pattern references?\s*:/i.test(workOrder);
}

function userStoryLikelyNeedsTemplatePatternReferences(userStory: string): boolean {
  const normalized = userStory.toLowerCase();
  const selectorCount = Array.from(normalized.matchAll(/\bapp-[a-z0-9-]+\b/g)).length;
  const hasFormTerms =
    /\bform(s)?\b/.test(normalized) ||
    /\bfield(s)?\b/.test(normalized) ||
    /\bsubmit\b/.test(normalized) ||
    /\bvalidation\b/.test(normalized) ||
    /\bfilter(s|ing)?\b/.test(normalized);
  const hasLayoutTerms =
    /\blayout\b/.test(normalized) ||
    /\bpage\b/.test(normalized) ||
    /\bdashboard\b/.test(normalized) ||
    /\blist\b/.test(normalized) ||
    /\btable\b/.test(normalized) ||
    /\bgrid\b/.test(normalized) ||
    /\btabs?\b/.test(normalized) ||
    /\bdrawer\b/.test(normalized) ||
    /\bdialog\b/.test(normalized) ||
    /\bwizard\b/.test(normalized);

  return hasFormTerms || hasLayoutTerms || selectorCount >= 2;
}

function validateWorkOrderQuality(userStory: string, workOrder: string): string[] {
  const issues: string[] = [];
  const normalizedWorkOrder = workOrder.toLowerCase();

  const requiredSections: Array<{ regex: RegExp; label: string }> = [
    { regex: /feature name|goal/i, label: "Feature Name & Goal section" },
    { regex: /file structure/i, label: "File Structure section" },
    { regex: /state management/i, label: "State Management section" },
    { regex: /ui\/ux requirements|ui requirements|ux requirements/i, label: "UI/UX Requirements section" },
    { regex: /acceptance criteria/i, label: "Acceptance Criteria section" },
    { regex: /user story data points|data points extracted from user story|data points from user story/i, label: "User Story Data Points section" },
    { regex: /traceability|requirement mapping|user story.*work order/i, label: "Requirement Traceability section" },
  ];

  for (const section of requiredSections) {
    if (!hasMarkdownHeading(workOrder, section.regex)) {
      issues.push(`Missing required Work Order section: ${section.label}`);
    }
  }

  if (
    userStoryLikelyNeedsTemplatePatternReferences(userStory) &&
    !workOrderHasTemplatePatternReferences(workOrder)
  ) {
    issues.push(
      "Form/layout-heavy Work Order is missing a `Template Pattern References:` line in UI/UX Requirements.",
    );
  }

  const explicitRoutes = extractExplicitRouteDataPoints(userStory);
  for (const route of explicitRoutes) {
    if (!normalizedWorkOrder.includes(route)) {
      issues.push(`Work Order is missing explicit route data point from user story: ${route}`);
    }
  }

  const requiredSelectors = extractRequiredSharedUiSelectors(userStory);
  if (requiredSelectors.length > 0) {
    const missingSelectors = requiredSelectors.filter((selector) => !normalizedWorkOrder.includes(selector));
    if (missingSelectors.length > 0) {
      issues.push(
        `Work Order is missing shared UI selectors from user story (must map all required selectors): ${missingSelectors.slice(0, 10).join(", ")}${missingSelectors.length > 10 ? " ..." : ""}`,
      );
    }
  }

  if (requiresReactiveFormValidation(userStory, workOrder)) {
    const requiredFormPlanningSignals: Array<{ regex: RegExp; label: string }> = [
      { regex: /validation matrix|field-by-field validation/i, label: "field-by-field validation matrix" },
      { regex: /reactive form/i, label: "typed Reactive Form planning" },
      { regex: /valuechange|valuechange\)|non-cva|controlvalueaccessor/i, label: "non-CVA shared control binding strategy" },
    ];

    for (const requirement of requiredFormPlanningSignals) {
      if (!requirement.regex.test(workOrder)) {
        issues.push(`Form-centric Work Order is missing: ${requirement.label}`);
      }
    }

    const fieldLabels = extractFormFieldDataPoints(userStory);
    const missingFieldLabels = fieldLabels.filter((field) => !normalizedWorkOrder.includes(field));
    const maxAllowedMissing = Math.max(2, Math.floor(fieldLabels.length * 0.2));

    if (fieldLabels.length > 0 && missingFieldLabels.length > maxAllowedMissing) {
      issues.push(
        `Work Order does not preserve enough form field data points from the user story. Missing examples: ${missingFieldLabels.slice(0, 10).join(", ")}${missingFieldLabels.length > 10 ? " ..." : ""}`,
      );
    }
  }

  return issues;
}

function detectSharedUiProjectionProviderRisks(relativePath: string, content: string): string[] {
  if (!relativePath.startsWith("src/app/shared/ui/")) {
    return [];
  }

  const normalized = content.toLowerCase();
  const hasProjectedContent = normalized.includes("<ng-content");
  if (!hasProjectedContent) {
    return [];
  }

  const violations: string[] = [];

  // Angular Aria accordion group provides ACCORDION_GROUP. If the directive sits on an
  // internal wrapper instead of the component host, projected app-accordion-item children
  // may fail to inject the group token at runtime (NG0201).
  if (
    /accordion\/accordion\.component\.ts$/i.test(relativePath) &&
    /\bngaccordiongroup\b/i.test(content) &&
    !/\bhostDirectives\b/.test(content)
  ) {
    violations.push(
      `${relativePath}:1 - Template/Agent-level issue: projected shared UI wrapper uses ngAccordionGroup on an internal element without hostDirectives. This can cause runtime NG0201 (ACCORDION_GROUP) for projected accordion items. Attach AccordionGroup to the component host.`,
    );
  }

  return violations;
}

function getMaxWorkflowIterations(state: typeof AgentState.State): number {
  const requiredSelectors = extractRequiredSharedUiSelectors(state.userStory);
  const complexCoverageStory = requiredSelectors.length >= 15;
  const formValidationStory = requiresReactiveFormValidation(state.userStory, state.workOrder);

  if (complexCoverageStory && formValidationStory) return 8;
  if (complexCoverageStory) return 7;
  return 5;
}

function isKnownSharedUiPathFalsePositive(feedback: string): boolean {
  if (!/shared ui component files are missing/i.test(feedback)) {
    return false;
  }

  const bogusPathMatches = Array.from(
    feedback.matchAll(/src\/app\/shared\/ui\/app-([a-z0-9-]+)\/app-\1\.component\.ts/gi),
  );

  if (bogusPathMatches.length === 0) {
    return false;
  }

  const sharedUiBarrelPath = path.join(TARGET_DIR, "src", "app", "shared", "ui", "index.ts");
  if (!fs.existsSync(sharedUiBarrelPath)) {
    return false;
  }

  const barrelContent = fs.readFileSync(sharedUiBarrelPath, "utf-8");
  return bogusPathMatches.every((match) => {
    const slug = (match[1] || "").toLowerCase();
    return barrelContent.includes(`./${slug}/${slug}.component`);
  });
}

function normalizeValidatorFeedback(rawFinalMessage: string): { normalized: string; warning?: string } {
  const trimmedFinalMessage = rawFinalMessage.trim();
  const endsWithPass = /^([\s\S]*\n)?PASS$/.test(trimmedFinalMessage);
  const hasFailureLanguage = /\b(fail|failed|missing|violation|error)\b/i.test(trimmedFinalMessage);

  if (trimmedFinalMessage === "PASS" || (endsWithPass && !hasFailureLanguage)) {
    return { normalized: "PASS" };
  }

  if (isKnownSharedUiPathFalsePositive(trimmedFinalMessage)) {
    return {
      normalized: "PASS",
      warning:
        "Validation agent false-positive normalized: selector names (app-*) were incorrectly treated as shared/ui folder names.",
    };
  }

  return { normalized: rawFinalMessage };
}

function inferExpectedPrimaryRoute(userStory: string, workOrder: string): string | null {
  const combined = `${userStory}\n${workOrder}`;

  const explicitRouteMatch = combined.match(/(?:Feature route should be|route should be|accessible at)\s+[`'"]?(\/[a-z0-9\-\/]+)[`'"]?/i);
  if (explicitRouteMatch?.[1]) {
    return explicitRouteMatch[1];
  }

  const defaultRedirectMatch = combined.match(/redirect(?:ed)? to\s+[`'"]?(\/[a-z0-9\-\/]+)[`'"]?/i);
  if (defaultRedirectMatch?.[1]) {
    return defaultRedirectMatch[1];
  }

  return null;
}

function walkFiles(dirPath: string): string[] {
  if (!fs.existsSync(dirPath)) return [];
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });
  const files: string[] = [];

  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);
    if (entry.isDirectory()) {
      files.push(...walkFiles(fullPath));
    } else if (entry.isFile()) {
      files.push(fullPath);
    }
  }

  return files;
}

function collectLineViolations(
  relativePath: string,
  content: string,
  regex: RegExp,
  label: string,
): string[] {
  const lines = content.split(/\r?\n/);
  const violations: string[] = [];

  for (let index = 0; index < lines.length; index += 1) {
    if (regex.test(lines[index])) {
      violations.push(`${relativePath}:${index + 1} - ${label}`);
    }
    regex.lastIndex = 0;
  }

  return violations;
}

function runDeterministicCommand(command: string): DeterministicCommandResult {
  try {
    const output = execSync(command, {
      cwd: TARGET_DIR,
      encoding: "utf-8",
      stdio: "pipe",
      timeout: 180000,
    });
    return { command, ok: true, output };
  } catch (error: any) {
    const stdout = typeof error?.stdout === "string" ? error.stdout : "";
    const stderr = typeof error?.stderr === "string" ? error.stderr : "";
    return {
      command,
      ok: false,
      output: `STDOUT:\n${stdout}\nSTDERR:\n${stderr}`.trim(),
    };
  }
}

function runDeterministicValidationChecks(state: typeof AgentState.State): DeterministicValidationResult {
  const violations: string[] = [];
  const srcAppDir = path.join(TARGET_DIR, "src", "app");
  const files = walkFiles(srcAppDir).filter((file) => /\.(ts|html|css)$/.test(file));
  const expectedPrimaryRoute = inferExpectedPrimaryRoute(state.userStory, state.workOrder);
  const shouldEnforceReactiveFormValidation = requiresReactiveFormValidation(state.userStory, state.workOrder);
  const requiredSharedUiSelectors = extractRequiredSharedUiSelectors(state.userStory);
  const featureComponentTsContents: Array<{ relativePath: string; content: string }> = [];
  const featureHtmlContents: Array<{ relativePath: string; content: string }> = [];

  const bannedHtmlTemplatePatterns: Array<{ regex: RegExp; label: string }> = [
    { regex: /\*ngIf\b/, label: "Use @if instead of *ngIf" },
    { regex: /\*ngFor\b/, label: "Use @for instead of *ngFor" },
    { regex: /\*ngSwitch\b/, label: "Use @switch instead of *ngSwitch" },
    { regex: /\*ngSwitchCase\b/, label: "Use @switch/@case instead of *ngSwitchCase" },
    { regex: /\*ngSwitchDefault\b/, label: "Use @switch/@default instead of *ngSwitchDefault" },
    { regex: /\[\(ngModel\)\]/, label: "Do not use [(ngModel)]; use Reactive Forms" },
    { regex: /=>/, label: "Do not use arrow functions in Angular templates" },
  ];

  for (const filePath of files) {
    const relativePath = path.relative(TARGET_DIR, filePath).replace(/\\/g, "/");
    const content = fs.readFileSync(filePath, "utf-8");
    violations.push(...detectSharedUiProjectionProviderRisks(relativePath, content));

    if (relativePath.startsWith("src/app/features/") && filePath.endsWith(".component.ts")) {
      featureComponentTsContents.push({ relativePath, content });
    }
    if (relativePath.startsWith("src/app/features/") && filePath.endsWith(".html")) {
      featureHtmlContents.push({ relativePath, content });
    }

    if (filePath.endsWith(".html")) {
      for (const pattern of bannedHtmlTemplatePatterns) {
        violations.push(...collectLineViolations(relativePath, content, pattern.regex, pattern.label));
      }
    }

    if (filePath.endsWith(".ts")) {
      violations.push(
        ...collectLineViolations(relativePath, content, /@Input\b/, "Use input() instead of @Input"),
      );
      violations.push(
        ...collectLineViolations(relativePath, content, /@Output\b/, "Use output() instead of @Output"),
      );
      violations.push(
        ...collectLineViolations(relativePath, content, /\bany\b/, "Avoid any; use strict types or unknown"),
      );

      if (filePath.endsWith(".spec.ts")) {
        violations.push(
          ...collectLineViolations(relativePath, content, /\.toBeTrue\(\)/, "Vitest does not support toBeTrue(); use toBe(true) or toBeTruthy()"),
        );
        violations.push(
          ...collectLineViolations(relativePath, content, /\.toBeFalse\(\)/, "Vitest does not support toBeFalse(); use toBe(false) or toBeFalsy()"),
        );
      }
    }

    if (filePath.endsWith(".component.ts")) {
      if (!content.includes("ChangeDetectionStrategy.OnPush")) {
        violations.push(`${relativePath}:1 - Component missing ChangeDetectionStrategy.OnPush`);
      }
      if (!content.includes("changeDetection:")) {
        violations.push(`${relativePath}:1 - Component missing explicit changeDetection config`);
      }
    }

    if (/\.(html|ts)$/.test(filePath)) {
      const customControlTagRegex =
        /<app-(select|autocomplete|text-input|textarea|checkbox|switch|radio-group)\b[^>]*\bformControlName\s*=/g;
      if (customControlTagRegex.test(content)) {
        violations.push(
          `${relativePath}:1 - Shared UI controls in app-* do not support formControlName unless explicitly documented`,
        );
      }
    }

    if (filePath.endsWith(".component.css") && relativePath.startsWith("src/app/features/")) {
      const tailwindUtilityRedefinitions: Array<{ regex: RegExp; label: string }> = [
        { regex: /^\s*\.container\b/m, label: "Do not redefine Tailwind utility '.container' in feature CSS" },
        { regex: /^\s*\.grid\b/m, label: "Do not redefine Tailwind utility '.grid' in feature CSS" },
        { regex: /^\s*\.grid-cols-\d+\b/m, label: "Do not redefine Tailwind grid-cols-* utilities in feature CSS" },
        { regex: /^\s*\.flex\b/m, label: "Do not redefine Tailwind utility '.flex' in feature CSS" },
      ];

      for (const pattern of tailwindUtilityRedefinitions) {
        if (pattern.regex.test(content)) {
          violations.push(`${relativePath}:1 - ${pattern.label}`);
        }
      }
    }
  }

  const appHtmlPath = path.join(srcAppDir, "app.html");
  if (fs.existsSync(appHtmlPath)) {
    const appHtml = fs.readFileSync(appHtmlPath, "utf-8");
    if (!appHtml.includes("<router-outlet")) {
      violations.push("src/app/app.html:1 - app shell should include <router-outlet />");
    }
  }

  const appRoutesPath = path.join(srcAppDir, "app.routes.ts");
  if (fs.existsSync(appRoutesPath)) {
    const appRoutes = fs.readFileSync(appRoutesPath, "utf-8");
    if (expectedPrimaryRoute) {
      const routeWithoutSlash = expectedPrimaryRoute.replace(/^\//, "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

      if (!new RegExp(`path:\\s*''[\\s\\S]*redirectTo:\\s*['"]/?${routeWithoutSlash}['"]`).test(appRoutes)) {
        violations.push(`src/app/app.routes.ts:1 - default route must redirect to ${expectedPrimaryRoute}`);
      }
      if (!new RegExp(`path:\\s*['"]${routeWithoutSlash}['"]`).test(appRoutes)) {
        violations.push(`src/app/app.routes.ts:1 - ${expectedPrimaryRoute} route is missing`);
      }
    } else {
      if (!/path:\s*''[\s\S]*redirectTo:\s*['"]\/?[a-z0-9\-\/]+['"]/i.test(appRoutes)) {
        violations.push("src/app/app.routes.ts:1 - default route should redirect to the generated feature route");
      }
    }
  }

  if (shouldEnforceReactiveFormValidation) {
    const hasReactiveFormsModuleImport = featureComponentTsContents.some(({ content }) =>
      /\bReactiveFormsModule\b/.test(content),
    );
    const hasFormModelUsage = featureComponentTsContents.some(({ content }) =>
      /\b(FormGroup|FormControl|FormBuilder|NonNullableFormBuilder)\b/.test(content),
    );
    const hasValidatorUsage = featureComponentTsContents.some(({ content }) =>
      /\bValidators\b|\bValidatorFn\b|\bAsyncValidatorFn\b/.test(content),
    );
    const formHtmlFiles = featureHtmlContents.filter(({ content }) => /<form\b/i.test(content));
    const hasValidationUiInForm = formHtmlFiles.some(({ content }) =>
      /\b(invalid|errors|touched|dirty|submitted|error)\b/.test(content),
    );
    const hasSubmitButton = formHtmlFiles.some(({ content }) => /type\s*=\s*"submit"/i.test(content));

    if (!hasReactiveFormsModuleImport) {
      violations.push(
        "src/app/features/*:1 - Form/validation story requires ReactiveFormsModule in at least one feature component imports array",
      );
    }
    if (!hasFormModelUsage) {
      violations.push(
        "src/app/features/*:1 - Form/validation story requires typed Reactive Forms model usage (FormGroup/FormControl/FormBuilder)",
      );
    }
    if (!hasValidatorUsage) {
      violations.push(
        "src/app/features/*:1 - Form/validation story requires validation rules (e.g., Validators.* or custom validator functions)",
      );
    }
    if (formHtmlFiles.length === 0) {
      violations.push(
        "src/app/features/*:1 - Form/validation story requires at least one <form> element in feature templates",
      );
    } else {
      if (!hasValidationUiInForm) {
        violations.push(
          "src/app/features/*:1 - Form/validation story requires visible validation/error UI in form templates (invalid/touched/errors/submitted states)",
        );
      }
      if (!hasSubmitButton) {
        violations.push(
          "src/app/features/*:1 - Form/validation story requires a submit button (type=\"submit\")",
        );
      }
    }
  }

  if (requiredSharedUiSelectors.length > 0) {
    const combinedFeatureHtml = featureHtmlContents.map(({ content }) => content).join("\n");
    const missingSelectors = requiredSharedUiSelectors.filter((selector) => {
      const selectorRegex = new RegExp(`<${selector}\\b`, "i");
      return !selectorRegex.test(combinedFeatureHtml);
    });

    for (const selector of missingSelectors) {
      violations.push(
        `src/app/features/*:1 - User story requires shared UI selector '${selector}' to be used at least once in feature templates`,
      );
    }
  }

  const deterministicCommands = [
    runDeterministicCommand("npm.cmd run build"),
    runDeterministicCommand("npm.cmd run test -- --watch=false"),
  ];

  for (const result of deterministicCommands) {
    if (!result.ok) {
      violations.push(
        `${result.command} failed.\n${result.output.slice(0, 6000)}${result.output.length > 6000 ? "\n...[truncated]" : ""}`,
      );
      continue;
    }

    if (/run build/i.test(result.command)) {
      const hasAngularWarning =
        /\bWARNING\b/i.test(result.output) && (/\bNG\d{4,}\b/.test(result.output) || /\[plugin angular-compiler\]/i.test(result.output));

      if (hasAngularWarning) {
        violations.push(
          `${result.command} produced Angular build warnings (warnings are disallowed).\n${result.output.slice(0, 6000)}${result.output.length > 6000 ? "\n...[truncated]" : ""}`,
        );
      }
    }
  }

  if (violations.length === 0) {
    return {
      ok: true,
      report: "Deterministic validator checks: PASS",
    };
  }

  const report = [
    "Deterministic validator checks FAILED.",
    "",
    "Violations:",
    ...violations.map((violation) => `- ${violation}`),
  ].join("\n");

  return { ok: false, report };
}

// 2. Define State
const AgentState = Annotation.Root({
  userStory: Annotation<string>(),
  blueprint: Annotation<string>(),
  instructions: Annotation<string>(),
  orchestratorSkills: Annotation<string>(),
  angularVersionContext: Annotation<string>(),
  workOrder: Annotation<string>(),
  validationFeedback: Annotation<string>(),
  iterations: Annotation<number>({ reducer: (x, y) => x + y, default: () => 0 }),
});

// 3. Initialize LLM
const llm = new ChatOpenAI({ 
  model: "gpt-4.1-nano", 
  temperature: 0,
  callbacks: [
    {
      handleLLMEnd(output) {
        const usage = output.llmOutput?.tokenUsage;
        if (usage) {
          totalTokens += usage.totalTokens || 0;
          promptTokens += usage.promptTokens || 0;
          completionTokens += usage.completionTokens || 0;
        }
      }
    }
  ]
});

// 4. Define Nodes
async function plannerNode(state: typeof AgentState.State) {
  console.log("\n--- PLANNING AGENT ---");
  const basePrompt = `You are the Planning Agent (The Architect).
Blueprint:
${state.blueprint}

Instructions:
${state.instructions}

Orchestrator Angular Skills (derived from Codex Angular skills):
${state.orchestratorSkills}

Angular Version Context:
${state.angularVersionContext}

User Story:
${state.userStory}

Create a detailed Work Order (Markdown) for the Development Agent following the Vertical Slicing Architecture.
Include File Structure, State Management, UI/UX Requirements, and Acceptance Criteria.
WORK ORDER STRUCTURE RULE (required headings):
- Feature Name & Goal
- User Story Data Points (extract exact routes, field lists/options, required selectors, validation rules, and acceptance-critical constraints from the user story)
- Requirement Traceability (map each user-story requirement/data point to implementation tasks + acceptance criteria)
- File Structure
- State Management
- Form Model & Validation (when applicable)
- UI/UX Requirements
- Acceptance Criteria
TEMPLATE PATTERN RULE: For form/layout-heavy features, the Work Order 'UI/UX Requirements' section MUST include a 'Template Pattern References:' line citing selected pattern IDs from the template docs catalog (for example 'layout-page-shell-header-toolbar', 'form-mixed-controls-create-edit').
TEMPLATE PATTERN RULE: If no catalog pattern fits, include 'Template Pattern References: none' and a 'Deviation Notes:' line explaining why.
DATA FIDELITY RULE: All concrete data points (routes, field names, options, limits, required selectors, validation requirements) must come from the user story unless explicitly marked as an assumption.
ASSUMPTION RULE: If you add any assumption, place it in a short "Assumptions" section and label each assumption clearly.
CRITICAL: Explicitly instruct the Developer to overwrite 'src/app/app.html' and 'src/app/app.routes.ts' so the new feature is the default view and the Angular boilerplate is removed.
CRITICAL UI RULE: You MUST utilize the pre-built UI components located in 'src/app/shared/ui/' whenever these patterns are needed. Do not instruct the developer to build these from scratch.
CRITICAL UI RULE: Before listing custom UI work, require the Developer to inspect 'src/app/shared/ui/index.ts' and the top usage comments in the selected shared UI component files.
CRITICAL IMPORT RULE: The template supports the TypeScript path alias 'src/*'. Prefer shared UI barrel imports from 'src/app/shared/ui' unless a relative import is clearer.
TEMPLATE-FIRST RULE: If a likely reusable issue is identified (template config, shared UI component behavior, boilerplate app shell issue, path alias/import problem), call it out as a Template/Agent-level issue in the Work Order/notes so it can be fixed upstream.
SCOPE RULE: Do NOT add new mandatory tools/process requirements (e.g., AXE, Playwright, Lighthouse, e2e suites) unless the user story explicitly requires them.
FORM RULE: If the user story is form-centric, you MUST include a typed Reactive Forms schema, a field-by-field validation matrix (required/min/max/pattern/custom), validation message behavior (when errors appear), submit/disable rules, and the exact shared-ui control binding strategy for non-CVA controls.
PATTERN SELECTION RULE: Use the template pattern catalog in 'automate-angular-template/docs/agent-patterns/' to choose one primary 'layout-*' pattern and 0-2 'form-*' patterns before proposing custom UI structure.
SHARED UI COVERAGE RULE: If the user story lists specific 'app-*' selectors, include a checklist in the Work Order mapping every listed selector to a concrete feature location/interaction.
SHARED UI COVERAGE IMPLEMENTATION TIP: If the selector list is long, explicitly plan a "Shared UI Coverage" section/panel in the feature so every required component is demonstrated meaningfully without cluttering the primary form path.
You MUST explicitly list the exact shared UI imports/selectors the Developer should use (e.g., app-card, app-button, app-tabs, app-select, app-text-input, app-checkbox, app-empty-state, app-icon).`;

  let workOrder = "";
  let qualityIssues: string[] = [];

  for (let attempt = 1; attempt <= 3; attempt += 1) {
    const retrySupplement =
      attempt === 1
        ? ""
        : `\n\nPLANNER SELF-CORRECTION (attempt ${attempt} of 3):
Previous Work Order quality issues that MUST be fixed:
${qualityIssues.map((issue) => `- ${issue}`).join("\n")}

Return a complete corrected Work Order (full markdown), not a diff.`;

    const response = await llm.invoke([new SystemMessage(`${basePrompt}${retrySupplement}`)]);
    workOrder = String(response.content ?? "");
    qualityIssues = validateWorkOrderQuality(state.userStory, workOrder);

    if (qualityIssues.length === 0) {
      break;
    }

    console.warn(
      `Planner Work Order quality check failed (attempt ${attempt}/3):\n- ${qualityIssues.join("\n- ")}`,
    );
  }

  if (qualityIssues.length > 0) {
    console.warn(
      `Planner Work Order quality check still has issues after retries. Proceeding with latest Work Order.\n- ${qualityIssues.join("\n- ")}`,
    );
  }

  fs.writeFileSync(LAST_WORK_ORDER_PATH, workOrder, "utf-8");
  console.log("Work Order Generated.");
  return { workOrder };
}

async function developerNode(state: typeof AgentState.State) {
  console.log(`\n--- DEVELOPMENT AGENT (Iteration ${state.iterations + 1}) ---`);
  const hasValidatorFeedback = Boolean(state.validationFeedback?.trim());
  const isDeterministicRetry = /^Deterministic validator checks FAILED\./.test(
    state.validationFeedback?.trim() ?? "",
  );
  const devRecursionLimit = isDeterministicRetry ? 320 : 220;
  const retryFocusInstructions = isDeterministicRetry
    ? `
RETRY MODE (deterministic fixes only):
- The Validator already identified exact violations. Fix ONLY the cited files/patterns first.
- Do not rewrite the feature from scratch.
- Prefer minimal edits in the file paths listed in Validator feedback.
- Re-run 'npm run build' after each focused change and stop once build passes.`
    : "";
  
  const devAgent = createReactAgent({
    llm,
    tools,
    messageModifier: new SystemMessage(`You are the Development Agent (The Engineer).
Your job is to execute the Work Order by writing code and ensuring the app compiles.
You MUST use the provided tools to write files and run 'npm run build'.
Do not stop until 'npm run build' succeeds with ZERO errors and ZERO warnings (e.g., fix NG8103 warnings by using @for).
Before coding, use read_file to inspect:
1) 'src/app/shared/ui/index.ts'
2) The shared UI component files you plan to use (read the top usage comments)
3) 'src/app/app.ts', 'src/app/app.html', 'src/app/app.routes.ts', and 'src/app/app.spec.ts'
4) If the Work Order cites pattern IDs, read 'automate-angular-template/docs/agent-patterns/README.md' and the cited pattern docs in 'forms-core.md' / 'layouts-core.md'

CRITICAL ROUTING RULE:
You MUST overwrite 'src/app/app.html' to remove the default Angular boilerplate and replace it with your own layout or just '<router-outlet />'.
You MUST update 'src/app/app.routes.ts' to set the default route (path: '') to redirect to your new feature, or load your feature directly. The main page of the feature MUST be the first page to appear.
You MUST update 'src/app/app.ts' to remove 'NgOptimizedImage' from the imports array if you are no longer using it in 'app.html'.
You MUST update 'src/app/app.spec.ts' to remove the test that checks for the 'h1' element, and ensure there are no duplicate 'imports' keys in 'TestBed.configureTestingModule'. Also, ensure 'App' is in 'imports' and NOT in 'declarations' since it is a standalone component.
NEVER use '[(ngModel)]' or Template-driven forms. ALWAYS use Reactive Forms ('FormControl', 'FormGroup', 'ReactiveFormsModule').
CRITICAL ANGULAR RULES (hard validation failures):
- Use 'ChangeDetectionStrategy.OnPush' on all new components.
- Use 'inject()' instead of constructor injection.
- Use 'input()', 'output()', and 'model()' instead of '@Input()' and '@Output()' decorators.
- Use Signals ('signal', 'computed') for feature state. Do not store core feature state as plain mutable class fields.
- Use native control flow (@if/@for/@switch). Do not use *ngIf/*ngFor.
CRITICAL UI RULE: You MUST use the pre-built UI components in 'src/app/shared/ui/' instead of building custom versions for covered patterns.
Prefer: <app-card>, <app-button>, <app-badge>, <app-tabs>, <app-select>, <app-text-input>, <app-textarea>, <app-checkbox>, <app-empty-state>, <app-icon>.
SHARED UI COVERAGE RULE: If the Work Order/user story lists required selectors, you MUST track them and ensure each one appears in the feature templates at least once.
SHARED UI COVERAGE IMPLEMENTATION TIP: For large selector lists, create a dedicated "UI coverage/demo" section using realistic mock content so all required components are present while keeping the main form usable.
TEMPLATE PATTERN IMPLEMENTATION RULE: If the Work Order includes 'Template Pattern References', follow the cited pattern skeletons and shared UI composition maps first. Only deviate if the Work Order includes a justified 'Deviation Notes' explanation.
TAILWIND RULE: Style feature UIs with Tailwind utility classes in templates. Do NOT recreate Tailwind utilities in feature component CSS (e.g., '.container', '.grid', '.grid-cols-*', '.flex').
TAILWIND RULE: Keep feature component CSS empty/minimal unless there is a justified non-utility styling need.
TEMPLATE EXPRESSION RULE: Do NOT use inline arrow functions in templates. Do NOT invent complex inline object/function literals for component APIs when the shape is non-trivial; define typed arrays/options/config in component TypeScript instead.
API SHAPE RULE: Do not guess shared UI inputs/outputs. Read the component usage comment and component code first, then match the documented API exactly.
CRITICAL IMPORT RULE: Import shared UI components from 'src/app/shared/ui' (barrel import supported by template tsconfig path alias 'src/*'), or use explicit relative imports if you choose not to use the alias.
Do NOT create duplicate files under 'src/app/shared/ui/' for components that already exist in the template.
NOTE: These custom UI components do NOT implement ControlValueAccessor. You CANNOT use 'formControlName' on them. You MUST bind to their model inputs (e.g., '[value]="form.controls.myControl.value" (valueChange)="updateControl($event)"').
FORM VALIDATION RULES (required when the feature includes forms):
- Build a typed Reactive Form ('FormGroup'/'FormControl', '{ nonNullable: true }' where appropriate) and import 'ReactiveFormsModule'.
- Define explicit validators ('Validators.required', 'Validators.email', 'Validators.minLength', custom validators, etc.) according to the Work Order.
- Show validation feedback in the template (error text/hint states) based on 'touched', 'dirty', or submitted state.
- Include inline error messages for multiple fields and a form-level validation summary/alert after submit attempt.
- Disable submit while the form is invalid/pending and surface a success/error result state after submit.
- For shared UI controls without CVA support, create explicit bridge methods between form controls and component 'value'/'valueChange' APIs.
RADIO GROUP RULE: If 'app-radio-group' is in the required selector list, use it in the actual inquiry form flow (not only in a detached coverage/demo section).
IMPORTANT: If the Validator reports issues, fix those exact issues first, rerun build/tests, and then stop.
If the Validator or build output suggests a reusable template/orchestration issue, explicitly state "Template/Agent-level issue" in your response with the file path and root cause.
RUNTIME DI RULE: If you encounter runtime Angular DI errors like 'NG0201 No provider found' from shared UI wrappers (especially Angular Aria wrappers under 'src/app/shared/ui/'), treat it as a likely Template/Agent-level issue. Inspect whether provider/group directives are attached to an internal wrapper instead of the shared component host when children are projected via '<ng-content>'.
TESTING RULE: This workspace uses Vitest. Do NOT use Jasmine-only matchers like toBeTrue()/toBeFalse(); use toBe(true/false) or toBeTruthy()/toBeFalsy().
ANGULAR TEMPLATE RULE: Do NOT use TypeScript 'as' casts inside Angular template expressions/event bindings. Normalize or narrow values in component TypeScript methods instead.
${retryFocusInstructions}

Blueprint:
${state.blueprint}

Instructions:
${state.instructions}

Orchestrator Angular Skills (derived from Codex Angular skills):
${state.orchestratorSkills}

Angular Version Context:
${state.angularVersionContext}`)
  });

  const prompt = `Here is your Work Order:\n${state.workOrder}\n\nFeedback from Validator (if any):\n${state.validationFeedback || "None. This is the first attempt."}\n\nPlease implement the feature, write the files, and run 'npm run build'.`;
  
  await devAgent.invoke(
    { messages: [new HumanMessage(prompt)] },
    { recursionLimit: devRecursionLimit }
  );
  console.log("Development Complete.");
  return { iterations: 1 };
}

async function validatorNode(state: typeof AgentState.State) {
  console.log("\n--- VALIDATION AGENT ---");

  const deterministic = runDeterministicValidationChecks(state);
  if (!deterministic.ok) {
    fs.writeFileSync(LAST_VALIDATION_PATH, deterministic.report, "utf-8");
    console.log(`Validator Feedback (Deterministic):\n${deterministic.report.slice(0, 6000)}${deterministic.report.length > 6000 ? "\n...[truncated]" : ""}`);
    console.log("Validation Complete.");
    return { validationFeedback: deterministic.report };
  }
  console.log(deterministic.report);
  
  const valAgent = createReactAgent({
    llm,
    tools,
    messageModifier: new SystemMessage(`You are the Validation Agent (The Tester).
Your job is to verify the Developer's output against the Work Order's Acceptance Criteria.
Deterministic prechecks (build/test + rule scans) already passed. You should still inspect the code for semantic correctness.
You MUST use the tools to run 'npm run test -- --watch=false' and read files to check for Zoneless compliance, Signals, and OnPush.
You MUST verify that the Developer reused the pre-built UI components in 'src/app/shared/ui/' where applicable (not only Accordion/Autocomplete/Menu/Select/Tabs, but also Button/Card/Badge/TextInput/Checkbox/etc. when relevant).
CRITICAL SHARED UI PATH RULE: Selectors like '<app-card>' map to component selectors, not necessarily folder names. In this template, '<app-card>' is implemented at 'src/app/shared/ui/card/card.component.ts' (not 'src/app/shared/ui/app-card/app-card.component.ts'). Verify reuse by checking actual imports (preferably from 'src/app/shared/ui') and selector usage, not guessed 'app-*' file paths.
You MUST verify that the Developer implemented ALL features requested in the Work Order (e.g., forms, buttons, lists).
FORM VALIDATION RULE: If the feature is form-centric, verify the code contains a typed Reactive Form model, validators, validation/error UI states, and proper submit handling. For shared UI controls, verify 'value'/'valueChange' bridging is used instead of unsupported 'formControlName'.
SHARED UI COVERAGE RULE: If the user story explicitly lists required 'app-*' selectors, verify each listed selector is present in the feature templates and used meaningfully (not just imported).
TEMPLATE PATTERN RULE: If the Work Order is form/layout-heavy, verify 'UI/UX Requirements' includes 'Template Pattern References' (or 'Template Pattern References: none' plus 'Deviation Notes').
TEMPLATE PATTERN RULE: Check that the implementation broadly reflects the cited pattern IDs, or that any deviation is documented and still satisfies acceptance criteria.
Only fail on requirements that are explicitly REQUIRED by the Work Order / user story.
Do NOT fail the app for "Nice to Have", "Optional", or "Consider adding" items.
Do NOT fail because "information is not provided" if you can read the relevant files with tools. Inspect the actual HTML/CSS/TS before claiming uncertainty.
Do NOT require automated AXE/Lighthouse/Playwright runs unless the user story explicitly requires those exact tools. Validate accessibility by code inspection when automation is not explicitly required.
Do NOT claim missing features unless you inspected the actual HTML/TS and can cite the file path and concrete missing element/logic.
Do NOT fail for zoneless configuration unless you find a concrete violation in code or missing required provider setup explicitly requested by the Work Order.
Do NOT fail solely because a cited template pattern was adapted, if the Work Order documents the deviation and the implementation remains correct.
Classify each failure in your report as either "Feature-level" or "Template/Agent-level". Mark issues as Template/Agent-level when they are reusable across generated apps (template defaults, tsconfig/path alias, shared UI component defects, boilerplate app shell issues, validator/prompt gaps).
RUNTIME DI CLASSIFICATION RULE: If you find an Angular runtime DI error (e.g., NG0201 No provider found) caused by a shared UI wrapper in 'src/app/shared/ui/' using content projection with Angular Aria/provider directives, classify it as "Template/Agent-level" and cite the shared UI wrapper file(s), not only the feature component that rendered it.
If it passes ALL checks with no caveats or uncertainties, output exactly "PASS" and nothing else.
If it fails ANY check, output a concise detailed feedback report with:
- Build/test failures first (exact command + error summary)
- Then architecture/style violations (file paths)
- Then missing features vs acceptance criteria
- Concrete fixes the Developer should make next.
If you are uncertain whether any acceptance criterion is implemented, treat that as a failure and do NOT output PASS.

Blueprint:
${state.blueprint}

Instructions:
${state.instructions}

Orchestrator Angular Skills (derived from Codex Angular skills):
${state.orchestratorSkills}

Angular Version Context:
${state.angularVersionContext}`)
  });

  const prompt = `Work Order:\n${state.workOrder}\n\nPlease validate the implementation. Run tests and check the code. If everything is perfect, respond with "PASS". Otherwise, provide a detailed feedback report.`;
  
  const response = await valAgent.invoke(
    { messages: [new HumanMessage(prompt)] },
    { recursionLimit: 150 }
  );
  const rawFinalMessage = response.messages[response.messages.length - 1].content as string;
  const { normalized: normalizedFinalMessage, warning: normalizationWarning } =
    normalizeValidatorFeedback(rawFinalMessage);

  if (normalizationWarning) {
    console.warn(normalizationWarning);
  }

  fs.writeFileSync(LAST_VALIDATION_PATH, normalizedFinalMessage, "utf-8");
  console.log(normalizedFinalMessage === "PASS" ? "Validator Result: PASS" : `Validator Feedback:\n${normalizedFinalMessage.slice(0, 4000)}${normalizedFinalMessage.length > 4000 ? "\n...[truncated]" : ""}`);
  console.log("Validation Complete.");
  return { validationFeedback: normalizedFinalMessage };
}

function shouldContinue(state: typeof AgentState.State) {
  if (state.validationFeedback.trim() === "PASS") {
    console.log("\nWorkflow Complete! App is ready.");
    return END;
  }
  const maxIterations = getMaxWorkflowIterations(state);
  if (state.iterations >= maxIterations) {
    console.log("\nMax iterations reached. Stopping.");
    return END;
  }
  console.log("\nValidation failed. Routing back to Developer...");
  return "developer";
}

// 5. Build Graph
const workflow = new StateGraph(AgentState)
  .addNode("planner", plannerNode)
  .addNode("developer", developerNode)
  .addNode("validator", validatorNode)
  .addEdge(START, "planner")
  .addEdge("planner", "developer")
  .addEdge("developer", "validator")
  .addConditionalEdges("validator", shouldContinue);

const app = workflow.compile();

// 6. Run
async function main() {
  await setupProject();
  
  const userStory = fs.readFileSync(USER_STORY_PATH, "utf-8");
  const blueprint = fs.readFileSync(BLUEPRINT_PATH, "utf-8");
  const instructions = fs.readFileSync(INSTRUCTIONS_PATH, "utf-8");
  const orchestratorSkills = buildOrchestratorSkillContext();
  const angularVersionContext = buildAngularVersionContext(path.join(TARGET_DIR, "package.json"));

  console.log("\nStarting Agentic Workflow...");
  await app.invoke({
    userStory,
    blueprint,
    instructions,
    orchestratorSkills,
    angularVersionContext,
    iterations: 0,
    validationFeedback: ""
  }, {
    recursionLimit: 50
  });

  console.log("\n--- TOKEN USAGE ---");
  console.log(`Prompt Tokens:     ${promptTokens}`);
  console.log(`Completion Tokens: ${completionTokens}`);
  console.log(`Total Tokens:      ${totalTokens}`);
}

main().catch(console.error);
