export type ConversationStatus = 'ai_chat' | 'queuing' | 'processing' | 'completed';

export type MessageRole = 'user' | 'assistant' | 'agent' | 'system';

export interface Citation {
  file_id: number;
  filename: string;
  chunk_index: number;
  preview: string;
  similarity?: number;
}

export interface MessageMetadata {
  response_type?: 'qa_match' | 'clarify' | 'rag' | 'mock';
  intent?: string;
  /** 向量相似度 [0.75,0.85) 时为「相似问题」 */
  match_label?: string | null;
  vector_similarity?: number | null;
  citations?: Citation[];
  /** 前端乐观 UI：助手回复生成中 */
  pending?: boolean;
}

export interface Message {
  id: number;
  role: MessageRole;
  content: string;
  metadata?: MessageMetadata | null;
  created_at: string;
}

export interface Conversation {
  id: number;
  title: string;
  status: ConversationStatus;
  created_at: string;
  updated_at: string;
  messages: Message[];
}
