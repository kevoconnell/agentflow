import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Label } from "./ui/label";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";

interface AgentConfig {
  name: string;
  model: string;
  instructions: string;
  temperature?: number;
  tools?: string[];
  handoffs?: string[];
}

interface AgentEditorProps {
  agents: string[];
  workflowName?: string;
  onAgentUpdate?: (agentName: string, updates: Partial<AgentConfig>) => void;
}

const AVAILABLE_MODELS = [
  "gpt-4o",
  "gpt-4o-mini",
  "gpt-4-turbo",
  "gpt-3.5-turbo",
  "claude-3-5-sonnet-20241022",
  "claude-3-opus-20240229",
];

export default function AgentEditor({
  agents,
  workflowName,
  onAgentUpdate,
}: AgentEditorProps) {
  const [selectedAgent, setSelectedAgent] = useState<string>(agents[0] || "");
  const [agentDetails, setAgentDetails] = useState<AgentConfig | null>(null);
  const [editedInstructions, setEditedInstructions] = useState<string>("");
  const [editedModel, setEditedModel] = useState<string>("gpt-4o-mini");
  const [editedTemperature, setEditedTemperature] = useState<number>(0.7);
  const [isEditing, setIsEditing] = useState(false);

  // Fetch agent details when workflow or selected agent changes
  useEffect(() => {
    if (!workflowName || !selectedAgent) return;

    fetch(`/api/workflow/${workflowName}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.agents && data.agents[selectedAgent]) {
          const agent = data.agents[selectedAgent];
          setAgentDetails(agent);
          setEditedInstructions(agent.instructions || "");
          setEditedModel(agent.model || "gpt-4o-mini");
          setEditedTemperature(agent.temperature || 0.7);
        }
      })
      .catch((err) => console.error("Error fetching agent details:", err));
  }, [workflowName, selectedAgent]);

  const handleSave = () => {
    if (onAgentUpdate && selectedAgent) {
      onAgentUpdate(selectedAgent, {
        instructions: editedInstructions,
        model: editedModel,
        temperature: editedTemperature,
      });
      setIsEditing(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    // Reset to original values from agentDetails
    if (agentDetails) {
      setEditedInstructions(agentDetails.instructions || "");
      setEditedModel(agentDetails.model || "gpt-4o-mini");
      setEditedTemperature(agentDetails.temperature || 0.7);
    }
  };

  if (!selectedAgent) {
    return (
      <div className="text-muted-foreground text-sm">No agents available</div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Agent Selector */}
      <div className="space-y-2">
        <Label>Select Agent</Label>
        <Select value={selectedAgent} onValueChange={setSelectedAgent}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {agents.map((agent) => (
              <SelectItem key={agent} value={agent}>
                {agent}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Agent Details Card */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-base">{selectedAgent}</CardTitle>
          {!isEditing && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setIsEditing(true)}
            >
              Edit
            </Button>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Model */}
          <div className="space-y-2">
            <Label>Model</Label>
            {isEditing ? (
              <Select value={editedModel} onValueChange={setEditedModel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {AVAILABLE_MODELS.map((model) => (
                    <SelectItem key={model} value={model}>
                      {model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <div className="text-sm text-muted-foreground">{editedModel}</div>
            )}
          </div>

          {/* Instructions */}
          <div className="space-y-2">
            <Label>Instructions</Label>
            {isEditing ? (
              <Textarea
                value={editedInstructions}
                onChange={(e) => setEditedInstructions(e.target.value)}
                placeholder="Enter agent instructions..."
                rows={6}
                className="font-mono text-sm"
              />
            ) : (
              <div className="text-sm text-muted-foreground whitespace-pre-wrap bg-muted p-3 rounded">
                {editedInstructions || "No instructions set"}
              </div>
            )}
          </div>

          {/* Temperature */}
          <div className="space-y-2">
            <Label>Temperature: {editedTemperature}</Label>
            {isEditing ? (
              <Input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={editedTemperature}
                onChange={(e) =>
                  setEditedTemperature(parseFloat(e.target.value))
                }
              />
            ) : (
              <div className="text-sm text-muted-foreground">
                {editedTemperature}
              </div>
            )}
          </div>

          {/* Tools (read-only) */}
          {agentDetails?.tools && agentDetails.tools.length > 0 && (
            <div className="space-y-2">
              <Label>Tools</Label>
              <div className="flex flex-wrap gap-2">
                {agentDetails.tools.map((tool) => (
                  <Badge key={tool} variant="outline">
                    {tool}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Handoffs (read-only) */}
          {agentDetails?.handoffs && agentDetails.handoffs.length > 0 && (
            <div className="space-y-2">
              <Label>Handoffs</Label>
              <div className="flex flex-wrap gap-2">
                {agentDetails.handoffs.map((handoff) => (
                  <Badge key={handoff} variant="secondary">
                    {handoff}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {isEditing && (
            <div className="flex gap-2 pt-2">
              <Button size="sm" onClick={handleSave}>
                Save Changes
              </Button>
              <Button size="sm" variant="outline" onClick={handleCancel}>
                Cancel
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Help Text */}
      <div className="text-xs text-muted-foreground bg-muted p-3 rounded">
        💡 Changes are applied temporarily for this session. To persist changes,
        update your .agent.py file.
      </div>
    </div>
  );
}
