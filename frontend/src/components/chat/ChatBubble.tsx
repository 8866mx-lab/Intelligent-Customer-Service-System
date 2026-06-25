import { Tag } from 'antd';
import type { Message } from '@/types/conversation';
import { CitationCard } from './CitationCard';
import './chat.css';

const roleLabel: Record<Message['role'], string> = {
  user: '我',
  assistant: '智能助手',
  agent: '坐席',
  system: '系统',
};

interface ChatBubbleProps {
  message: Message;
  /** 坐席端等场景覆盖默认角色标签 */
  label?: string;
  /** 助手回复生成中 */
  loading?: boolean;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ message, label, loading }) => {
  const isLoading = loading ?? message.metadata?.pending === true;
  if (message.role === 'system') {
    return (
      <div className="message-row system">
        <div className="message-bubble system-bubble">{message.content}</div>
      </div>
    );
  }

  return (
    <div className={`message-row ${message.role}`}>
      <span className="message-label">{label ?? roleLabel[message.role]}</span>
      <div className="message-bubble">
        {isLoading ? (
          <div className="typing-indicator" aria-label="正在生成回复">
            <span />
            <span />
            <span />
          </div>
        ) : (
          <>
            {message.metadata?.match_label === '相似问题' && (
              <Tag color="warning" bordered={false} className="match-label-tag">
                相似问题
              </Tag>
            )}
            {message.content.split('\n').map((line, i) => (
              <span key={i}>
                {line}
                {i < message.content.split('\n').length - 1 && <br />}
              </span>
            ))}
            {message.metadata?.response_type === 'rag' &&
              message.metadata.citations?.map((c) => (
                <CitationCard key={`${c.file_id}-${c.chunk_index}`} citation={c} />
              ))}
          </>
        )}
      </div>
    </div>
  );
};
