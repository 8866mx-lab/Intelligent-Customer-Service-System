import type { KbFile } from '@/types/kb';

const fmt = (d: Date) => d.toISOString();
const now = new Date();

export const mockKbFiles: KbFile[] = [
  {
    id: 1,
    filename: '员工手册.md',
    status: 'completed',
    chunk_count: 42,
    qa_count: 15,
    stores: {
      vector: 'completed',
      keyword: 'completed',
      metadata: 'completed',
      qa: 'completed',
    },
    error_message: null,
    uploaded_by: 1,
    created_at: fmt(now),
    updated_at: fmt(now),
  },
  {
    id: 2,
    filename: 'IT指南.md',
    status: 'processing',
    chunk_count: null,
    qa_count: null,
    stores: {
      vector: 'processing',
      keyword: 'processing',
      metadata: 'processing',
      qa: 'pending',
    },
    error_message: null,
    uploaded_by: 1,
    created_at: fmt(new Date(now.getTime() - 3600000)),
    updated_at: fmt(new Date(now.getTime() - 3600000)),
  },
  {
    id: 3,
    filename: '财务报销规范.md',
    status: 'completed',
    chunk_count: 35,
    qa_count: 12,
    stores: {
      vector: 'completed',
      keyword: 'completed',
      metadata: 'completed',
      qa: 'completed',
    },
    error_message: null,
    uploaded_by: 1,
    created_at: fmt(new Date(now.getTime() - 86400000)),
    updated_at: fmt(new Date(now.getTime() - 86400000)),
  },
  {
    id: 4,
    filename: '行政管理制度.md',
    status: 'failed',
    chunk_count: null,
    qa_count: null,
    stores: {
      vector: 'pending',
      keyword: 'pending',
      metadata: 'pending',
      qa: 'pending',
    },
    error_message: '文件编码不支持，请使用 UTF-8 编码的 .md 文件',
    uploaded_by: 1,
    created_at: fmt(new Date(now.getTime() - 2 * 86400000)),
    updated_at: fmt(new Date(now.getTime() - 2 * 86400000)),
  },
];

let nextId = 10;

export function cloneKbFiles(): KbFile[] {
  return JSON.parse(JSON.stringify(mockKbFiles)) as KbFile[];
}

export function uploadKbFile(filename: string): KbFile {
  const file: KbFile = {
    id: nextId++,
    filename,
    status: 'processing',
    chunk_count: null,
    qa_count: null,
    stores: {
      vector: 'processing',
      keyword: 'pending',
      metadata: 'pending',
      qa: 'pending',
    },
    error_message: null,
    uploaded_by: 1,
    created_at: fmt(new Date()),
    updated_at: fmt(new Date()),
  };
  mockKbFiles.unshift(file);
  return JSON.parse(JSON.stringify(file)) as KbFile;
}

export function completeKbUpload(fileId: number): KbFile | null {
  const f = mockKbFiles.find((x) => x.id === fileId);
  if (!f) return null;
  f.status = 'completed';
  f.chunk_count = 18;
  f.qa_count = 6;
  f.stores = {
    vector: 'completed',
    keyword: 'completed',
    metadata: 'completed',
    qa: 'completed',
  };
  f.updated_at = fmt(new Date());
  return JSON.parse(JSON.stringify(f)) as KbFile;
}

export function deleteKbFile(fileId: number): boolean {
  const idx = mockKbFiles.findIndex((x) => x.id === fileId);
  if (idx < 0) return false;
  mockKbFiles.splice(idx, 1);
  return true;
}
