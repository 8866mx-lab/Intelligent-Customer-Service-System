import api from './api';
import type { Ticket, TicketCategory, SuggestItem } from '@/types/ticket';
import {
  cloneTickets,
  acceptTicket,
  sendAgentMessage,
  updateTicketCategory,
  completeTicket,
  getSuggestions,
} from '@/mocks/tickets';

const useMock = import.meta.env.VITE_USE_MOCK === 'true';

type TicketListItem = Omit<Ticket, 'messages'>;

function toTicket(item: TicketListItem, messages: Ticket['messages'] = []): Ticket {
  return { ...item, messages };
}

export const ticketService = {
  async list(): Promise<Ticket[]> {
    if (useMock) return cloneTickets();

    const response = await api.get<{
      code: number;
      message: string;
      data: { items: TicketListItem[] };
    }>('/tickets', { params: { page: 1, page_size: 50 } });

    if (response.data.code === 200) {
      return response.data.data.items.map((item) => toTicket(item));
    }

    throw new Error(response.data.message);
  },

  async get(id: number): Promise<Ticket | undefined> {
    if (useMock) return cloneTickets().find((t) => t.id === id);

    const response = await api.get<{ code: number; message: string; data: Ticket }>(
      `/tickets/${id}`
    );

    if (response.data.code === 200) {
      return response.data.data;
    }

    throw new Error(response.data.message);
  },

  async accept(ticketId: number): Promise<Ticket | undefined> {
    if (useMock) return acceptTicket(ticketId) ?? undefined;

    const response = await api.post<{ code: number; message: string }>(
      `/tickets/${ticketId}/accept`
    );

    if (response.data.code === 200) {
      return await this.get(ticketId);
    }

    throw new Error(response.data.message);
  },

  async sendMessage(ticketId: number, content: string): Promise<Ticket | undefined> {
    if (useMock) return sendAgentMessage(ticketId, content) ?? undefined;

    const response = await api.post<{
      code: number;
      message: string;
      data: {
        id: number;
        role: string;
        content: string;
        created_at: string;
      };
    }>(`/tickets/${ticketId}/messages`, { content });

    if (response.data.code === 200) {
      return await this.get(ticketId);
    }

    throw new Error(response.data.message);
  },

  async suggest(ticketId: number): Promise<SuggestItem[]> {
    if (useMock) return getSuggestions();

    const response = await api.post<{
      code: number;
      message: string;
      data: { suggestions: SuggestItem[] };
    }>(`/tickets/${ticketId}/suggest`);

    if (response.data.code === 200) {
      return response.data.data.suggestions;
    }

    throw new Error(response.data.message);
  },

  async updateCategory(ticketId: number, category: TicketCategory): Promise<Ticket | undefined> {
    if (useMock) return updateTicketCategory(ticketId, category) ?? undefined;

    const response = await api.patch<{ code: number; message: string }>(
      `/tickets/${ticketId}`,
      { category }
    );

    if (response.data.code === 200) {
      return await this.get(ticketId);
    }

    throw new Error(response.data.message);
  },

  async complete(ticketId: number): Promise<Ticket | undefined> {
    if (useMock) return completeTicket(ticketId) ?? undefined;

    const response = await api.patch<{ code: number; message: string }>(
      `/tickets/${ticketId}`,
      { status: 'completed' }
    );

    if (response.data.code === 200) {
      return await this.get(ticketId);
    }

    throw new Error(response.data.message);
  },
};
