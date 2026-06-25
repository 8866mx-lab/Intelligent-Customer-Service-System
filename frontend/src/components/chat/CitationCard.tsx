import { useState } from 'react';
import { Modal, Spin, message } from 'antd';
import { kbService } from '@/services/kbService';
import type { Citation } from '@/types/conversation';
import './chat.css';

interface CitationCardProps {
  citation: Citation;
}

export const CitationCard: React.FC<CitationCardProps> = ({ citation }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [fullContent, setFullContent] = useState<string | null>(null);

  const handleViewOriginal = async () => {
    setOpen(true);
    if (fullContent !== null) return;

    setLoading(true);
    try {
      const chunk = await kbService.getChunk(citation.file_id, citation.chunk_index);
      if (!chunk?.content) {
        message.warning('未能加载切块原文');
        setFullContent(citation.preview);
        return;
      }
      setFullContent(chunk.content);
    } catch (error: unknown) {
      message.error(error instanceof Error ? error.message : '加载原文失败');
      setFullContent(citation.preview);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="cite-card">
        <div className="cite-title">
          {citation.filename} · 第 {citation.chunk_index} 段
          {citation.similarity !== undefined && (
            <span className="cite-score">
              {' '}
              · 相关度 {(citation.similarity * 100).toFixed(0)}%
            </span>
          )}
        </div>
        <div className="cite-preview">{citation.preview}</div>
        <button type="button" className="cite-link" onClick={() => void handleViewOriginal()}>
          查看原文 →
        </button>
      </div>

      <Modal
        title={`${citation.filename} · 第 ${citation.chunk_index} 段`}
        open={open}
        onCancel={() => setOpen(false)}
        footer={null}
        width={640}
      >
        {loading ? (
          <div className="cite-modal-loading">
            <Spin />
          </div>
        ) : (
          <pre className="cite-modal-content">{fullContent ?? citation.preview}</pre>
        )}
      </Modal>
    </>
  );
};
