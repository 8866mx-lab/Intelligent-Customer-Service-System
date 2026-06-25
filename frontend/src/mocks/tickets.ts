import type { Ticket, SuggestItem } from '@/types/ticket';

const fmt = (d: Date) => d.toISOString();
const now = new Date();

export const mockTickets: Ticket[] = [
  {
    id: 1024,
    conversation_id: 2,
    user_id: 2,
    user_name: '李四',
    agent_id: null,
    category: null,
    status: 'pending',
    summary: 'VPN 无法连接',
    created_at: fmt(now),
    updated_at: fmt(now),
    messages: [
      {
        id: 101,
        role: 'user',
        content: '公司的 VPN 连不上了，提示认证失败，怎么办？',
        metadata: null,
        created_at: fmt(now),
      },
      {
        id: 102,
        role: 'assistant',
        content: '抱歉，我未能从知识库中找到 VPN 认证失败的具体解决方案，建议您转接人工客服。',
        metadata: {
          response_type: 'rag',
          citations: [
            {
              file_id: 2,
              filename: 'IT指南.md',
              chunk_index: 5,
              preview: '「VPN 连接问题请联系 IT 服务台…」（相似度不足 0.8，未直答）',
            },
          ],
        },
        created_at: fmt(now),
      },
      {
        id: 103,
        role: 'user',
        content: '【已转人工】',
        metadata: null,
        created_at: fmt(now),
      },
    ],
  },
  {
    id: 1025,
    conversation_id: 5,
    user_id: 3,
    user_name: '王五',
    agent_id: null,
    category: null,
    status: 'pending',
    summary: '打印机故障',
    created_at: fmt(now),
    updated_at: fmt(now),
    messages: [
      {
        id: 110,
        role: 'user',
        content: '三楼打印机无法打印，显示离线',
        metadata: null,
        created_at: fmt(now),
      },
    ],
  },
  {
    id: 1020,
    conversation_id: 6,
    user_id: 4,
    user_name: '赵六',
    agent_id: 1,
    category: 'hr',
    status: 'processing',
    summary: '请假流程咨询',
    created_at: fmt(now),
    updated_at: fmt(now),
    messages: [
      {
        id: 120,
        role: 'user',
        content: '年假怎么申请？',
        metadata: null,
        created_at: fmt(now),
      },
      {
        id: 121,
        role: 'assistant',
        content: '请在 OA 系统提交年假申请，提前 3 个工作日。',
        metadata: { response_type: 'rag' },
        created_at: fmt(now),
      },
    ],
  },
  {
    id: 1018,
    conversation_id: 7,
    user_id: 5,
    user_name: '钱七',
    agent_id: 1,
    category: 'finance',
    status: 'completed',
    summary: '报销流程说明',
    created_at: fmt(new Date(now.getTime() - 86400000)),
    updated_at: fmt(new Date(now.getTime() - 86400000)),
    messages: [
      {
        id: 130,
        role: 'user',
        content: '报销需要哪些材料？',
        metadata: null,
        created_at: fmt(now),
      },
      {
        id: 131,
        role: 'agent',
        content: '请准备发票原件和报销单。',
        metadata: null,
        created_at: fmt(now),
      },
    ],
  },
  {
    id: 1015,
    conversation_id: 8,
    user_id: 6,
    user_name: '孙八',
    agent_id: 1,
    category: 'admin',
    status: 'completed',
    summary: '会议室预订',
    created_at: fmt(new Date(now.getTime() - 2 * 86400000)),
    updated_at: fmt(new Date(now.getTime() - 2 * 86400000)),
    messages: [
      {
        id: 140,
        role: 'user',
        content: '如何预订会议室？',
        metadata: null,
        created_at: fmt(now),
      },
    ],
  },
];

const mockSuggestions: SuggestItem[] = [
  {
    index: 1,
    content: '您好，VPN 认证失败通常是密码过期导致，请尝试在 OA 系统重置密码后重新连接。',
  },
  {
    index: 2,
    content: '请确认您使用的是公司分配的 VPN 客户端（版本 3.2+），旧版本可能导致认证失败。',
  },
  {
    index: 3,
    content: '如仍无法连接，请提供错误截图，我帮您进一步排查。也可拨打 IT 热线 8888。',
  },
];

export function cloneTickets(): Ticket[] {
  return JSON.parse(JSON.stringify(mockTickets)) as Ticket[];
}

export function acceptTicket(ticketId: number): Ticket | null {
  const t = mockTickets.find((x) => x.id === ticketId);
  if (!t || t.status !== 'pending') return null;
  t.status = 'processing';
  t.agent_id = 1;
  t.updated_at = fmt(new Date());
  return JSON.parse(JSON.stringify(t)) as Ticket;
}

export function sendAgentMessage(ticketId: number, content: string): Ticket | null {
  const t = mockTickets.find((x) => x.id === ticketId);
  if (!t || t.status !== 'processing') return null;
  t.messages.push({
    id: Date.now(),
    role: 'agent',
    content,
    metadata: null,
    created_at: fmt(new Date()),
  });
  t.updated_at = fmt(new Date());
  return JSON.parse(JSON.stringify(t)) as Ticket;
}

export function updateTicketCategory(ticketId: number, category: Ticket['category']): Ticket | null {
  const t = mockTickets.find((x) => x.id === ticketId);
  if (!t) return null;
  t.category = category;
  t.updated_at = fmt(new Date());
  return JSON.parse(JSON.stringify(t)) as Ticket;
}

export function completeTicket(ticketId: number): Ticket | null {
  const t = mockTickets.find((x) => x.id === ticketId);
  if (!t || t.status !== 'processing') return null;
  t.status = 'completed';
  t.updated_at = fmt(new Date());
  return JSON.parse(JSON.stringify(t)) as Ticket;
}

export function getSuggestions(): SuggestItem[] {
  return [...mockSuggestions];
}
