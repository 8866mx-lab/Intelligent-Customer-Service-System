import { useCallback, useEffect, useState } from 'react';
import { Upload, Table, Tag, Button, Modal, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { kbService } from '@/services/kbService';
import type { KbFile, KbFileStatus, StoreStatus } from '@/types/kb';
import './KnowledgePage.css';

const storeLabel: Record<StoreStatus, string> = {
  pending: '等待中',
  processing: '处理中',
  completed: '已入库',
  failed: '失败',
};

const storeColor: Record<StoreStatus, string> = {
  pending: 'default',
  processing: 'processing',
  completed: 'success',
  failed: 'error',
};

const fileStatusColor: Record<KbFileStatus, string> = {
  pending: 'default',
  processing: 'warning',
  completed: 'success',
  failed: 'error',
};

const fileStatusLabel: Record<KbFileStatus, string> = {
  pending: '待处理',
  processing: '处理中',
  completed: '已完成',
  failed: '失败',
};

const FALLBACK_ERROR_MESSAGE =
  '入库失败，未记录详细原因。请删除该文件后重新上传；若持续失败请检查 DashScope API 配置与网络连接。';

function resolveErrorMessage(errorMessage: string | null | undefined): string {
  const text = errorMessage?.trim();
  return text || FALLBACK_ERROR_MESSAGE;
}

export const KnowledgePage: React.FC = () => {
  const [files, setFiles] = useState<KbFile[]>([]);
  const [loading, setLoading] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      setFiles(await kbService.list());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    const fetchList = async () => {
      const list = await kbService.list();
      if (mounted) setFiles(list);
    };
    void fetchList();
    const timer = window.setInterval(() => void fetchList(), 2500);
    return () => {
      mounted = false;
      window.clearInterval(timer);
    };
  }, []);

  const showDetail = async (file: KbFile) => {
    let detail = file;
    if (file.status === 'failed' && !file.error_message?.trim()) {
      const fetched = await kbService.get(file.id);
      if (fetched) detail = fetched;
    }

    Modal.info({
      title: `入库详情：${detail.filename}`,
      width: 480,
      content: (
        <div className="kb-detail">
          <p>切块数：{detail.chunk_count ?? '—'}</p>
          <p>QA 抽取数：{detail.qa_count ?? '—'}</p>
          <p>向量库：{storeLabel[detail.stores.vector]}</p>
          <p>关键词库：{storeLabel[detail.stores.keyword]}</p>
          <p>Metadata 库：{storeLabel[detail.stores.metadata]}</p>
          <p>QA 库：{storeLabel[detail.stores.qa]}</p>
          {detail.status === 'failed' && (
            <p className="kb-error">错误：{resolveErrorMessage(detail.error_message)}</p>
          )}
        </div>
      ),
    });
  };

  const showError = async (file: KbFile) => {
    let detail = file;
    if (!file.error_message?.trim()) {
      const fetched = await kbService.get(file.id);
      if (fetched) detail = fetched;
    }

    Modal.error({
      title: `入库失败：${detail.filename}`,
      width: 520,
      content: <p className="kb-error">{resolveErrorMessage(detail.error_message)}</p>,
    });
  };

  const handleDelete = (file: KbFile) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定删除「${file.filename}」及其索引数据？`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        await kbService.remove(file.id);
        await reload();
        message.success('已删除');
      },
    });
  };

  const uploadProps: UploadProps = {
    accept: '.md',
    showUploadList: false,
    multiple: false,
    beforeUpload: (file) => {
      if (!file.name.toLowerCase().endsWith('.md')) {
        message.error('仅支持 .md 格式文件');
        return Upload.LIST_IGNORE;
      }
      void (async () => {
        try {
          await kbService.upload(file);
          message.success('上传成功，正在入库…');
          await reload();
        } catch (e) {
          message.error(e instanceof Error ? e.message : '上传失败');
        }
      })();
      return false;
    },
  };

  const renderStore = (status: StoreStatus) => (
    <Tag color={storeColor[status]} bordered={false}>
      {storeLabel[status]}
    </Tag>
  );

  const columns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      render: (text: string) => <strong>{text}</strong>,
    },
    {
      title: '上传时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (v: string) => new Date(v).toLocaleString('zh-CN'),
    },
    { title: '切块数', dataIndex: 'chunk_count', key: 'chunk_count', render: (v: number | null) => v ?? '—' },
    { title: 'QA 数', dataIndex: 'qa_count', key: 'qa_count', render: (v: number | null) => v ?? '—' },
    {
      title: '向量库',
      key: 'vector',
      render: (_: unknown, r: KbFile) => renderStore(r.stores.vector),
    },
    {
      title: '关键词库',
      key: 'keyword',
      render: (_: unknown, r: KbFile) => renderStore(r.stores.keyword),
    },
    {
      title: 'Metadata',
      key: 'metadata',
      render: (_: unknown, r: KbFile) => renderStore(r.stores.metadata),
    },
    {
      title: 'QA 库',
      key: 'qa',
      render: (_: unknown, r: KbFile) => renderStore(r.stores.qa),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (s: KbFileStatus) => (
        <Tag color={fileStatusColor[s]} bordered={false}>
          {fileStatusLabel[s]}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: unknown, r: KbFile) => (
        <span className="kb-actions">
          <Button type="link" size="small" onClick={() => void showDetail(r)}>
            详情
          </Button>
          {r.status === 'failed' && (
            <Button type="link" size="small" onClick={() => void showError(r)}>
              查看错误
            </Button>
          )}
          {r.status === 'completed' && (
            <Button type="link" size="small" danger onClick={() => handleDelete(r)}>
              删除
            </Button>
          )}
        </span>
      ),
    },
  ];

  return (
    <div className="knowledge-page">
      <h1 className="kb-title">知识库管理</h1>

      <Upload.Dragger {...uploadProps} className="kb-upload">
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">
          点击或拖拽 <strong>.md</strong> 文件到此区域上传
        </p>
        <p className="ant-upload-hint">仅支持 Markdown 格式，单文件上传</p>
      </Upload.Dragger>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={files}
        loading={loading}
        pagination={false}
        scroll={{ x: 1100 }}
        className="kb-table"
      />
    </div>
  );
};
