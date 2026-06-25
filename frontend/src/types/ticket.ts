import type { Message } from './conversation';

export type TicketStatus = 'pending' | 'processing' | 'completed';

export type TicketCategory = 'it' | 'hr' | 'finance' | 'admin' | 'other';

export interface Ticket {
  id: number;
  conversation_id: number;
  user_id: number;
  user_name: string;
  agent_id: number | null;
  category: TicketCategory | null;
  status: TicketStatus;
  summary: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface SuggestItem {
  index: number;
  content: string;
}
