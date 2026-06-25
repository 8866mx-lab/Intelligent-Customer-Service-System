import type { ConversationStatus, Message } from './conversation';
import type { TicketStatus } from './ticket';

export type WsEventType = 'new_message' | 'ticket_status_changed' | 'ticket_created';

export interface WsNewMessageData {
  conversation_id: number;
  ticket_id?: number;
  message: Message;
}

export interface WsTicketStatusChangedData {
  ticket_id: number;
  status: TicketStatus;
  conversation_id: number;
  conversation_status: ConversationStatus;
}

export interface WsTicketCreatedData {
  ticket_id: number;
  conversation_id: number;
  status: TicketStatus;
}

export type WsEvent =
  | { event: 'new_message'; data: WsNewMessageData }
  | { event: 'ticket_status_changed'; data: WsTicketStatusChangedData }
  | { event: 'ticket_created'; data: WsTicketCreatedData };
