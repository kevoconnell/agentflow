import { Workflow } from "../types";
import { Card, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { ScrollArea } from "./ui/scroll-area";
import { cn } from "@/lib/utils";

interface WorkflowSidebarProps {
  workflows: Workflow[];
  selectedWorkflow: string | null;
  onSelect: (name: string) => void;
}

export default function WorkflowSidebar({
  workflows,
  selectedWorkflow,
  onSelect,
}: WorkflowSidebarProps) {
  return (
    <aside className="w-80 bg-card border-r border-border p-6">
      <h2 className="text-lg font-semibold mb-4">Agents</h2>
      <ScrollArea className="h-[calc(100vh-120px)]">
        <div className="space-y-3 pr-4">
          {workflows.length === 0 ? (
            <div className="text-muted-foreground italic">No agents found</div>
          ) : (
            workflows.map((wf) => (
              <Card
                key={wf.name}
                className={cn(
                  "cursor-pointer transition-all hover:shadow-lg",
                  selectedWorkflow === wf.name && "ring-2 ring-primary"
                )}
                onClick={() => onSelect(wf.name)}
              >
                <CardHeader className="p-4">
                  <CardTitle className="text-base">{wf.name}</CardTitle>
                  <CardDescription className="text-xs">
                    Sub-Agents: {wf.agents.join(", ")}
                  </CardDescription>
                </CardHeader>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>
    </aside>
  );
}
