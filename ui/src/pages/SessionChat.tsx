import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { sessionApi, kbApi } from '../api';
import type { ChatFile, KbItem, SessionItem, SessionStreamError } from '../api';
import SessionSidebar from '../components/SessionSidebar';
import ChatArea from '../components/ChatArea';
import styles from './SessionChat.module.css';

interface Message {
  role: string;
  content: string;
  sources?: { text: string; score: number }[];
}

function toHistoryMessage(message: {
  role: string;
  content: string;
  additional_kwargs?: { sources?: { text: string; score: number }[] };
}): Message {
  const sources = Array.isArray(message.additional_kwargs?.sources)
    ? message.additional_kwargs.sources
    : undefined;

  return {
    role: message.role,
    content: message.content,
    // Structured persisted sources are authoritative; legacy inline text stays body-only.
    sources,
  };
}

export default function SessionChat() {
  const { name } = useParams<{ name: string }>();
  const [sessionInfo, setSessionInfo] = useState<SessionItem | null>(null);
  const [chats, setChats] = useState<ChatFile[]>([]);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showBind, setShowBind] = useState(false);
  const [kbList, setKbList] = useState<KbItem[]>([]);
  const [topK, setTopK] = useState(8);
  const [topN, setTopN] = useState(5);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [showParams, setShowParams] = useState(true);

  // AbortController ref for SSE stream cancellation
  const abortRef = useRef<AbortController | null>(null);

  const load = useCallback(async () => {
    if (!name) return;
    try {
      const info = await sessionApi.get(name);
      setSessionInfo(info);
      if (info.kb_name) setShowBind(false);
      const c = await sessionApi.listChats(name);
      setChats(c.chats);
    } catch (e) { console.error(e); }
  }, [name]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (sessionInfo) {
      setTopK(sessionInfo.top_k ?? 8);
      setTopN(sessionInfo.top_n ?? 5);
      setSystemPrompt(sessionInfo.system_prompt ?? "");
    }
  }, [sessionInfo]);

  useEffect(() => {
    // loading 时跳过：提交中会通过 onToken 填充消息，不要被空文件内容覆盖
    if (!name || !activeChat || loading) return;
    sessionApi.getMessages(name, activeChat)
      .then(d => setMessages(d.messages.map(toHistoryMessage)))
      .catch(() => setMessages([]));
  }, [name, activeChat, loading]);

  // Abort SSE on unmount
  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  const handleBind = async (kbName: string) => {
    if (!name) return;
    await sessionApi.bind(name, kbName);
    setShowBind(false);
    load();
  };

  const handleSelectChat = (chatFile: string) => {
    // Cancel any in-flight stream before switching to a different chat
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
      setLoading(false);
    }
    setMessages([]);
    setActiveChat(chatFile);
    if (!name) return;
    sessionApi.selectChat(name, chatFile).catch(console.error);
  };

  const handleNewChat = async () => {
    if (!name) return;
    try {
      const res = await sessionApi.newChat(name);
      setActiveChat(res.chat_file);
      setMessages([]);
      await load();
    } catch (e) {
      console.error(e);
      alert(`❌ 创建聊天失败\n\n${e}`);
    }
  };

  const handleSaveConfig = async () => {
    if (!name) return;
    if (topK < 1 || topN < 1) {
      setSaveStatus('error');
      return;
    }
    setSaveStatus('saving');
    try {
      await sessionApi.updateConfig(name, { top_k: topK, top_n: topN, system_prompt: systemPrompt });
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    } catch {
      setSaveStatus('error');
    }
  };

  const handleSubmit = async () => {
    if (!input.trim() || !name || loading) return;

    // Abort any previous in-flight stream before starting a new one
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }

    const q = input.trim();
    setInput('');
    setLoading(true);

    // Add user message + empty assistant placeholder
    setMessages(prev => [...prev, { role: 'user', content: q }, { role: 'assistant', content: '' }]);

    // 按需创建聊天：空白状态下提交时先创建新聊天文件
    let chatFile = activeChat;
    if (!chatFile) {
      try {
        const res = await sessionApi.newChat(name);
        chatFile = res.chat_file;
        setActiveChat(chatFile);
        load(); // 立即刷新侧边栏，新聊天无需等流结束就出现
      } catch (e) {
        setMessages(prev => {
          const msgs = [...prev];
          const last = { ...msgs[msgs.length - 1] };
          last.content = `❌ 创建聊天失败: ${e}`;
          msgs[msgs.length - 1] = last;
          return msgs;
        });
        setLoading(false);
        return;
      }
    }

    const controller = new AbortController();
    abortRef.current = controller;

    await sessionApi.chatStream(name, q, {
      signal: controller.signal,
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
      onDone: (_chat_file) => {
        abortRef.current = null;
        setLoading(false);
        load();
      },
      onError: (err: SessionStreamError) => {
        abortRef.current = null;
        const showErrorMessage = () => {
          setMessages(prev => {
            const msgs = [...prev];
            const last = { ...msgs[msgs.length - 1] };
            last.content = `❌ ${err.message}`;
            msgs[msgs.length - 1] = last;
            return msgs;
          });
        };

        const isKbError = err.category === 'kb';
        if (isKbError) {
          showErrorMessage();
          setLoading(false);
          load();
          alert('⚠️ 知识库中还没有索引数据\n\n请先在知识库中上传并索引文件，然后再开始对话。');
          return;
        }

        const isModelError = err.category === 'model' || err.code === 'MODEL_UNAVAILABLE';
        if (isModelError) {
          showErrorMessage();
          setLoading(false);
          load();
          alert(`⚠️ 模型加载失败\n\n${err.message}`);
          return;
        }
        showErrorMessage();
        setLoading(false);
        load();
      },
    }, chatFile);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // 聊天删除：从服务器获取最新列表再计算 activeChat，修复 race condition
  const handleDeleteChat = async (chatFile: string) => {
    if (!name || !confirm(`确定删除聊天「${chatFile}」？`)) return;
    // Cancel any in-flight stream before deleting the currently selected chat
    if (activeChat === chatFile && abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
      setLoading(false);
    }
    await sessionApi.deleteChat(name, chatFile);
    const updated = await sessionApi.listChats(name);
    setChats(updated.chats);
    if (activeChat === chatFile) {
      const remaining = updated.chats.filter(x => x.file !== chatFile);
      const nextChat = remaining.length > 0 ? remaining[0].file : null;
      setMessages([]);
      setActiveChat(nextChat);
      if (nextChat) sessionApi.selectChat(name, nextChat).catch(console.error);
    }
  };

  const handleShowBind = async () => {
    const list = await kbApi.list();
    setKbList(list);
    setShowBind(true);
  };

  if (!name) return null;

  return (
    <div className={styles.wrapper}>
      <SessionSidebar
        name={name} sessionInfo={sessionInfo}
        chats={chats} activeChat={activeChat}
        onSelectChat={handleSelectChat}
        onDeleteChat={handleDeleteChat}
        onNewChat={handleNewChat}
        showBind={showBind} kbList={kbList}
        onBind={handleBind} onShowBind={handleShowBind}
        topK={topK} topN={topN} systemPrompt={systemPrompt}
        saveStatus={saveStatus} showParams={showParams}
        onTopKChange={v => { setTopK(v); setSaveStatus('idle'); }}
        onTopNChange={v => { setTopN(v); setSaveStatus('idle'); }}
        onSystemPromptChange={v => { setSystemPrompt(v); setSaveStatus('idle'); }}
        onSaveConfig={handleSaveConfig}
        onToggleParams={() => setShowParams(p => !p)}
      />

      <ChatArea
        messages={messages} activeChat={activeChat}
        chatsCount={chats.length} loading={loading}
        input={input} onInputChange={setInput}
        onSubmit={handleSubmit} onKeyDown={handleKeyDown}
      />
    </div>
  );
}
