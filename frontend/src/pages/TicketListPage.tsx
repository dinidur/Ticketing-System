import {
    Alert,
    Badge,
    Button,
    Group,
    Loader,
    Paper,
    SegmentedControl,
    Select,
    Table,
    Text,
    TextInput,
    Title,
  } from "@mantine/core";
  import { useDebouncedValue } from "@mantine/hooks";
  import { keepPreviousData, useQuery } from "@tanstack/react-query";
  import { useState } from "react";
  import { useNavigate } from "react-router";
  import { listTickets } from "../api/tickets";
  import { PRIORITIES, type Priority, type TicketFilters } from "../api/types";
  import { PriorityBadge } from "../components/PriorityBadge";
  
  type AssignmentFilter = "all" | "unassigned" | "assigned";
  
  export default function TicketListPage() {
    const navigate = useNavigate();
  
    // ----- Filters -----
    const [priority, setPriority] = useState<Priority | null>(null);
    const [assignment, setAssignment] = useState<AssignmentFilter>("all");
    const [tagInput, setTagInput] = useState("");
    const [tag] = useDebouncedValue(tagInput.trim().toLowerCase(), 400); // don't call API on every key
  
    const filters: TicketFilters = {
      priority: priority ?? undefined,
      assigned: assignment === "all" ? undefined : assignment === "assigned",
      tag: tag || undefined,
    };
  
    // ----- Cursor pagination -----
    // A stack of cursors lets us go back. It resets automatically when the filters change.
    const filterKey = JSON.stringify(filters);
    const [pagination, setPagination] = useState<{ filterKey: string; cursors: (string | null)[] }>({
      filterKey,
      cursors: [null],
    });
    const cursors = pagination.filterKey === filterKey ? pagination.cursors : [null];
    const cursor = cursors[cursors.length - 1];
    const pageNumber = cursors.length;
  
    const { data, isPending, isError, error, isFetching } = useQuery({
      queryKey: ["tickets", filters, cursor],
      queryFn: () => listTickets(filters, cursor),
      placeholderData: keepPreviousData, // keep the old page visible while the next one loads
    });
  
    function goNext() {
      if (data?.next_cursor) {
        setPagination({ filterKey, cursors: [...cursors, data.next_cursor] });
      }
    }
  
    function goPrevious() {
      setPagination({ filterKey, cursors: cursors.slice(0, -1) });
    }
  
    return (
      <>
        <Group justify="space-between" mb="md">
          <Title order={2}>Tickets</Title>
          {isFetching && <Loader size="sm" />}
        </Group>
  
        <Paper withBorder p="md" mb="md">
          <Group align="flex-end" wrap="wrap">
            <Select
              label="Priority"
              placeholder="All priorities"
              clearable
              data={PRIORITIES}
              value={priority}
              onChange={(value) => setPriority(value as Priority | null)}
              w={180}
            />
            <div>
              <Text size="sm" fw={500} mb={4}>
                Assignment
              </Text>
              <SegmentedControl
                value={assignment}
                onChange={(value) => setAssignment(value as AssignmentFilter)}
                data={[
                  { label: "All", value: "all" },
                  { label: "Unassigned", value: "unassigned" },
                  { label: "Assigned", value: "assigned" },
                ]}
              />
            </div>
            <TextInput
              label="Tag"
              placeholder="e.g. vpn"
              value={tagInput}
              onChange={(event) => setTagInput(event.currentTarget.value)}
              w={180}
            />
          </Group>
        </Paper>
  
        {isError && (
          <Alert color="red" title="Could not load tickets" mb="md">
            {error.message}
          </Alert>
        )}
  
        {isPending && (
          <Group justify="center" p="xl">
            <Loader />
          </Group>
        )}
  
        {data && (
          <>
            <Table.ScrollContainer minWidth={800}>
              <Table highlightOnHover striped>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>#</Table.Th>
                    <Table.Th>Title</Table.Th>
                    <Table.Th>Priority</Table.Th>
                    <Table.Th>Tags</Table.Th>
                    <Table.Th>Assigned to</Table.Th>
                    <Table.Th>Created</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {data.items.length === 0 && (
                    <Table.Tr>
                      <Table.Td colSpan={6}>
                        <Text c="dimmed" ta="center" py="lg">
                          No tickets found.
                        </Text>
                      </Table.Td>
                    </Table.Tr>
                  )}
                  {data.items.map((ticket) => (
                    <Table.Tr
                      key={ticket.id}
                      onClick={() => navigate(`/tickets/${ticket.id}`)}
                      style={{ cursor: "pointer" }}
                    >
                      <Table.Td>{ticket.id}</Table.Td>
                      <Table.Td>{ticket.title}</Table.Td>
                      <Table.Td>
                        <PriorityBadge priority={ticket.priority} />
                      </Table.Td>
                      <Table.Td>
                        <Group gap={4}>
                          {ticket.tags.map((tagName) => (
                            <Badge key={tagName} variant="outline" size="sm">
                              {tagName}
                            </Badge>
                          ))}
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        {ticket.assigned_to ?? (
                          <Badge color="green" variant="light">
                            Unassigned
                          </Badge>
                        )}
                      </Table.Td>
                      <Table.Td>{new Date(ticket.created_at).toLocaleString()}</Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Table.ScrollContainer>
  
            <Group justify="space-between" mt="md">
              <Text size="sm" c="dimmed">
                Page {pageNumber}
              </Text>
              <Group>
                <Button variant="default" onClick={goPrevious} disabled={pageNumber === 1}>
                  ← Previous
                </Button>
                <Button variant="default" onClick={goNext} disabled={!data.has_more}>
                  Next →
                </Button>
              </Group>
            </Group>
          </>
        )}
      </>
    );
  }