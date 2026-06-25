import type { WsEvent } from '@/types/ws';

type WsHandler = (event: WsEvent) => void;

const useMock = import.meta.env.VITE_USE_MOCK === 'true';
const RECONNECT_MS = 3000;

class WsService {
  private ws: WebSocket | null = null;
  private handlers = new Set<WsHandler>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private intentionalClose = false;

  connect(): void {
    if (useMock) return;

    const token = localStorage.getItem('token');
    if (!token) return;

    if (this.ws?.readyState === WebSocket.OPEN || this.ws?.readyState === WebSocket.CONNECTING) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/ws/messages?token=${encodeURIComponent(token)}`;

    this.intentionalClose = false;
    const socket = new WebSocket(url);
    this.ws = socket;

    socket.onopen = () => {
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
      }
    };

    socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data as string) as WsEvent;
        this.handlers.forEach((handler) => handler(payload));
      } catch {
        // ignore malformed payloads
      }
    };

    socket.onclose = () => {
      if (this.ws === socket) {
        this.ws = null;
      }
      if (!this.intentionalClose) {
        this.scheduleReconnect();
      }
    };
  }

  disconnect(): void {
    this.intentionalClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
  }

  subscribe(handler: WsHandler): () => void {
    this.handlers.add(handler);
    return () => {
      this.handlers.delete(handler);
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer || useMock) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, RECONNECT_MS);
  }
}

export const wsService = new WsService();
