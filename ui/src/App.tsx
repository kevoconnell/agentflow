import { useState, useEffect } from "react";
import {
  Workflow,
  StreamEvent,
  ResultMessage,
  ConversationMessage,
  ControlConfig,
} from "./types";
import WorkflowSidebar from "./components/WorkflowSidebar";
import InputPanel from "./components/InputPanel";
import OutputDisplay from "./components/OutputDisplay";
import ControlsPanel from "./components/ControlsPanel";

import AgentEditor from "./components/AgentEditor";
import { Alert, AlertDescription } from "./components/ui/alert";
import { ThemeToggle } from "./components/ThemeToggle";

function App() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [conversationHistory, setConversationHistory] = useState<
    ConversationMessage[]
  >([]);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [controlValues, setControlValues] = useState<Record<string, any>>({});

  const selectedWorkflowData = workflows.find(
    (w) => w.name === selectedWorkflow
  );
  const controls: ControlConfig[] = selectedWorkflowData?.controls || [];

  const agentsList = selectedWorkflowData?.agents || [];

  useEffect(() => {
    fetch("/api/workflows")
      .then((res) => res.json())
      .then((data) => {
        setWorkflows(data.workflows);
        // Auto-select first workflow if available
        if (data.workflows && data.workflows.length > 0) {
          setSelectedWorkflow(data.workflows[0].name);
        }
      })
      .catch((err) => console.error("Error loading agents:", err));
  }, []);

  // Reset conversation when workflow changes
  useEffect(() => {
    setConversationHistory([]);
    setEvents([]);
    setError(null);
    setControlValues({});
  }, [selectedWorkflow]);

  const handleControlChange = (name: string, value: any) => {
    setControlValues((prev) => ({ ...prev, [name]: value }));
  };

  const runWorkflowWithInput = async (userInput: string) => {
    if (!selectedWorkflow || !userInput.trim()) {
      return;
    }

    const userMessage = userInput.trim();

    setIsRunning(true);

    // Add user message to conversation history (optimistic update)
    const newHistory = [
      ...conversationHistory,
      { role: "user" as const, content: userMessage },
    ];
    setConversationHistory(newHistory);

    // Clear previous run's data
    setEvents([]);
    setError(null);

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/run`);

    let assistantResponse = "";
    let runResult: ResultMessage | null = null;

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          workflow: selectedWorkflow,
          messages: newHistory,
          controls: controlValues, // Send control values
        })
      );
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      console.log("Received event:", data);

      if (
        data.type === "agent_updated_stream_event" ||
        data.type === "run_item_stream_event" ||
        data.type === "raw_response_event"
      ) {
        setEvents((prev) => [...prev, data]);

        if (
          data.event_type === "run_item" &&
          data.item_type === "message_output_item" &&
          data.delta
        ) {
          assistantResponse += data.delta;
        }
      } else if (data.type === "result") {
        runResult = data;
      } else if (data.type === "done") {
        setIsRunning(false);

        let fullResponse = assistantResponse;

        if (
          runResult &&
          runResult.tool_calls &&
          runResult.tool_calls.length > 0
        ) {
          fullResponse += "\n\n---\n\n**Tools Used:**\n\n";
          runResult.tool_calls.forEach((tool, idx) => {
            fullResponse += `${idx + 1}. **${tool.name}**\n`;
            if (tool.input) {
              fullResponse += `   - Input: \`${tool.input.substring(0, 100)}${
                tool.input.length > 100 ? "..." : ""
              }\`\n`;
            }
          });
        }

        if (fullResponse) {
          setConversationHistory((prev) => [
            ...prev,
            {
              role: "assistant" as const,
              content: fullResponse,
              workflow: selectedWorkflow || undefined,
            },
          ]);
        }
      } else if (data.type === "error" || data.error) {
        setError(data.message || data.error);
        setIsRunning(false);
      }
    };

    ws.onerror = () => {
      setError("Connection error");
      setIsRunning(false);
    };
  };

  const runWorkflow = () => {
    if (!selectedWorkflow || !input.trim()) {
      alert("Please select an agent and enter input");
      return;
    }

    const userMessage = input.trim();
    setInput(""); // Clear input immediately
    runWorkflowWithInput(userMessage);
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="bg-card border-b border-border px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src="/logo.png" alt="AgentFlow Logo" className="h-8 w-8" />
          <h1 className="text-2xl font-bold">AgentFlow</h1>
        </div>
        <ThemeToggle />
      </header>

      <div className="flex flex-1 overflow-hidden">
        <WorkflowSidebar
          workflows={workflows}
          selectedWorkflow={selectedWorkflow}
          onSelect={setSelectedWorkflow}
        />

        <main className="flex-1 flex flex-col p-8 overflow-hidden">
          <InputPanel
            input={input}
            onInputChange={setInput}
            onRun={runWorkflow}
            isRunning={isRunning}
            disabled={!selectedWorkflow}
          />

          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertDescription>Error: {error}</AlertDescription>
            </Alert>
          )}

          <OutputDisplay
            conversationHistory={conversationHistory}
            events={events}
            workflowName={selectedWorkflow || ""}
          />
        </main>

        {selectedWorkflow && (
          <aside className="w-96 bg-card border-l border-border p-6 overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4">Configuration</h2>
            <div className="space-y-6">
              {/* Agent Configuration */}
              <div>
                <h3 className="text-sm font-semibold mb-3">
                  Agent Configuration
                </h3>
                <AgentEditor
                  agents={agentsList}
                  workflowName={selectedWorkflow || undefined}
                  onAgentUpdate={async (agentName, updates) => {
                    if (!selectedWorkflow) return;

                    try {
                      const response = await fetch(
                        `/api/workflow/${selectedWorkflow}/agent/${agentName}`,
                        {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify(updates),
                        }
                      );
                      const data = await response.json();
                      if (data.success) {
                        console.log("Agent updated successfully");
                      }
                    } catch (error) {
                      console.error("Error updating agent:", error);
                    }
                  }}
                />
              </div>

              {/* Workflow Controls */}
              {controls.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold mb-3">
                    Workflow Controls
                  </h3>
                  <div className="space-y-4">
                    {controls.map((control) => (
                      <ControlsPanel
                        key={control.name}
                        controls={[control]}
                        values={controlValues}
                        onChange={handleControlChange}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}

export default App;
