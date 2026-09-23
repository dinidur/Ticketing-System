import { apiFetch } from "./client";
import type { Ticket, TicketFilters, TicketPage } from "./types";

export const PAGE_SIZE = 20;

export function listTickets(filters: TicketFilters, cursor: string | null): Promise<TicketPage> {
  const params = new URLSearchParams({ limit: String(PAGE_SIZE) });
  if (cursor) params.set("cursor", cursor);
  if (filters.priority) params.set("priority", filters.priority);
  if (filters.assigned !== undefined) params.set("assigned", String(filters.assigned));
  if (filters.tag) params.set("tag", filters.tag);
  return apiFetch<TicketPage>(`/tickets?${params}`);
}

export function getTicket(id: number): Promise<Ticket> {
  return apiFetch<Ticket>(`/tickets/${id}`);
}

export function assignTicket(id: number, email: string): Promise<Ticket> {
  return apiFetch<Ticket>(`/tickets/${id}/assign`, {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}