import { Label } from "./ui/label";
import { Input } from "./ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Separator } from "./ui/separator";

export interface ControlConfig {
  name: string;
  type: "text" | "number" | "select" | "boolean";
  label: string;
  defaultValue?: string | number | boolean;
  options?: string[];
  description?: string;
}

interface ControlsPanelProps {
  controls: ControlConfig[];
  values: Record<string, any>;
  onChange: (name: string, value: any) => void;
}

export default function ControlsPanel({
  controls,
  values,
  onChange,
}: ControlsPanelProps) {
  if (controls.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      {controls.map((control) => (
        <div key={control.name} className="space-y-2">
          <Label htmlFor={control.name}>
            {control.label}
            {control.description && (
              <span className="text-xs text-muted-foreground ml-2">
                {control.description}
              </span>
            )}
          </Label>

          {control.type === "text" && (
            <Input
              id={control.name}
              type="text"
              value={values[control.name] || control.defaultValue || ""}
              onChange={(e) => onChange(control.name, e.target.value)}
              placeholder={control.defaultValue?.toString()}
            />
          )}

          {control.type === "number" && (
            <Input
              id={control.name}
              type="number"
              value={values[control.name] || control.defaultValue || 0}
              onChange={(e) =>
                onChange(control.name, parseFloat(e.target.value))
              }
            />
          )}

          {control.type === "select" && control.options && (
            <Select
              value={values[control.name] || control.defaultValue?.toString()}
              onValueChange={(value) => onChange(control.name, value)}
            >
              <SelectTrigger id={control.name}>
                <SelectValue placeholder="Select an option" />
              </SelectTrigger>
              <SelectContent>
                {control.options.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          {control.type === "boolean" && (
            <div className="flex items-center space-x-2">
              <input
                id={control.name}
                type="checkbox"
                checked={values[control.name] || control.defaultValue || false}
                onChange={(e) => onChange(control.name, e.target.checked)}
                className="w-4 h-4 rounded border-gray-300"
              />
              <Label htmlFor={control.name} className="cursor-pointer">
                {control.label}
              </Label>
            </div>
          )}
        </div>
      ))}
      {controls.length > 1 && <Separator />}
    </div>
  );
}
