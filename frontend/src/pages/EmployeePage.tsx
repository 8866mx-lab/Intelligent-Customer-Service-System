import { useCallback, useEffect, useRef, useState } from 'react';
import { Button, Input, Modal, Tag, message } from 'antd';
import { ChatBubble } from '@/components/chat/ChatBubble';
import { conversationService } from '@/services/conversationService';
import { wsService } from '@/services/wsService';
import type { Conversation, ConversationStatus, Message } from '@/types/conversation';
import type { WsEvent } from '@/types/ws';
import './EmployeePage.css';

const { TextArea } = Input;

const OPT_USER_MSG_ID = -1;
const OPT_ASSISTANT_MSG_ID = -2;

const statusTag: Record<
  ConversationStatus,
  { label: string; color: 'processing' | 'warning' | 'success' | 'default' }
> = {
  ai_chat: { label: 'AI对话中', color: 'processing' },
  queuing: { label: '排队中', color: 'warning' },
  processing: { label: '人工处理中', color: 'processing' },
  completed: { label: '已完成', color: 'success' },
};

function formatTime(iso: string): string {
  const d = new Date(iso);
  const today = new Date();
  if (d.toDateString() === today.toDateString()) {
    return `今天 ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
  }
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  if (d.toDateString() === yesterday.toDateString()) {
    return `昨天 ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
  }
  return `${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
}

function isSlowRequestError(error: unknown): boolean {
  if (!(error instanceof Error)) return false;
  const msg = error.message.toLowerCase();
  return msg.includes('timeout') || msg.includes('network error');
}

function findLastUserMessageIndex(messages: Message[], text: string): number {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    if (messages[i].role === 'user' && messages[i].content === text) {
      return i;
    }
  }
  return -1;
}

function hasAssistantReplyAfter(messages: Message[], userIdx: number): boolean {
  return messages.slice(userIdx + 1).some((m) => m.role === 'assistant');
}

async function recoverConversationAfterSlowSend(
  conversationId: number,
  sentText: string
): Promise<Conversation | null> {
  const maxAttempts = 40;
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    if (attempt > 0) {
      await new Promise((resolve) => setTimeout(resolve, 3000));
    }
    const detail = await conversationService.get(conversationId);
    if (!detail) continue;

    const userIdx = findLastUserMessageIndex(detail.messages, sentText);
    if (userIdx === -1) continue;

    if (hasAssistantReplyAfter(detail.messages, userIdx)) {
      return detail;
    }
  }
  return null;
}

function mergeWsMessage(messages: Message[], msg: Message): Message[] {
  if (messages.some((m) => m.id === msg.id)) return messages;

  let next = [...messages];
  if (msg.role === 'user') {
    next = next.filter(
      (m) => m.id !== OPT_USER_MSG_ID && !(m.role === 'user' && m.content === msg.content)
    );
  }
  if (msg.role === 'assistant' || msg.role === 'agent' || msg.role === 'system') {
    next = next.filter((m) => m.id !== OPT_ASSISTANT_MSG_ID);
  }
  return [...next, msg];
}

export const EmployeePage: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const active = conversations.find((c) => c.id === activeId) ?? null;

  const loadConversationDetail = useCallback(async (id: number) => {
    const detail = await conversationService.get(id);
    if (detail) {
      setConversations((prev) => prev.map((c) => (c.id === id ? detail : c)));
    }
    return detail;
  }, []);

  const reload = useCallback(async () => {
    const list = await conversationService.list();
    setConversations(list);
    setActiveId((prev) => {
      const next = prev ?? list[0]?.id ?? null;
      if (next) {
        void loadConversationDetail(next);
      }
      return next;
    });
  }, [loadConversationDetail]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const list = await conversationService.list();
        if (!mounted) return;
        setConversations(list);
        const firstId = list[0]?.id ?? null;
        setActiveId(firstId);
        if (firstId) {
          await loadConversationDetail(firstId);
        }
      } catch (error: unknown) {
        if (!mounted) return;
        message.error(
          error instanceof Error ? error.message : '加载会话列表失败，请确认后端已启动'
        );
      }
    })();
    return () => {
      mounted = false;
    };
  }, [loadConversationDetail]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [active?.messages]);

  useEffect(() => {
    wsService.connect();

    const appendMessage = (conversationId: number, msg: Message) => {
      setConversations((prev) =>
        prev.map((c) => {
          if (c.id !== conversationId) return c;
          return { ...c, messages: mergeWsMessage(c.messages, msg) };
        })
      );
    };

    const handleWsEvent = (event: WsEvent) => {
      if (event.event === 'new_message') {
        const { conversation_id, message } = event.data;
        appendMessage(conversation_id, message);
        return;
      }

      if (event.event === 'ticket_status_changed') {
        const { conversation_id, conversation_status } = event.data;
        setConversations((prev) =>
          prev.map((c) =>
            c.id === conversation_id ? { ...c, status: conversation_status } : c
          )
        );
      }
    };

    const unsubscribe = wsService.subscribe(handleWsEvent);
    return () => {
      unsubscribe();
    };
  }, []);

  const handleNewSession = async () => {
    try {
      const c = await conversationService.create();
      await reload();
      setActiveId(c.id);
      message.success('已创建新对话');
    } catch (error: unknown) {
      const msg =
        error instanceof Error ? error.message : '创建会话失败，请稍后重试';
      message.error(msg);
    }
  };

  const handleSelect = async (id: number) => {
    setActiveId(id);
    setInput('');
    await loadConversationDetail(id);
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;

    let conversationId = activeId;
    let conversation = active;

    if (!conversationId || !conversation) {
      try {
        const title = text.length > 20 ? `${text.slice(0, 20)}…` : text;
        const created = await conversationService.create(title);
        setConversations((prev) => [created, ...prev]);
        setActiveId(created.id);
        conversationId = created.id;
        conversation = created;
      } catch (error: unknown) {
        message.error(error instanceof Error ? error.message : '创建会话失败，请稍后重试');
        return;
      }
    }

    if (conversation.status === 'completed') {
      message.warning('该会话已结束，不可继续发送');
      return;
    }

    const priorMessages = conversation.messages.filter((m) => m.id > 0);
    const now = new Date().toISOString();
    const optimisticUser: Message = {
      id: OPT_USER_MSG_ID,
      role: 'user',
      content: text,
      created_at: now,
    };
    const optimisticAssistant: Message = {
      id: OPT_ASSISTANT_MSG_ID,
      role: 'assistant',
      content: '',
      metadata: { pending: true },
      created_at: now,
    };

    setInput('');
    setSending(true);
    setConversations((prev) =>
      prev.map((c) =>
        c.id === conversationId
          ? { ...c, messages: [...priorMessages, optimisticUser, optimisticAssistant] }
          : c
      )
    );

    try {
      const updated = await conversationService.sendMessage(conversationId, text, {
        ...conversation,
        messages: priorMessages,
      });
      if (updated) {
        setConversations((prev) => prev.map((c) => (c.id === conversationId ? updated : c)));
      }
    } catch (error: unknown) {
      if (isSlowRequestError(error)) {
        message.warning('AI 回复生成较慢，正在后台等待，请稍候…');
        const recovered = await recoverConversationAfterSlowSend(conversationId, text);
        if (recovered) {
          setConversations((prev) => prev.map((c) => (c.id === conversationId ? recovered : c)));
          return;
        }

        const partial = await conversationService.get(conversationId);
        if (partial && findLastUserMessageIndex(partial.messages, text) !== -1) {
          setConversations((prev) => prev.map((c) => (c.id === conversationId ? partial : c)));
          message.info('您的消息已保存，AI 仍在生成回复，请稍候或刷新查看');
          return;
        }
      }

      setConversations((prev) =>
        prev.map((c) => (c.id === conversationId ? { ...c, messages: priorMessages } : c))
      );
      setInput(text);
      message.error(error instanceof Error ? error.message : '发送失败，请稍后重试');
    } finally {
      setSending(false);
    }
  };

  const handleTransfer = () => {
    if (!activeId || !active) return;
    if (active.status === 'completed') {
      message.warning('该会话已结束，不可转人工');
      return;
    }
    if (active.status !== 'ai_chat') {
      message.warning('该会话已在排队或处理中');
      return;
    }
    Modal.confirm({
      title: '转接人工客服',
      content: '确认转接人工客服？您的会话将进入排队队列。',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          const updated = await conversationService.transfer(activeId);
          if (updated) {
            setConversations((prev) =>
              prev.map((c) => (c.id === activeId ? updated : c))
            );
          } else {
            await reload();
          }
          message.success('已转入人工排队，坐席端可查看工单');
        } catch (error: unknown) {
          message.error(error instanceof Error ? error.message : '转人工失败，请稍后重试');
        }
      },
    });
  };

  const isReadOnly = active?.status === 'completed';
  const canTransfer = active?.status === 'ai_chat';

  return (
    <div className="employee-page">
      <aside className="employee-sidebar">
        <div className="sidebar-header">
          <Button type="default" block onClick={() => void handleNewSession()}>
            + 新对话
          </Button>
        </div>
        <div className="session-list">
          {conversations.map((c) => {
            const tag = statusTag[c.status];
            return (
              <button
                key={c.id}
                type="button"
                className={`session-item${c.id === activeId ? ' active' : ''}`}
                onClick={() => void handleSelect(c.id)}
              >
                <div className="session-title">{c.title}</div>
                <div className="session-meta">
                  <span>{formatTime(c.updated_at)}</span>
                  <Tag color={tag.color} bordered={false} className="session-tag">
                    {tag.label}
                  </Tag>
                </div>
              </button>
            );
          })}
        </div>
      </aside>

      <main className="employee-main">
        <div className="chat-header">{active?.title ?? '新对话（发送首条消息即可开始）'}</div>

        <div className="chat-messages">
          {active?.messages.map((m) => (
            <ChatBubble
              key={m.id}
              message={m}
              loading={m.id === OPT_ASSISTANT_MSG_ID && sending}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          {isReadOnly ? (
            <div className="chat-disabled">该会话已结束，不可继续发送消息</div>
          ) : (
            <div className="chat-input-row">
              <TextArea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="输入您的问题…"
                autoSize={{ minRows: 2, maxRows: 4 }}
                onPressEnter={(e) => {
                  if (!e.shiftKey) {
                    e.preventDefault();
                    void handleSend();
                  }
                }}
              />
              <div className="chat-actions">
                <Button disabled={!canTransfer} onClick={handleTransfer}>
                  转人工
                </Button>
                <Button type="primary" loading={sending} onClick={() => void handleSend()}>
                  发送
                </Button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
