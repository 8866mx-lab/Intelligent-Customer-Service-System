import { useCallback, useEffect, useRef, useState } from 'react';
import { Button, Input, Select, Tag, message } from 'antd';
import { ChatBubble } from '@/components/chat/ChatBubble';
import { ticketService } from '@/services/ticketService';
import { wsService } from '@/services/wsService';
import type { Ticket, TicketCategory, TicketStatus } from '@/types/ticket';
import type { WsEvent } from '@/types/ws';
import type { Message } from '@/types/conversation';
import './AgentPage.css';

const { TextArea } = Input;

const categoryOptions: { value: TicketCategory; label: string }[] = [
  { value: 'it', label: 'IT' },
  { value: 'hr', label: 'HR' },
  { value: 'finance', label: '财务' },
  { value: 'admin', label: '行政' },
  { value: 'other', label: '其他' },
];

const categoryLabel: Record<TicketCategory, string> = {
  it: 'IT',
  hr: 'HR',
  finance: '财务',
  admin: '行政',
  other: '其他',
};

const statusTag: Record<TicketStatus, { label: string; color: 'default' | 'processing' | 'success' }> = {
  pending: { label: '待处理', color: 'default' },
  processing: { label: '处理中', color: 'processing' },
  completed: { label: '已完成', color: 'success' },
};

function messageLabel(msg: Message, userName: string): string | undefined {
  if (msg.role === 'user') return `${userName}（员工）`;
  if (msg.role === 'assistant') return '智能助手（历史）';
  if (msg.role === 'agent') return '坐席（我）';
  return undefined;
}

