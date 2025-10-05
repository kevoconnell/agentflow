"""
Web UI playground for agent workflows using FastAPI.
"""

import sys
from pathlib import Path
from typing import Any, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from agents import Runner, ItemHelpers

from .loader import find_workflow_files, load_workflow


def serialize_stream_event(event: Any) -> Dict[str, Any]:
    """
    Convert stream event objects to JSON-serializable dictionaries.
    
    Args:
        event: Stream event from the agents SDK
        
    Returns:
        Dictionary that can be serialized to JSON
    """
    event_dict: Dict[str, Any] = {"type": event.type}
    
    if event.type == "agent_updated_stream_event":
        # AgentUpdatedStreamEvent
        event_dict["event_type"] = "agent_updated"
        event_dict["new_agent_name"] = event.new_agent.name if hasattr(event, "new_agent") else None
        
    elif event.type == "run_item_stream_event":
        # RunItemStreamEvent
        event_dict["event_type"] = "run_item"
        event_dict["name"] = event.name if hasattr(event, "name") else None
        
        if hasattr(event, "item"):
            item = event.item
            item_type = item.type if hasattr(item, "type") else None
            event_dict["item_type"] = item_type
            
            # Handle different item types
            if item_type == "message_output_item":
                # Extract text content from message
                content = ItemHelpers.text_message_output(item)
                event_dict["delta"] = content
                event_dict["agent"] = item.agent_name if hasattr(item, "agent_name") else None
                
            elif item_type == "tool_call_item":
                # Extract tool information from raw_item
                tool_name = None
                tool_input = None
                print(f"Item: {item}")

                
                if hasattr(item, "raw_item"):
                    raw = item.raw_item
                    # Extract tool name (e.g., 'web_search_call')
                    if hasattr(raw, "type") and raw.type is not "function_call":
                        tool_name = raw.type
                    elif hasattr(raw, "name"):
                        tool_name = raw.name
                    
                    # Extract tool input/action
                    if hasattr(raw, "action"):
                        tool_input = str(raw.action)
                    elif hasattr(raw, "arguments"):
                        tool_input = str(raw.arguments)
                    elif hasattr(raw, "function") and hasattr(raw.function, "arguments"):
                        tool_input = str(raw.function.arguments)

                
                event_dict["tool_name"] = tool_name
                event_dict["tool_input"] = tool_input
                event_dict["agent"] = item.agent.name if hasattr(item, "agent") else None
                
            elif item_type == "tool_call_output_item":
                # Extract tool output
                tool_output = None
                if hasattr(item, "raw_item"):
                    raw = item.raw_item
                    if hasattr(raw, "content"):
                        tool_output = raw.content
                    elif hasattr(raw, "output"):
                        tool_output = raw.output
                
                if not tool_output and hasattr(item, "output"):
                    tool_output = item.output
                
                event_dict["tool_output"] = str(tool_output) if tool_output else None
                event_dict["agent"] = item.agent.name if hasattr(item, "agent") else None
                
    elif event.type == "raw_response_event":
        # RawResponsesStreamEvent - we'll skip these in the handler
        event_dict["event_type"] = "raw_response"
        
    return event_dict


app = FastAPI(title="Agent Flow Playground")

# Mount static files (React build output)
static_dir = Path(__file__).parent / "static"


@app.get("/api/workflows")
async def list_workflows():
    """List all available workflows."""
    workflow_files = find_workflow_files()
    workflows = []

    for wf_path in workflow_files:
        try:
            spec = load_workflow(wf_path)
            # Remove both .workflow and .agent suffixes
            name = wf_path.stem.replace(".workflow", "").replace(".agent", "")

            # Load controls from FlowSpec
            controls = spec.controls if hasattr(spec, 'controls') and spec.controls else None

            workflow_data = {
                "name": name,
                "file": str(wf_path),
                "agents": list(spec.agents.keys())
            }

            if controls:
                workflow_data["controls"] = controls

            workflows.append(workflow_data)
        except Exception as e:
            print(f"Error loading {wf_path}: {e}")

    return {"workflows": workflows}


