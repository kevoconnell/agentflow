import { useState } from 'react';
import { ToolCall } from '../types';

interface ToolCallSummaryProps {
  toolCalls: ToolCall[];
}

export default function ToolCallSummary({ toolCalls }: ToolCallSummaryProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <details
      className="mt-4"
      open={isOpen}
      onToggle={(e) => setIsOpen((e.target as HTMLDetailsElement).open)}
    >
      <summary className="cursor-pointer text-sm font-semibold text-blue-400 hover:text-blue-300 select-none list-none">
        <span className="inline-flex items-center gap-2">
          <span className="transform transition-transform" style={{
            transform: isOpen ? 'rotate(90deg)' : 'rotate(0deg)'
          }}>
            ▶
          </span>
          Tool Calls Summary ({toolCalls.length})
        </span>
      </summary>
      <div className="mt-2 space-y-2">
        {toolCalls.map((call, idx) => (
          <div
            key={idx}
            className="ml-4 p-3 bg-gray-800 rounded border-l-2 border-blue-500"
          >
            <div className="font-semibold text-blue-400">
              {idx + 1}. {call.name}
            </div>
            {call.input && (
              <div className="text-sm text-gray-400 mt-1">
                <span className="font-medium">Input:</span> {call.input}
              </div>
            )}
            {call.output && (
              <div className="text-sm text-green-400 mt-1">
                <span className="font-medium">Output:</span> {call.output}
              </div>
            )}
          </div>
        ))}
      </div>
    </details>
  );
}
