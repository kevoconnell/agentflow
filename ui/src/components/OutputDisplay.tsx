import { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { StreamEvent, ConversationMessage } from "../types";
import { Card, CardContent } from "./ui/card";
import { ScrollArea } from "./ui/scroll-area";
import { Badge } from "./ui/badge";
import { cn } from "@/lib/utils";

interface OutputDisplayProps {
  conversationHistory: ConversationMessage[];
  events: StreamEvent[];
  workflowName: string;
}

export default function OutputDisplay({
  conversationHistory,
  events,
  workflowName,
}: OutputDisplayProps) {
  const outputRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [conversationHistory, events]);

  // Custom link handler with confirmation
  const handleLinkClick = (
    e: React.MouseEvent<HTMLAnchorElement>,
    href?: string
  ) => {
    if (!href) return;

    e.preventDefault();
    const confirmed = window.confirm(
      `You are about to visit:\n\n${href}\n\nNavigate at your own risk. Continue?`
    );

    if (confirmed) {
      window.open(href, "_blank", "noopener,noreferrer");
    }
  };

  // Accumulate streaming text and events
  let accumulatedText = "";
  const toolCallEvents: StreamEvent[] = [];

  console.log("All events:", events);

  events.forEach((event) => {
    if (event.event_type === "run_item") {
      if (event.item_type === "tool_call_item") {
        console.log("Found tool_call_item:", event);
        toolCallEvents.push(event);
      } else if (event.item_type === "tool_call_output_item") {
        console.log("Found tool_call_output_item:", event);
        toolCallEvents.push(event);
      } else if (event.item_type === "message_output_item" && event.delta) {
        accumulatedText += event.delta;
      }
    }
  });

  console.log("Tool call events:", toolCallEvents);

  return (
    <Card className="flex-1 overflow-hidden">
      <ScrollArea className="h-full">
        <CardContent ref={outputRef} className="p-4">
          {/* Display all conversation history except the last assistant message if streaming */}
          {conversationHistory.map((msg, idx) => {
            // Skip the last assistant message if we're currently streaming
            const isLastAssistant =
              msg.role === "assistant" &&
              idx === conversationHistory.length - 1;
            if (isLastAssistant && events.length > 0) {
              return null;
            }

            return (
              <Card
                key={`history-${idx}`}
                className={cn(
                  "mb-4 border-l-4",
                  msg.role === "user"
                    ? "border-l-blue-500 bg-blue-500/10"
                    : "border-l-green-500 bg-green-500/10"
                )}
              >
                <CardContent className="p-3">
                  <Badge
                    variant={msg.role === "user" ? "default" : "secondary"}
                    className="mb-2"
                  >
                    {msg.role === "user"
                      ? "👤 You"
                      : `🤖 ${msg.workflow || workflowName || "Assistant"}`}
                  </Badge>
                  {msg.role === "assistant" ? (
                    <div className="prose dark:prose-invert prose-sm max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          a: ({ node, href, ...props }) => (
                            <a
                              {...props}
                              href={href}
                              onClick={(e) => handleLinkClick(e, href)}
                              className="cursor-pointer"
                            />
                          ),
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <div className="text-foreground">{msg.content}</div>
                  )}
                </CardContent>
              </Card>
            );
          })}

          {/* Display current streaming response as an assistant message */}
          {events.length > 0 && (
            <Card className="mb-4 border-l-4 border-l-green-500 bg-green-500/10">
              <CardContent className="p-3">
                <Badge variant="secondary" className="mb-2">
                  🤖 {workflowName || "Assistant"}
                </Badge>

                {/* Tool calls */}
                {toolCallEvents.map((event, idx) => {
                  if (event.item_type === "tool_call_item") {
                    return (
                      <div
                        key={`tool-${idx}`}
                        className="my-2 flex items-center gap-2"
                      >
                        <Badge variant="outline" className="text-blue-400">
                          🔧 {event.tool_name}
                        </Badge>
                        {event.tool_input && (
                          <span className="text-muted-foreground text-xs">
                            ({event.tool_input.substring(0, 50)}...)
                          </span>
                        )}
                      </div>
                    );
                  } else if (event.item_type === "tool_call_output_item") {
                    return (
                      <div key={`output-${idx}`} className="my-2">
                        <Badge
                          variant="outline"
                          className="text-green-400 mb-1"
                        >
                          ✓ Tool completed
                        </Badge>
                        {event.tool_output && (
                          <div className="text-muted-foreground text-xs pl-4 border-l-2 border-border mt-1">
                            <div className="font-semibold mb-1">Output:</div>
                            <div className="whitespace-pre-wrap break-words max-h-40 overflow-y-auto bg-background p-2 rounded">
                              {event.tool_output.substring(0, 500)}
                              {event.tool_output.length > 500 && "..."}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  }
                  return null;
                })}

                {/* Accumulated message text rendered as markdown */}
                {accumulatedText && (
                  <div className="prose dark:prose-invert prose-sm max-w-none mt-2">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        a: ({ node, href, ...props }) => (
                          <a
                            {...props}
                            href={href}
                            onClick={(e) => handleLinkClick(e, href)}
                            className="cursor-pointer"
                          />
                        ),
                      }}
                    >
                      {accumulatedText}
                    </ReactMarkdown>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </CardContent>
      </ScrollArea>
    </Card>
  );
}
