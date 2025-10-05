export interface ControlConfig {
  name: string;
  type: "text" | "number" | "select" | "boolean";
  label: string;
  defaultValue?: string | number | boolean;
  options?: string[];
  description?: string;
}

export interface Workflow {
  name: string;
  file: string;
  agents: string[];
  controls?: ControlConfig[];
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
  workflow?: string;
}

export interface StreamEvent {
  type:
    | "agent_updated_stream_event"
    | "run_item_stream_event"
    | "raw_response_event";
  event_type: "agent_updated" | "run_item" | "raw_response";
  agent?: string;
  delta?: string;
  item_type?: string;
  tool_name?: string;
  tool_input?: string;
  tool_output?: string;
  new_agent_name?: string;
  name?: string;
}

export interface ToolCall {
  name: string;
  input: string;
  output: string | null;
}

export interface ResultMessage {
  type: "result";
  agent: string;
  last_agent: string | null;
  last_response_id: string | null;
  num_new_items: number;
  num_raw_responses: number;
  tool_calls: ToolCall[];
  input_guardrails?: number;
  output_guardrails?: number;
}

export interface ErrorMessage {
  type: "error";
  message: string;
}

export interface DoneMessage {
  type: "done";
}

export type WSMessage =
  | StreamEvent
  | ResultMessage
  | ErrorMessage
  | DoneMessage;
