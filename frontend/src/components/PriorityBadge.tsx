import { Badge } from "@mantine/core";
import type { Priority } from "../api/types";

const COLORS: Record<Priority, string> = {
  low: "gray",
  medium: "blue",
  high: "orange",
  critical: "red",
};

export function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <Badge color={COLORS[priority]} variant="light">
      {priority}
    </Badge>
  );
}