# Agent Flow UI

React TypeScript frontend for Agent Flow Playground.

## Development

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build
```

The build output will be placed in `../src/agent_flow/static/` which is served by the FastAPI backend.

## Components

- `App.tsx` - Main application component
- `WorkflowSidebar.tsx` - Workflow selection sidebar
- `InputPanel.tsx` - Input form and run button
- `OutputDisplay.tsx` - Real-time streaming output display
- `ToolCallSummary.tsx` - Collapsible tool calls summary

## Building for Production

Run `npm run build` from this directory. The built files will be output to `../src/agent_flow/static/`.

The Python package will serve these static files when running the UI server.
