export type KbFileStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type StoreStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface KbStores {
  vector: StoreStatus;
  keyword: StoreStatus;
  metadata: StoreStatus;
  qa: StoreStatus;
}

export interface KbFile {
  id: number;
  filename: string;
  status: KbFileStatus;
  chunk_count: number | null;
  qa_count: number | null;
  stores: KbStores;
  error_message: string | null;
  uploaded_by: number;
  created_at: string;
  updated_at: string;
}
