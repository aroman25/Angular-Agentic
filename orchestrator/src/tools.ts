import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { execSync } from "child_process";
import fs from "fs-extra";
import path from "path";

export const TARGET_DIR = path.resolve(__dirname, '../../generated-app');

export const writeCodeTool = tool(
  async ({ filePath, content }) => {
    const fullPath = path.join(TARGET_DIR, filePath);
    fs.ensureDirSync(path.dirname(fullPath));
    fs.writeFileSync(fullPath, content, 'utf-8');
    return `Successfully wrote to ${filePath}`;
  },
  {
    name: "write_code",
    description: "Write code to a file in the generated Angular app.",
    schema: z.object({
      filePath: z.string().describe("Path relative to the generated app root (e.g., src/app/features/login/login.ts)"),
      content: z.string().describe("The code content to write"),
    }),
  }
);

export const readFileTool = tool(
  async ({ filePath }) => {
    const fullPath = path.join(TARGET_DIR, filePath);
    if (!fs.existsSync(fullPath)) {
      return `Error: File ${filePath} does not exist.`;
    }
    return fs.readFileSync(fullPath, 'utf-8');
  },
  {
    name: "read_file",
    description: "Read the contents of a file in the generated Angular app.",
    schema: z.object({
      filePath: z.string().describe("Path relative to the generated app root"),
    }),
  }
);

export const runCommandTool = tool(
  async ({ command }) => {
    try {
      // Run command synchronously and capture output
      const output = execSync(command, { cwd: TARGET_DIR, encoding: 'utf-8', stdio: 'pipe' });
      return `Command succeeded:\n${output}`;
    } catch (error: any) {
      return `Command failed:\nSTDOUT:\n${error.stdout}\nSTDERR:\n${error.stderr}`;
    }
  },
  {
    name: "run_command",
    description: "Run a shell command in the generated app directory (e.g., npm run build, npm run test -- --watch=false).",
    schema: z.object({
      command: z.string().describe("The shell command to run"),
    }),
  }
);

export const tools = [writeCodeTool, readFileTool, runCommandTool];
