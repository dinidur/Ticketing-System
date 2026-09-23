import { Anchor, AppShell, Container, Group, Text, Title } from "@mantine/core";
import { Link, Route, Routes } from "react-router";
import TicketDetailPage from "./pages/TicketDetailPage";
import TicketListPage from "./pages/TicketListPage";

export default function App() {
  return (
    <AppShell header={{ height: 60 }} padding="md">
      <AppShell.Header>
        <Container size="lg" h="100%">
          <Group h="100%">
            <Anchor component={Link} to="/" underline="never" c="inherit">
              <Title order={3}>🎫 Support Tickets</Title>
            </Anchor>
          </Group>
        </Container>
      </AppShell.Header>

      <AppShell.Main>
        <Container size="lg">
          <Routes>
            <Route path="/" element={<TicketListPage />} />
            <Route path="/tickets/:ticketId" element={<TicketDetailPage />} />
            <Route path="*" element={<Text c="dimmed">Page not found.</Text>} />
          </Routes>
        </Container>
      </AppShell.Main>
    </AppShell>
  );
}