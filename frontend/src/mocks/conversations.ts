import type { Conversation } from '@/types/conversation';

const now = new Date();
const fmt = (d: Date) => d.toISOString();

export const mockConversations: Conversation[] = [
  {
    id: 1,
    title: '请假流程咨询',
    status: 'ai_chat',
    created_at: fmt(now),
    updated_at: fmt(now),
    messages: [
      {
        id: 1,
        role: 'assistant',
        content: '您好，我是企业内部智能助手，有什么可以帮您的？',
        metadata: null,
        created_at: fmt(now),
      },
      {
        id: 2,
        role: 'user',
        content: '请问公司的请假流程是什么？',
        metadata: null,
        created_at: fmt(now),
      },
      {
        id: 3,
        role: 'assistant',
        content:
          '根据《员工手册》规定，请假流程如下：\n\n1. 提前在 OA 系统提交请假申请\n2. 直属主管审批（1 个工作日内）\n3. 人事部门备案\n4. 年假需提前 3 个工作日申请',
        metadata: {
          response_type: 'rag',
          intent: 'clear_query',
          citations: [
            {
              file_id: 1,
              filename: '员工手册.md',
              chunk_index: 12,
              preview:
                '「员工请假应提前通过 OA 系统提交申请，经直属主管审批后生效。年假须提前 3 个工作日申请…」',
              similarity: 0.92,
            },
          ],
        },
        created_at: fmt(now),
      },
    ],
  },
  {
    id: 2,
    title: 'VPN 无法连接',
    status: 'queuing',
    created_at: fmt(new Date(now.getTime() - 3 * 3600000)),
    updated_at: fmt(new Date(now.getTime() - 2 * 3600000)),
    messages: [
      {
        id: 10,
        role: 'user',
        content: '公司的 VPN 连不上了，提示认证失败',
        metadata: null,
        created_at: fmt(now),
      },
      {
        id: 11,
        role: 'assistant',
        content: '抱歉，未能找到 VPN 认证失败的具体方案，建议您转接人工客服。',
        metadata: { response_type: 'rag', intent: 'clear_query' },
        created_at: fmt(now),
      },
      {
        id: 12,
        role: 'system',
        content: '已转人工，正在排队中…',
        metadata: null,
        created_at: fmt(now),
      },
    ],
  },
  {
    id: 3,
    title: '报销流程说明',
    status: 'completed',
    created_at: fmt(new Date(now.getTime() - 86400000)),
    updated_at: fmt(new Date(now.getTime() - 86400000)),
    messages: [
      {
        id: 20,
        role: 'user',
        content: '报销需要哪些材料？',
        metadata: null,
        created_at: fmt(now),
      },
      {
        id: 21,
        role: 'assistant',
        content: '请准备发票原件、报销单和审批邮件截图。',
        metadata: { response_type: 'rag' },
        created_at: fmt(now),
      },
    ],
  },
  {
    id: 4,
    title: '年假余额查询',
    status: 'ai_chat',
    created_at: fmt(new Date(now.getTime() - 2 * 86400000)),
    updated_at: fmt(new Date(now.getTime() - 2 * 86400000)),
    messages: [
      {
        id: 30,
        role: 'assistant',
        content: '您好，我是企业内部智能助手，有什么可以帮您的？',
        metadata: null,
        created_at: fmt(now),
      },
    ],
  },
];

let nextId = 100;
let nextMsgId = 1000;

export function cloneConversations(): Conversation[] {
  return JSON.parse(JSON.stringify(mockConversations)) as Conversation[];
}

export function createNewConversation(): Conversation {
  const c: Conversation = {
    id: nextId++,
    title: '新对话',
    status: 'ai_chat',
    created_at: fmt(new Date()),
    updated_at: fmt(new Date()),
    messages: [
      {
        id: nextMsgId++,
        role: 'assistant',
        content: '您好，我是企业内部智能助手，有什么可以帮您的？',
        metadata: null,
        created_at: fmt(new Date()),
      },
    ],
  };
  mockConversations.unshift(c);
  return JSON.parse(JSON.stringify(c)) as Conversation;
}

export function appendUserMessage(conversationId: number, content: string): Conversation | null {
  const conv = mockConversations.find((c) => c.id === conversationId);
  if (!conv || conv.status === 'completed') return null;

  conv.messages.push({
    id: nextMsgId++,
    role: 'user',
    content,
    metadata: null,
    created_at: fmt(new Date()),
  });

  conv.messages.push({
    id: nextMsgId++,
    role: 'assistant',
    content: '正在检索知识库并生成回答…（Mock 演示）',
    metadata: { response_type: 'mock' },
    created_at: fmt(new Date()),
  });
  conv.updated_at = fmt(new Date());
  return JSON.parse(JSON.stringify(conv)) as Conversation;
}

export function transferConversation(conversationId: number): Conversation | null {
  const conv = mockConversations.find((c) => c.id === conversationId);
  if (!conv || conv.status === 'completed') return null;
  conv.status = 'queuing';
  conv.messages.push({
    id: nextMsgId++,
    role: 'system',
    content: '已转人工，正在排队中…',
    metadata: null,
    created_at: fmt(new Date()),
  });
  conv.updated_at = fmt(new Date());
  return JSON.parse(JSON.stringify(conv)) as Conversation;
}
