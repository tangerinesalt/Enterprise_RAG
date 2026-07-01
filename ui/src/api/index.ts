const BASE = '/api';
const API_DEBUG = import.meta.env.VITE_API_DEBUG === 'true';

function logApiSuccess(method: string, url: string, elapsed: number) {
  if (!API_DEBUG) return;
  const msg = `[API] ${method} ${url} -> ${elapsed.toFixed(0)}ms`;
  if (elapsed > 1000) console.warn(`[API][SLOW] ${msg}`);
  else console.log(msg);
}

function logApiError(method: string, url: string, elapsed: number, error: unknown) {
  console.error(`[API][ERROR] ${method} ${url} -> ${elapsed.toFixed(0)}ms`, error);
}

async function req<T>(url: string, options?: RequestInit): Promise<T> {
  const t0 = performance.now();
  const method = options?.method || 'GET';
  try {
    const res = await fetch(`${BASE}${url}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    const elapsed = performance.now() - t0;
    logApiSuccess(method, url, elapsed);
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || 'Unknown error');
    return data.data as T;
  } catch (e) {
    const elapsed = performance.now() - t0;
    logApiError(method, url, elapsed, e);
    throw e;
  }
}

export interface KbItem {
  name: string;
  files: number;
  folders: number;
}

export interface FileItem {
  name: string;
  size: number;
  size_str: string;
  type: 'file' | 'folder';
}

export const kbApi = {
  list: () => req<KbItem[]>('/kb'),
  create: (name: string) => req<{ name: string }>('/kb', {
    method: 'POST', body: JSON.stringify({ name }),
  }),
  get: (name: string) => req<{ name: string; files: FileItem[] }>(`/kb/${name}`),
  delete: (name: string) => req<{ name: string }>(`/kb/${name}`, { method: 'DELETE' }),
  upload: async (name: string, files: File[]) => {
    const t0 = performance.now();
    const url = '/kb/upload';
    const form = new FormData();
    form.append('name', name);
    files.forEach(f => form.append('files', f));
    try {
      const res = await fetch(`${BASE}${url}`, { method: 'POST', body: form });
      const elapsed = performance.now() - t0;
      logApiSuccess('POST', url, elapsed);
      const data = await res.json();
      if (!data.ok) throw new Error(data.error);
      return data.data;
    } catch (e) {
      const elapsed = performance.now() - t0;
      logApiError('POST', url, elapsed, e);
      throw e;
    }
  },
  index: (name: string, target: string) => req<{ indexed: number }>('/kb/index', {
    method: 'POST', body: JSON.stringify({ name, target }),
  }),
  indexAll: (name: string) => req<{ indexed: number }>('/kb/index', {
    method: 'POST', body: JSON.stringify({ name, all: true }),
  }),
  deleteFile: (name: string, target: string) => req(`/kb/${name}/files?filename=${encodeURIComponent(target)}`, {
    method: 'DELETE',
  }),
};

export interface SessionItem {
  name: string;
  kb_name: string | null;
  active_chat: string | null;
  top_k?: number;
  top_n?: number;
  system_prompt?: string;
  total_chats: number;
}

export interface ChatFile {
  file: string;
  is_active: boolean;
}

export interface SourceItem {
  text: string;
  score: number;
}

export const sessionApi = {
  list: () => req<SessionItem[]>('/session'),
  create: (name: string) => req<{ name: string }>('/session', {
    method: 'POST', body: JSON.stringify({ name }),
  }),
  get: (name: string) => req<SessionItem>(`/session/${name}`),
  delete: (name: string) => req<{ name: string }>(`/session/${name}`, { method: 'DELETE' }),
  bind: (name: string, kb_name: string) => req<{ name: string; kb_name: string }>('/session/bind', {
    method: 'POST', body: JSON.stringify({ name, kb_name }),
  }),
  newChat: (name: string) => req<{ name: string; chat_file: string }>('/session/new', {
    method: 'POST', body: JSON.stringify({ name }),
  }),
  selectChat: (name: string, chat_file: string) => req('/session/select', {
    method: 'POST', body: JSON.stringify({ name, chat_file }),
  }),
  chat: (name: string, query: string, chat_file?: string) =>
    req<{ answer: string; sources: SourceItem[]; chat_file: string }>('/session/chat', {
      method: 'POST', body: JSON.stringify({ name, query, chat_file }),
    }),
  chatStream: (
    name: string,
    query: string,
    callbacks: {
      onToken?: (token: string) => void;
      onSources?: (sources: SourceItem[]) => void;
      onDone?: (chat_file: string) => void;
      onError?: (error: string) => void;
    },
    chat_file?: string,
  ): Promise<void> => {
    const { onToken, onSources, onDone, onError } = callbacks;
    const t0 = performance.now();
    const url = '/session/chat/stream';
    return fetch(`${BASE}${url}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, query, chat_file }),
    }).then(async (res) => {
      if (!res.ok) {
        const text = await res.text();
        const message = `HTTP ${res.status}: ${text}`;
        logApiError('POST', url, performance.now() - t0, message);
        onError?.(message);
        return;
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buf = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buf += decoder.decode(value, { stream: true });

        let sepIdx: number;
        while ((sepIdx = buf.indexOf('\n\n')) !== -1) {
          const block = buf.slice(0, sepIdx);
          buf = buf.slice(sepIdx + 2);

          let eventType = '';
          let dataStr = '';
          for (const line of block.split('\n')) {
            if (line.startsWith('event: ')) eventType = line.slice(7);
            else if (line.startsWith('data: ')) dataStr = line.slice(6);
          }
          if (!dataStr) continue;

          try {
            const data = JSON.parse(dataStr);
            if (eventType === 'token') onToken?.(data.token);
            else if (eventType === 'sources') onSources?.(data.sources);
            else if (eventType === 'done') onDone?.(data.chat_file);
            else if (eventType === 'error') onError?.(data.message);
          } catch {
            // Ignore malformed SSE data blocks.
          }
        }
      }

      logApiSuccess('POST', url, performance.now() - t0);
    }).catch((err) => {
      logApiError('POST', url, performance.now() - t0, err);
      onError?.(String(err));
    });
  },
  deleteChat: (name: string, chatFile: string) =>
    req<{ name: string; chat_file: string }>(`/session/${name}/chats/${chatFile}`, { method: 'DELETE' }),
  listChats: (name: string) => req<{ name: string; chats: ChatFile[] }>(`/session/${name}/chats`),
  getMessages: (name: string, chatFile: string) =>
    req<{
      name: string;
      chat_file: string;
      messages: {
        role: string;
        content: string;
        additional_kwargs?: { sources?: SourceItem[] };
      }[];
    }>(`/session/${name}/chats/${chatFile}`),
  updateConfig: (name: string, data: { top_k?: number; top_n?: number; system_prompt?: string }) =>
    req<{ top_k: number; top_n: number; system_prompt?: string }>(`/session/${name}/config`, {
      method: 'PATCH', body: JSON.stringify(data),
    }),
};
