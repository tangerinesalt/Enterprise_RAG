import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { sessionApi, kbApi } from '../api';
import type { ChatFile, KbItem } from '../api';
import MarkdownMessage from '../components/MarkdownMessage';

interface Message {
  role: string;
  content: string;
  sources?: { text: string; score: number }[];
}

export default function SessionChat() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const [sessionInfo, setSessionInfo] = useState<any>(null);
  const [chats, setChats] = useState<ChatFile[]>([]);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showBind, setShowBind] = useState(false);
  const [kbList, setKbList] = useState<KbItem[]>([]);
  const msgEndRef = useRef<HTMLDivElement>(null);

  const load = async () => {
    if (!name) return;
    try {
      const info = await sessionApi.get(name);
      setSessionInfo(info);
      if (info.kb_name) setShowBind(false);
      const c = await sessionApi.listChats(name);
      setChats(c.chats);
      if (!activeChat && c.chats.length > 0) {
        setActiveChat(c.chats[0].file);
      }
    } catch (e) { console.error(e); }
  };

  useEffect(() => { load(); }, [name]);
  useEffect(() => { msgEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  useEffect(() => {
    if (!name || !activeChat) return;
    sessionApi.getMessages(name, activeChat)
      .then(d => setMessages(d.messages.map(m => ({
        role: m.role,
        content: m.content,
        sources: m.additional_kwargs?.sources || undefined,
      }))))
      .catch(() => setMessages([]));
  }, [name, activeChat]);

  const handleBind = async (kbName: string) => {
    if (!name) return;
    await sessionApi.bind(name, kbName);
    setShowBind(false);
    load();
  };

  const handleNewChat = async () => {
    if (!name) return;
    const res = await sessionApi.newChat(name);
    setActiveChat(res.chat_file);
    setMessages([]);
    load();
  };

  const handleSubmit = async () => {
    if (!input.trim() || !name || loading) return;
    const q = input.trim();
    setInput('');
    setLoading(true);

    // Add user message + empty assistant placeholder
    setMessages(prev => [...prev, { role: 'user', content: q }, { role: 'assistant', content: '' }]);

    await sessionApi.chatStream(name, q, {
      onToken: (token) => {
        setMessages(prev => {
          const msgs = [...prev];
          const last = { ...msgs[msgs.length - 1] };
          last.content += token;
          msgs[msgs.length - 1] = last;
          return msgs;
        });
      },
      onSources: (sources) => {
        setMessages(prev => {
          const msgs = [...prev];
          const last = { ...msgs[msgs.length - 1] };
          last.sources = sources;
          msgs[msgs.length - 1] = last;
          return msgs;
        });
      },
      onDone: (chat_file) => {
        if (!activeChat) setActiveChat(chat_file);
        setLoading(false);
        load(); // refresh chat list
      },
      onError: (err) => {
        setMessages(prev => {
          const msgs = [...prev];
          const last = { ...msgs[msgs.length - 1] };
          last.content = `❌ 错误: ${err}`;
          msgs[msgs.length - 1] = last;
          return msgs;
        });
        setLoading(false);
      },
    }, activeChat || undefined);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  if (!name) return null;

  return (
    <div style={{ display: 'flex', gap: 0, height: 'calc(100vh - 80px)' }}>
      {/* 左栏 */}
      <div style={{ width: 260, minWidth: 260, borderRight: '1px solid #e5e7eb', padding: 12, overflowY: 'auto' }}>
        <button onClick={() => navigate('/session')} style={linkStyle}>← 返回</button>
        <h3 style={{ margin: '8px 0' }}>{name}</h3>

        <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 8 }}>
          KB: {sessionInfo?.kb_name || '未绑定'}
        </div>

        {sessionInfo?.kb_name ? null : (
          <button onClick={async () => {
            const list = await kbApi.list();
            setKbList(list);
            setShowBind(true);
          }} style={btnSmall}>🔗 绑定知识库</button>
        )}

        {showBind && (
          <div style={{ margin: '8px 0' }}>
            {kbList.map(kb => (
              <div key={kb.name} onClick={() => handleBind(kb.name)}
                style={{ padding: '4px 8px', cursor: 'pointer', borderRadius: 4, fontSize: 13 }}>
                📁 {kb.name}
              </div>
            ))}
          </div>
        )}

        <button onClick={handleNewChat} style={{ ...btnPrimary, width: '100%', margin: '12px 0' }}>＋ 新聊天</button>

        <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 4 }}>聊天列表</div>
        {chats.map(c => (
          <div key={c.file} style={{
            display: 'flex', alignItems: 'center', borderRadius: 4, fontSize: 13,
            background: activeChat === c.file ? '#eff6ff' : 'transparent',
            fontWeight: activeChat === c.file ? 500 : 400,
          }}>
            <div onClick={() => setActiveChat(c.file)}
              style={{ flex: 1, padding: '6px 8px', cursor: 'pointer', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {c.file}
            </div>
            <button onClick={async (e) => {
              e.stopPropagation();
              if (!confirm(`确定删除聊天「${c.file}」？`)) return;
              if (!name) return;
              await sessionApi.deleteChat(name, c.file);
              load();
              if (activeChat === c.file) {
                const remaining = chats.filter(x => x.file !== c.file);
                setActiveChat(remaining.length > 0 ? remaining[0].file : null);
                if (remaining.length === 0) setMessages([]);
              }
            }} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px 6px', fontSize: 14, color: '#9ca3af' }}
              title="删除聊天">🗑️</button>
          </div>
        ))}
      </div>

      {/* 右栏 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 12 }}>
        {activeChat ? (
          <>
            <div style={{ fontSize: 12, color: '#9ca3af', marginBottom: 8 }}>{activeChat}</div>
            <div style={{ flex: 1, overflowY: 'auto', marginBottom: 12 }}>
              {messages.map((msg, i) => (
                <div key={i} style={{ marginBottom: 16 }}>
                  <div style={{ fontWeight: 600, fontSize: 13, color: msg.role === 'user' ? '#2563eb' : '#059669', marginBottom: 4 }}>
                    {msg.role === 'user' ? '👤 用户' : '🤖 助手'}
                  </div>
                  {msg.role === 'user' ? (
                    <div style={{ fontSize: 14, lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </div>
                  ) : (
                    <div style={{ fontSize: 14, lineHeight: 1.6 }}>
                      <MarkdownMessage content={msg.content} />
                      {msg.sources && msg.sources.length > 0 && (
                        <details style={{ marginTop: 12, fontSize: 13, color: '#6b7280' }}>
                          <summary style={{ cursor: 'pointer', userSelect: 'none' }}>📎 来源 ({msg.sources.length})</summary>
                          {msg.sources.map((s, i) => (
                            <div key={i} style={{ marginTop: 8, padding: 8, background: '#f9fafb', borderRadius: 4, border: '1px solid #e5e7eb' }}>
                              <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 2 }}>相关度: {s.score ?? 'N/A'}</div>
                              <div>{s.text}</div>
                            </div>
                          ))}
                        </details>
                      )}
                    </div>
                  )}
                </div>
              ))}
              <div ref={msgEndRef} />
            </div>

            <div style={{ display: 'flex', gap: 8, borderTop: '1px solid #e5e7eb', paddingTop: 12 }}>
              <textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
                rows={2}
                style={{
                  flex: 1, padding: '8px 12px', border: '1px solid #d1d5db',
                  borderRadius: 6, fontSize: 14, resize: 'none',
                  fontFamily: 'inherit',
                }}
              />
              <button onClick={handleSubmit} disabled={loading || !input.trim()}
                style={{
                  padding: '8px 20px', background: loading ? '#93c5fd' : '#2563eb',
                  color: '#fff', border: 'none', borderRadius: 6,
                  cursor: 'pointer', fontSize: 14, alignSelf: 'flex-end',
                }}>
                {loading ? '...' : '↵ 发送'}
              </button>
            </div>
          </>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#9ca3af' }}>
            {chats.length === 0 ? '点击「新聊天」开始对话' : '选择一个聊天'}
          </div>
        )}
      </div>
    </div>
  );
}

const linkStyle: React.CSSProperties = {
  background: 'none', border: 'none', color: '#2563eb',
  cursor: 'pointer', padding: 0, fontSize: 13,
};
const btnPrimary: React.CSSProperties = {
  padding: '6px 14px', background: '#2563eb', color: '#fff',
  border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 13,
};
const btnSmall: React.CSSProperties = {
  padding: '4px 10px', background: '#e5e7eb', color: '#374151',
  border: 'none', borderRadius: 3, cursor: 'pointer', fontSize: 12,
};
