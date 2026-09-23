import {
    Alert,
    Anchor,
    Badge,
    Button,
    Divider,
    Group,
    Loader,
    Paper,
    Stack,
    Text,
    TextInput,
    Title,
  } from "@mantine/core";
  import { useLocalStorage } from "@mantine/hooks";
  import { notifications } from "@mantine/notifications";
  import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
  import { Link, useParams } from "react-router";
  import { ApiError } from "../api/client";
  import { assignTicket, getTicket } from "../api/tickets";
  import { PriorityBadge } from "../components/PriorityBadge";
  
  const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  
  function formatDate(iso: string): string {
    return new Date(iso).toLocaleString();
  }
  
  function BackLink() {
    return (
      <Anchor component={Link} to="/" size="sm">
        ← Back to tickets
      </Anchor>
    );
  }
  
  export default function TicketDetailPage() {
    const ticketId = Number(useParams().ticketId);
    const isValidId = Number.isInteger(ticketId) && ticketId > 0;
    const queryClient = useQueryClient();
  
    // "Current user": the agent's email, remembered in the browser between visits
    const [email, setEmail] = useLocalStorage({ key: "agent-email", defaultValue: "" });
    const trimmedEmail = email.trim();
    const emailError =
      trimmedEmail && !EMAIL_PATTERN.test(trimmedEmail) ? "Enter a valid email address" : null;
  
    const {
      data: ticket,
      isPending,
      isError,
      error,
    } = useQuery({
      queryKey: ["ticket", ticketId],
      queryFn: () => getTicket(ticketId),
      enabled: isValidId,
    });
  
    const claim = useMutation({
      mutationFn: (agentEmail: string) => assignTicket(ticketId, agentEmail),
      onSuccess: (updated) => {
        queryClient.setQueryData(["ticket", ticketId], updated);
        queryClient.invalidateQueries({ queryKey: ["tickets"] }); // list must show the new owner
        notifications.show({
          color: "green",
          title: "Ticket claimed",
          message: `Ticket #${updated.id} is now assigned to ${updated.assigned_to}.`,
        });
      },
      onError: (err) => {
        if (err instanceof ApiError && err.status === 409) {
          // Another agent was faster: reload so the page shows the real owner
          queryClient.invalidateQueries({ queryKey: ["ticket", ticketId] });
          queryClient.invalidateQueries({ queryKey: ["tickets"] });
        }
        notifications.show({ color: "red", title: "Could not claim ticket", message: err.message });
      },
    });
  
    if (!isValidId) {
      return (
        <Alert color="red" title="Invalid ticket id">
          <BackLink />
        </Alert>
      );
    }
  
    if (isPending) {
      return (
        <Group justify="center" p="xl">
          <Loader />
        </Group>
      );
    }
  
    if (isError) {
      const notFound = error instanceof ApiError && error.status === 404;
      return (
        <Alert color="red" title={notFound ? "Ticket not found" : "Could not load ticket"}>
          <Text mb="sm">{error.message}</Text>
          <BackLink />
        </Alert>
      );
    }
  
    return (
      <Stack>
        <BackLink />
  
        <Paper withBorder p="lg">
          <Group justify="space-between" align="flex-start">
            <div>
              <Text c="dimmed" size="sm">
                Ticket #{ticket.id}
              </Text>
              <Title order={2}>{ticket.title}</Title>
            </div>
            <PriorityBadge priority={ticket.priority} />
          </Group>
  
          {ticket.tags.length > 0 && (
            <Group gap={4} mt="sm">
              {ticket.tags.map((tagName) => (
                <Badge key={tagName} variant="outline" size="sm">
                  {tagName}
                </Badge>
              ))}
            </Group>
          )}
  
          <Divider my="md" />
          <Text style={{ whiteSpace: "pre-wrap" }}>{ticket.description}</Text>
          <Divider my="md" />
  
          <Group gap="xl">
            <Text size="sm" c="dimmed">
              Created: {formatDate(ticket.created_at)}
            </Text>
            <Text size="sm" c="dimmed">
              Updated: {formatDate(ticket.updated_at)}
            </Text>
          </Group>
        </Paper>
  
        <Paper withBorder p="lg">
          <Title order={4} mb="sm">
            Assignment
          </Title>
  
          {ticket.assigned_to ? (
            <Text>
              Assigned to <b>{ticket.assigned_to}</b>
              {ticket.assigned_at && ` on ${formatDate(ticket.assigned_at)}`}
            </Text>
          ) : (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                if (trimmedEmail && !emailError) claim.mutate(trimmedEmail);
              }}
            >
              <Group align="flex-start">
                <TextInput
                  label="Your email"
                  placeholder="you@company.com"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.currentTarget.value)}
                  error={emailError}
                  required
                  w={300}
                />
                <Button
                  type="submit"
                  mt={25}
                  loading={claim.isPending}
                  disabled={!trimmedEmail || Boolean(emailError)}
                >
                  Claim ticket
                </Button>
              </Group>
            </form>
          )}
        </Paper>
      </Stack>
    );
  }