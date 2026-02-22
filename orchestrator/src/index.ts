import { Annotation, StateGraph, START, END } from "@langchain/langgraph";
import { ChatOpenAI } from "@langchain/openai";
import { HumanMessage, SystemMessage } from "@langchain/core/messages";
import { createReactAgent } from "@langchain/langgraph/prebuilt";
import { tools, TARGET_DIR } from "./tools";
import fs from "fs-extra";
import path from "path";
import dotenv from "dotenv";

dotenv.config();

const TEMPLATE_DIR = path.resolve(__dirname, '../../automate-angular-template');
const BLUEPRINT_PATH = path.resolve(__dirname, '../../ai-angular-blueprint.txt');
const INSTRUCTIONS_PATH = path.resolve(__dirname, '../../instructions.md');
const USER_STORY_PATH = path.resolve(__dirname, '../user-story.md');

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

// 1. Setup Project Clone
function setupProject() {
  console.log("Cloning template to fresh generated-app directory...");
  if (fs.existsSync(TARGET_DIR)) {
    fs.removeSync(TARGET_DIR);
  }
  fs.copySync(TEMPLATE_DIR, TARGET_DIR);
  
  // Install dependencies in the new cloned app
  console.log("Installing dependencies in generated-app...");
  import("child_process").then(({ execSync }) => {
    execSync("npm install", { cwd: TARGET_DIR, stdio: "inherit" });
  });
  console.log("Template ready!");
}

// 2. Define State
const AgentState = Annotation.Root({
  userStory: Annotation<string>(),
  blueprint: Annotation<string>(),
  instructions: Annotation<string>(),
  workOrder: Annotation<string>(),
  validationFeedback: Annotation<string>(),
  iterations: Annotation<number>({ reducer: (x, y) => x + y, default: () => 0 }),
});

// 3. Initialize LLM
const llm = new ChatOpenAI({ 
  model: "gpt-4o", 
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
  const prompt = `You are the Planning Agent (The Architect).
Blueprint:
${state.blueprint}

Instructions:
${state.instructions}

User Story:
${state.userStory}

Create a detailed Work Order (Markdown) for the Development Agent following the Vertical Slicing Architecture.
Include File Structure, State Management, UI/UX Requirements, and Acceptance Criteria.
CRITICAL: Explicitly instruct the Developer to overwrite 'src/app/app.html' and 'src/app/app.routes.ts' so the new feature is the default view and the Angular boilerplate is removed.`;

  const response = await llm.invoke([new SystemMessage(prompt)]);
  console.log("Work Order Generated.");
  return { workOrder: response.content as string };
}

async function developerNode(state: typeof AgentState.State) {
  console.log(`\n--- DEVELOPMENT AGENT (Iteration ${state.iterations + 1}) ---`);
  
  const devAgent = createReactAgent({
    llm,
    tools,
    messageModifier: new SystemMessage(`You are the Development Agent (The Engineer).
Your job is to execute the Work Order by writing code and ensuring the app compiles.
You MUST use the provided tools to write files and run 'npm run build'.
Do not stop until 'npm run build' succeeds.

CRITICAL ROUTING RULE:
You MUST overwrite 'src/app/app.html' to remove the default Angular boilerplate and replace it with your own layout or just '<router-outlet />'.
You MUST update 'src/app/app.routes.ts' to set the default route (path: '') to redirect to your new feature, or load your feature directly. The main page of the feature MUST be the first page to appear.

Blueprint:
${state.blueprint}

Instructions:
${state.instructions}`)
  });

  const prompt = `Here is your Work Order:\n${state.workOrder}\n\nFeedback from Validator (if any):\n${state.validationFeedback || "None. This is the first attempt."}\n\nPlease implement the feature, write the files, and run 'npm run build'.`;
  
  await devAgent.invoke({ messages: [new HumanMessage(prompt)] });
  console.log("Development Complete.");
  return { iterations: 1 };
}

async function validatorNode(state: typeof AgentState.State) {
  console.log("\n--- VALIDATION AGENT ---");
  
  const valAgent = createReactAgent({
    llm,
    tools,
    messageModifier: new SystemMessage(`You are the Validation Agent (The Tester).
Your job is to verify the Developer's output against the Work Order's Acceptance Criteria.
You MUST use the tools to run 'npm run test -- --watch=false' and read files to check for Zoneless compliance, Signals, and OnPush.
If it passes, output exactly "PASS". If it fails, output a detailed feedback report.`)
  });

  const prompt = `Work Order:\n${state.workOrder}\n\nPlease validate the implementation. Run tests and check the code. If everything is perfect, respond with "PASS". Otherwise, provide a detailed feedback report.`;
  
  const response = await valAgent.invoke({ messages: [new HumanMessage(prompt)] });
  const finalMessage = response.messages[response.messages.length - 1].content as string;
  
  console.log("Validation Complete.");
  return { validationFeedback: finalMessage };
}

function shouldContinue(state: typeof AgentState.State) {
  if (state.validationFeedback.includes("PASS")) {
    console.log("\nWorkflow Complete! App is ready.");
    return END;
  }
  if (state.iterations >= 3) {
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
  setupProject();
  
  const userStory = fs.readFileSync(USER_STORY_PATH, "utf-8");
  const blueprint = fs.readFileSync(BLUEPRINT_PATH, "utf-8");
  const instructions = fs.readFileSync(INSTRUCTIONS_PATH, "utf-8");

  console.log("\nStarting Agentic Workflow...");
  await app.invoke({
    userStory,
    blueprint,
    instructions,
    iterations: 0,
    validationFeedback: ""
  });

  console.log("\n--- TOKEN USAGE ---");
  console.log(`Prompt Tokens:     ${promptTokens}`);
  console.log(`Completion Tokens: ${completionTokens}`);
  console.log(`Total Tokens:      ${totalTokens}`);
}

main().catch(console.error);
