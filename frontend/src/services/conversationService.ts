import api from './api';
import type { Conversation, Message, MessageMetadata } from '@/types/conversation';
import {
  cloneConversations,
  createNewConversation,
  appendUserMessage,
  transferConversation,
} from '@/mocks/conversations';

const useMock = import.meta.env.VITE_USE_MOCK === 'true';

interface ConversationListResponse {
  items: Omit<Conversation, 'messages'>[];
  total: number;
  page: number;
  page_size: number;
}

export const conversationService = {
  async list(): Promise<Conversation[]> {
    if (useMock) {
      return cloneConversations();
    }

    const response = await api.get<{ code: number; message: string; data: ConversationListResponse }>(
      '/conversations',
      { params: { page: 1, page_size: 50 } }
    );

    if (response.data.code === 200) {
      // Convert list items to full Conversation objects with empty messages array
      return response.data.data.items.map((item) => ({
        ...item,
        messages: [],
      }));
    }

    throw new Error(response.data.message);
  },

  async get(id: number): Promise<Conversation | undefined> {
    if (useMock) {
      return cloneConversations().find((c) => c.id === id);
    }

    try {
      const response = await api.get<{ code: number; message: string; data: Conversation }>(
        `/conversations/${id}`
      );

      if (response.data.code === 200) {
        return response.data.data;
      }

      throw new Error(response.data.message);
    } catch (error: unknown) {
      // Return undefined for 404 (conversation not found)
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { status?: number } };
        if (axiosError.response?.status === 404) {
          return undefined;
        }
      }
      throw error;
    }
  },

  async create(title?: string): Promise<Conversation> {
    if (useMock) {
      return createNewConversation();
    }

    const response = await api.post<{
      code: number;
      message: string;
      data: Omit<Conversation, 'messages'>;
    }>('/conversations', {
      title: title || '新对话',
    });

    if (response.data.code === 200) {
      // Convert to full Conversation object with empty messages array
      return {
        ...response.data.data,
        messages: [],
      };
    }

    throw new Error(response.data.message);
  },

  async sendMessage(
    conversationId: number,
    content: string,
    existing?: Conversation
  ): Promise<Conversation | undefined> {
    if (useMock) {
      return appendUserMessage(conversationId, content) ?? undefined;
    }

    const response = await api.post<{
      code: number;
      message: string;
      data: {
        user_message: {
          id: number;
          role: string;
          content: string;
          metadata: Record<string, unknown> | null;
          created_at: string;
        };
        assistant_message: {
          id: number;
          role: string;
          content: string;
          metadata: {
            response_type: string;
            intent: string;
            citations: Array<{
              file_id: number;
              filename: string;
              chunk_index: number;
              preview: string;
              similarity: number;
            }>;
          } | null;
          created_at: string;
        };
      };
    }>(`/conversations/${conversationId}/messages`, {
      content,
    });

    if (response.data.code === 200) {
      const { user_message, assistant_message } = response.data.data;
      const detail = await this.get(conversationId);
      if (detail) {
        return detail;
      }

      if (!existing) {
        throw new Error('会话不存在');
      }
      const base = existing;

      const prior = base.messages.filter((m) => m.id > 0);
      const userMsg: Message = {
        id: user_message.id,
        role: user_message.role as Message['role'],
        content: user_message.content,
        metadata: user_message.metadata as MessageMetadata | null,
        created_at: user_message.created_at,
      };
      const assistantMsg: Message = {
        id: assistant_message.id,
        role: assistant_message.role as Message['role'],
        content: assistant_message.content,
        metadata: assistant_message.metadata as MessageMetadata | null,
        created_at: assistant_message.created_at,
      };
      return {
        ...base,
        updated_at: assistant_message.created_at,
        messages: [...prior, userMsg, assistantMsg],
      };
    }

    throw new Error(response.data.message);
  },

  async transfer(conversationId: number): Promise<Conversation | undefined> {
    if (useMock) {
      return transferConversation(conversationId) ?? undefined;
    }

    const response = await api.post<{
      code: number;
      message: string;
      data: {
        conversation_id: number;
        conversation_status: string;
        ticket: {
          id: number;
          conversation_id: number;
          status: string;
          created_at: string;
        };
      };
    }>(`/conversations/${conversationId}/transfer`);

    if (response.data.code === 200) {
      return await this.get(conversationId);
    }

    throw new Error(response.data.message);
  },
};
