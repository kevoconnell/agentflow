import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Textarea } from "./ui/textarea";
import { Button } from "./ui/button";

interface InputPanelProps {
  input: string;
  onInputChange: (value: string) => void;
  onRun: () => void;
  isRunning: boolean;
  disabled: boolean;
}

export default function InputPanel({
  input,
  onInputChange,
  onRun,
  isRunning,
  disabled,
}: InputPanelProps) {
  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle>Input</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Textarea
          rows={3}
          placeholder="Enter your prompt here..."
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
        />
        <Button
          onClick={onRun}
          disabled={isRunning || disabled}
          className="w-full sm:w-auto"
        >
          {isRunning ? 'Running...' : 'Run Workflow'}
        </Button>
      </CardContent>
    </Card>
  );
}