@app.get("/api/workflow/{workflow_name}")
async def get_workflow(workflow_name: str):
    """Get details of a specific workflow."""
    workflow_files = find_workflow_files()
    workflow_path = None

    for wf in workflow_files:
        name = wf.stem.replace(".workflow", "").replace(".agent", "")
        if name == workflow_name:
            workflow_path = wf
            break

    if not workflow_path:
        return {"error": "Workflow not found"}

    try:
        spec = load_workflow(workflow_path)
        agents_info = {}

        for name, agent in spec.agents.items():
            instructions = getattr(agent, "instructions", "")
            if callable(instructions):
                instructions = "Dynamic instructions (callable)"

            # Get tools info
            tools = getattr(agent, "tools", [])
            tool_names = []
            for tool in tools:
                tool_name = None
                if hasattr(tool, "name"):
                    tool_name = tool.name
                elif hasattr(tool, "__name__"):
                    tool_name = tool.__name__
                elif callable(tool):
                    # Try to get function name from callable
                    tool_name = getattr(tool, "__name__", str(tool))
                
                if tool_name:
                    tool_names.append(tool_name)
                else:
                    # Fallback: use string representation
                    tool_names.append(str(tool))

            # Get handoffs info
            handoffs = getattr(agent, "handoffs", [])
            handoff_names = []
            for handoff in handoffs:
                if hasattr(handoff, "name"):
                    handoff_names.append(handoff.name)

            agents_info[name] = {
                "name": name,
                "model": getattr(agent, "model", "unknown"),
                "instructions": instructions,
                "temperature": getattr(agent, "temperature", 0.7),
                "tools": tool_names,
                "handoffs": handoff_names,
            }

        return {
            "name": workflow_name,
            "agents": agents_info,
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/workflow/{workflow_name}/agent/{agent_name}")
async def update_agent(workflow_name: str, agent_name: str, updates: dict):
    """Update agent configuration temporarily for this session."""
    # For now, just acknowledge the update
    # In a full implementation, you'd update the in-memory agent config
    return {
        "success": True,
        "workflow": workflow_name,
        "agent": agent_name,
        "updates": updates
    }


@app.websocket("/ws/run")
async def websocket_run(websocket: WebSocket):
    """WebSocket endpoint for running workflows with streaming."""
    await websocket.accept()

    try:
        # Receive configuration
        data = await websocket.receive_json()
        workflow_name = data.get("workflow")
        messages = data.get("messages", [])

        if not workflow_name or not messages:
            await websocket.send_json({"error": "Missing required fields"})
            await websocket.close()
            return

        # Load workflow
        workflow_files = find_workflow_files()
        workflow_path = None

        for wf in workflow_files:
            name = wf.stem.replace(".workflow", "").replace(".agent", "")
            if name == workflow_name:
                workflow_path = wf
                break

        if not workflow_path:
            await websocket.send_json({"error": "Workflow not found"})
            await websocket.close()
            return

        spec = load_workflow(workflow_path)

        # Get the first agent
        if not spec.agents:
            await websocket.send_json({"error": "No agents defined in workflow"})
            await websocket.close()
            return

        # Use first agent in the dict
        agent_name = next(iter(spec.agents.keys()))
        agent = spec.agents[agent_name]

        # Convert messages to the format expected by the SDK
        # The last message should be the user input
        user_input = messages[-1]["content"] if messages else ""

        # Run with streaming
        try:
            result = Runner.run_streamed(agent, input=user_input)

            # Track tool calls for summary
            tool_calls_summary = []
            current_tool_call = {}

            async for event in result.stream_events():
                # We'll ignore the raw responses event deltas
                if event.type == "raw_response_event":
                    continue
                elif event.type == "agent_updated_stream_event":
                    print(f"Agent updated: {event.new_agent.name}")
                    
                elif event.type == "run_item_stream_event":
                    if event.item.type == "tool_call_item":
                        # Track tool call for summary
                        tool_name = None
                        tool_input = None

                        # print the item
                        print(f"Item: {event.item}")
                        
                        
                        if hasattr(event.item, "raw_item"):
                            raw = event.item.raw_item
                            print(f"Raw: {raw}")
                            if hasattr(raw, "type") and raw.type is not "function_call":
                                tool_name = raw.type
                            elif hasattr(raw, "name"):
                                tool_name = raw.name
                            elif hasattr(raw, "function") and hasattr(raw.function, "name"):
                                tool_name = raw.function.name
                            
                            if hasattr(raw, "action"):
                                tool_input = str(raw.action)
                            elif hasattr(raw, "arguments"):
                                tool_input = str(raw.arguments)
                            elif hasattr(raw, "function") and hasattr(raw.function, "arguments"):
                                tool_input = str(raw.function.arguments)
                        
                        if not tool_name:
                            tool_name = event.item.name
                        
                        if not tool_input and hasattr(event.item, "input"):
                            tool_input = str(event.item.input)
                        
                        current_tool_call = {
                            "name": tool_name or "unknown",
                            "input": tool_input or "",
                            "output": None
                        }
                        
                    elif event.item.type == "tool_call_output_item":
                        # Extract tool output and complete the current tool call
                        tool_output = None
                        if hasattr(event.item, "raw_item"):
                            raw = event.item.raw_item
                            if hasattr(raw, "content"):
                                tool_output = raw.content
                            elif hasattr(raw, "output"):
                                tool_output = raw.output
                        
                        if not tool_output and hasattr(event.item, "output"):
                            tool_output = event.item.output
                        
                        if current_tool_call:
                            current_tool_call["output"] = str(tool_output) if tool_output else None
                            tool_calls_summary.append(current_tool_call)
                            current_tool_call = {}
        
                # Serialize the event before sending
                serialized_event = serialize_stream_event(event)
                await websocket.send_json(serialized_event)
            
            # Extract tool calls from result.new_items if not already captured during streaming
            if not tool_calls_summary and hasattr(result, 'new_items'):
                temp_tool_call = {}
                
                for item in result.new_items:
                    item_type = item.type if hasattr(item, 'type') else None
                    
                    if item_type == "tool_call_item":
                        tool_name = None
                        tool_input = None
                        
                        if hasattr(item, "raw_item"):
                            raw = item.raw_item
                            if hasattr(raw, "type"):
                                tool_name = raw.type
                            elif hasattr(raw, "name"):
                                tool_name = raw.name
                            elif hasattr(raw, "function") and hasattr(raw.function, "name"):
                                tool_name = raw.function.name
                            
                            if hasattr(raw, "action"):
                                tool_input = str(raw.action)
                            elif hasattr(raw, "arguments"):
                                tool_input = str(raw.arguments)
                            elif hasattr(raw, "function") and hasattr(raw.function, "arguments"):
                                tool_input = str(raw.function.arguments)
                        
                        if not tool_name and hasattr(item, "name"):
                            tool_name = item.name
                        
                        if not tool_input and hasattr(item, "input"):
                            tool_input = str(item.input)
                        
                        temp_tool_call = {
                            "name": tool_name or "unknown",
                            "input": tool_input or "",
                            "output": None
                        }
                        
                    elif item_type == "tool_call_output_item":
                        if temp_tool_call:
                            tool_output = None
                            if hasattr(item, "raw_item"):
                                raw = item.raw_item
                                if hasattr(raw, "content"):
                                    tool_output = raw.content
                                elif hasattr(raw, "output"):
                                    tool_output = raw.output
                            
                            if not tool_output and hasattr(item, "output"):
                                tool_output = item.output
                            
                            temp_tool_call["output"] = str(tool_output) if tool_output else None
                            tool_calls_summary.append(temp_tool_call)
                            temp_tool_call = {}
              

            result_info = {
                "type": "result",
                "agent": agent_name,
                "last_agent": result.last_agent.name if result.last_agent else None,
                "last_response_id": result.last_response_id if hasattr(result, 'last_response_id') else None,
                "num_new_items": len(result.new_items) if hasattr(result, 'new_items') else 0,
                "num_raw_responses": len(result.raw_responses) if hasattr(result, 'raw_responses') else 0,
                "tool_calls": tool_calls_summary,
            }

            # Add guardrail results if available
            if hasattr(result, 'input_guardrail_results') and result.input_guardrail_results:
                result_info["input_guardrails"] = len(result.input_guardrail_results)
            if hasattr(result, 'output_guardrail_results') and result.output_guardrail_results:
                result_info["output_guardrails"] = len(result.output_guardrail_results)

            await websocket.send_json(result_info)
            await websocket.send_json({"type": "done"})

        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            print(f"Error getting response: {error_msg}")
            await websocket.send_json({"type": "error", "message": str(e)})

        await websocket.close()

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
            await websocket.close()
        except:
            pass


# Mount static files after all routes are defined
# This serves the assets directory and other static files
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")




def start_ui(host: str = "0.0.0.0", port: int = 7000, rebuild: bool = False, open_browser: bool = True):
    """
    Start the UI server.

    Args:
        host: Host to bind to
        port: Port to bind to
        rebuild: Force a rebuild of the React UI even if not needed
        open_browser: Whether to automatically open the browser
    """
    from .build_ui import ensure_ui_built
    import webbrowser
    import threading
    import time

    # Ensure UI is built before starting the server
    error = ensure_ui_built(force=rebuild)
    if error:
        print(f"\n❌ Failed to start UI server:\n{error}\n", file=sys.stderr)
        sys.exit(1)

    import uvicorn
    
    # Determine the URL to open
    display_host = "localhost" if host in ["0.0.0.0", "127.0.0.1"] else host
    url = f"http://{display_host}:{port}"
    
    print(f"\n🚀 Starting Agent Flow Playground at {url}\n")
    print("📁 Watching .agent files for changes...\n")

    # Open browser after a short delay to let server start
    if open_browser:
        def _open_browser():
            time.sleep(1.5)  # Wait for server to be ready
            try:
                webbrowser.open(url)
            except Exception as e:
                # Don't fail if browser opening fails
                print(f"Note: Could not automatically open browser: {e}")
        
        # Start browser opening in background thread
        threading.Thread(target=_open_browser, daemon=True).start()

    # Configure uvicorn to watch for .agent file changes
    # Must pass as import string for reload to work
    uvicorn.run(
        "agent_flow.api:app",
        host=host,
        port=port,
        reload=True,
        reload_includes=["*.agent.py", "*.agent"]
    )
