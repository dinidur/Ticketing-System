export type Priority = "low" | "medium" | "high" | "critical";

export const PRIORITIES: Priority[] = ["low", "medium", "high", "critical"];

export interface Ticket {
  id: number;
  title: string;
  description: string;
  priority: Priority;
  tags: string[];
  assigned_to: string | null;
  assigned_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketPage {
  items: Ticket[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface TicketFilters {
  priority?: Priority;
  assigned?: boolean;
  tag?: string;
}