export const AgentPage: React.FC = () => {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [reply, setReply] = useState('');
  const [sending, setSending] = useState(false);
  const [suggestions, setSuggestions] = useState<{ index: number; content: string }[]>([]);
  const [showSuggest, setShowSuggest] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const active = tickets.find((t) => t.id === activeId) ?? null;

  const loadTicketDetail = useCallback(async (id: number) => {
    const detail = await ticketService.get(id);
    if (detail) {
      setTickets((prev) => prev.map((t) => (t.id === id ? detail : t)));
    }
    return detail;
  }, []);

  const reload = useCallback(async () => {
    const list = await ticketService.list();
    setTickets(list);
    setActiveId((prev) => {
      const next = prev && list.some((t) => t.id === prev)
        ? prev
        : (list.find((t) => t.status === 'pending')?.id ?? list[0]?.id ?? null);
      if (next) {
        void loadTicketDetail(next);
      }
      return next;
    });
  }, [loadTicketDetail]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      const list = await ticketService.list();
      if (!mounted) return;
      setTickets(list);
      const firstId = list.find((t) => t.status === 'pending')?.id ?? list[0]?.id ?? null;
      setActiveId(firstId);
      if (firstId) {
        await loadTicketDetail(firstId);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [loadTicketDetail]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [active?.messages]);

  useEffect(() => {
    wsService.connect();

    const appendMessage = (conversationId: number, msg: Message) => {
      setTickets((prev) =>
        prev.map((t) => {
          if (t.conversation_id !== conversationId) return t;
          if (t.messages.some((m) => m.id === msg.id)) return t;
          return { ...t, messages: [...t.messages, msg] };
        })
      );
    };

    const handleWsEvent = (event: WsEvent) => {
      if (event.event === 'ticket_created') {
        void reload();
        return;
      }

      if (event.event === 'ticket_status_changed') {
        const { ticket_id, status, conversation_id, conversation_status } = event.data;
        setTickets((prev) =>
          prev.map((t) =>
            t.id === ticket_id
              ? { ...t, status, conversation_id }
              : t
          )
        );
        if (conversation_status === 'processing' || conversation_status === 'completed') {
          void loadTicketDetail(ticket_id);
        }
        return;
      }

      if (event.event === 'new_message') {
        const { conversation_id, message } = event.data;
        appendMessage(conversation_id, message);
      }
    };

    const unsubscribe = wsService.subscribe(handleWsEvent);
    return () => {
      unsubscribe();
    };
  }, [loadTicketDetail, reload]);

  const grouped = {
    pending: tickets.filter((t) => t.status === 'pending'),
    processing: tickets.filter((t) => t.status === 'processing'),
    completed: tickets.filter((t) => t.status === 'completed'),
  };

  const handleAccept = async () => {
    if (!activeId) return;
    try {
      const updated = await ticketService.accept(activeId);
      if (!updated) {
        message.error('接单失败');
        return;
      }
      setTickets((prev) => prev.map((t) => (t.id === activeId ? updated : t)));
      await reload();
      message.success('已接单');
    } catch (error: unknown) {
      message.error(error instanceof Error ? error.message : '接单失败');
    }
  };

  const handleSend = async () => {
    const text = reply.trim();
    if (!text || !activeId) return;
    setSending(true);
    try {
      const updated = await ticketService.sendMessage(activeId, text);
      if (updated) {
        setTickets((prev) => prev.map((t) => (t.id === activeId ? updated : t)));
      } else {
        await reload();
      }
      setReply('');
      setShowSuggest(false);
    } catch (error: unknown) {
      message.error(error instanceof Error ? error.message : '发送失败，请稍后重试');
    } finally {
      setSending(false);
    }
  };

  const handleSuggest = async () => {
    if (!activeId) return;
    try {
      const items = await ticketService.suggest(activeId);
      setSuggestions(items);
      setShowSuggest(true);
    } catch (error: unknown) {
      message.error(error instanceof Error ? error.message : '智能回复生成失败');
    }
  };

  const handleCategory = async (category: TicketCategory) => {
    if (!activeId) return;
    try {
      const updated = await ticketService.updateCategory(activeId, category);
      if (updated) {
        setTickets((prev) => prev.map((t) => (t.id === activeId ? updated : t)));
      } else {
        await reload();
      }
      message.success('已保存分类');
    } catch (error: unknown) {
      message.error(error instanceof Error ? error.message : '保存分类失败');
    }
  };

  const handleComplete = async () => {
    if (!activeId) return;
    try {
      const updated = await ticketService.complete(activeId);
      if (updated) {
        setTickets((prev) => prev.map((t) => (t.id === activeId ? updated : t)));
      } else {
        await reload();
      }
      setReply('');
      setShowSuggest(false);
      message.success('工单已结束');
    } catch (error: unknown) {
      message.error(error instanceof Error ? error.message : '结束工单失败');
    }
  };

  const renderTicketItem = (t: Ticket) => (
    <button
      key={t.id}
      type="button"
      className={`ticket-item${t.id === activeId ? ' active' : ''}`}
      onClick={() => {
        setActiveId(t.id);
        setReply('');
        setShowSuggest(false);
        void loadTicketDetail(t.id);
      }}
    >
      <div className="ticket-title">
        #{t.id} · {t.user_name}
        {t.category ? (
          <Tag bordered={false} className="ticket-cat-tag">
            {categoryLabel[t.category]}
          </Tag>
        ) : null}
      </div>
      <div className="ticket-meta">
        <span className="ticket-summary">{t.summary}</span>
        <Tag color={statusTag[t.status].color} bordered={false}>
          {statusTag[t.status].label}
        </Tag>
      </div>
    </button>
  );

  const renderInputArea = () => {
    if (!active) return null;
    if (active.status === 'pending') {
      return <div className="chat-disabled">请先点击「接单」开始处理此工单</div>;
    }
    if (active.status === 'completed') {
      return <div className="chat-disabled">该工单已结束</div>;
    }
    return (
      <>
        <TextArea
          value={reply}
          onChange={(e) => setReply(e.target.value)}
          placeholder="输入回复内容…"
          autoSize={{ minRows: 2, maxRows: 4 }}
        />
        <div className="agent-toolbar">
          <Button onClick={() => void handleSuggest()}>智能回复</Button>
          <Select
            placeholder="选择归类"
            style={{ width: 120 }}
            value={active.category ?? undefined}
            onChange={(v) => void handleCategory(v)}
            options={categoryOptions}
          />
          <Button onClick={() => void handleComplete()}>结束工单</Button>
          <Button type="primary" loading={sending} onClick={() => void handleSend()}>
            发送
          </Button>
        </div>
        {showSuggest && suggestions.length > 0 && (
          <div className="suggest-panel">
            <div className="suggest-title">智能回复候选（点击填入输入框）</div>
            {suggestions.map((s) => (
              <button
                key={s.index}
                type="button"
                className="suggest-item"
                onClick={() => {
                  setReply(s.content);
                  setShowSuggest(false);
                }}
              >
                {s.index}. {s.content}
              </button>
            ))}
          </div>
        )}
      </>
    );
  };

  return (
    <div className="agent-page">
      <aside className="agent-sidebar">
        <div className="ticket-group-title">待处理 ({grouped.pending.length})</div>
        <div className="ticket-list">{grouped.pending.map(renderTicketItem)}</div>

        <div className="ticket-group-title">处理中 ({grouped.processing.length})</div>
        <div className="ticket-list">{grouped.processing.map(renderTicketItem)}</div>

        <div className="ticket-group-title">已完成</div>
        <div className="ticket-list">{grouped.completed.map(renderTicketItem)}</div>
      </aside>

      <main className="agent-main">
        <div className="chat-header agent-chat-header">
          {active ? (
            <>
              <span>
                工单 #{active.id} · {active.user_name}
                {active.category ? ` · ${categoryLabel[active.category]}` : ''}
              </span>
              <Tag color={statusTag[active.status].color}>{statusTag[active.status].label}</Tag>
              {active.status === 'pending' && (
                <Button type="primary" size="small" onClick={() => void handleAccept()}>
                  接单
                </Button>
              )}
            </>
          ) : (
            '请选择工单'
          )}
        </div>

        <div className="chat-messages">
          {active?.messages.map((m) => (
            <ChatBubble
              key={m.id}
              message={m}
              label={messageLabel(m, active.user_name)}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area agent-input-area">{renderInputArea()}</div>
      </main>
    </div>
  );
};
