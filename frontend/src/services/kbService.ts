import axios from 'axios';
import type { KbFile } from '@/types/kb';
import { cloneKbFiles, uploadKbFile, completeKbUpload, deleteKbFile } from '@/mocks/kb';

const useMock = import.meta.env.VITE_USE_MOCK === 'true';
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';

export const kbService = {
  async list(): Promise<KbFile[]> {
    if (useMock) return cloneKbFiles();

    const token = localStorage.getItem('token');
    const response = await axios.get<{ code: number; data: { items: KbFile[] } }>(
      `${apiBaseUrl}/kb/files`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    return response.data.data.items;
  },

  async get(id: number): Promise<KbFile | undefined> {
    if (useMock) return cloneKbFiles().find((f) => f.id === id);

    const token = localStorage.getItem('token');
    try {
      const response = await axios.get<{ code: number; data: KbFile }>(
        `${apiBaseUrl}/kb/files/${id}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      return response.data.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return undefined;
      }
      throw error;
    }
  },

  async upload(file: File): Promise<KbFile> {
    if (!file.name.toLowerCase().endsWith('.md')) {
      throw new Error('仅支持 .md 格式文件');
    }

    if (useMock) {
      const created = uploadKbFile(file.name);
      setTimeout(() => completeKbUpload(created.id), 2000);
      return created;
    }

    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post<{ code: number; data: KbFile }>(
      `${apiBaseUrl}/kb/upload`,
      formData,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data.data;
  },

  async getChunk(
    fileId: number,
    chunkIndex: number
  ): Promise<{ file_id: number; filename: string; chunk_index: number; content: string } | undefined> {
    if (useMock) {
      return {
        file_id: fileId,
        filename: `mock-${fileId}.md`,
        chunk_index: chunkIndex,
        content: '（Mock 模式）切块原文占位内容。',
      };
    }

    const token = localStorage.getItem('token');
    try {
      const response = await axios.get<{
        code: number;
        data: { file_id: number; filename: string; chunk_index: number; content: string };
      }>(`${apiBaseUrl}/kb/files/${fileId}/chunks/${chunkIndex}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.status === 404) {
        return undefined;
      }
      throw error;
    }
  },

  async remove(id: number): Promise<void> {
    if (useMock) {
      if (!deleteKbFile(id)) throw new Error('文件不存在');
      return;
    }

    const token = localStorage.getItem('token');
    await axios.delete(`${apiBaseUrl}/kb/files/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },
};
