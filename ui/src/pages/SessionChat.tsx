import { useEffect, useState, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { sessionApi, kbApi } from '../api';
import type { ChatFile, KbItem, SessionItem } from '../api';
import SessionSidebar from '../components/SessionSidebar';
import ChatArea from '../components/ChatArea';
import styles from './SessionChat.module.css';

interface Message {
  role: string;
  content: string;
  sources?: { text: string; score: number }[];
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
      .then(d => setMessages(d.messages.map(m => ({
        role: m.role,
        content: m.content,
        sources: m.additional_kwargs?.sources || undefined,
      }))))
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

  const handleNewChat = () => {
    setActiveChat(null);
    setMessages([]);
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
      onError: (err) => {
        abortRef.current = null;
        const showErrorMessage = () => {
          setMessages(prev => {
            const msgs = [...prev];
            const last = { ...msgs[msgs.length - 1] };
            last.content = `❌ ${err}`;
            msgs[msgs.length - 1] = last;
            return msgs;
          });
        };

        // 知识库无向量等预检错误 → 保留新聊天并写入错误消息
        const isKbError = err.includes('没有向量') || err.includes('未找到索引') || err.includes('未绑定知识库');
        if (isKbError) {
          showErrorMessage();
          setLoading(false);
          load();
          alert('⚠️ 知识库中还没有索引数据\n\n请先在知识库中上传并索引文件，然后再开始对话。');
          return;
        }
        // 模型初始化错误 → 弹窗提示
        const isModelError = err.includes('Ollama') || err.includes('模型') || err.includes('Embedding');
        if (isModelError) {
          showErrorMessage();
          setLoading(false);
          load();
          alert(`⚠️ 模型加载失败\n\n${err}`);
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
    await sessionApi.deleteChat(name, chatFile);
    const updated = await sessionApi.listChats(name);
    setChats(updated.chats);
    if (activeChat === chatFile) {
      const remaining = updated.chats.filter(x => x.file !== chatFile);
      setActiveChat(remaining.length > 0 ? remaining[0].file : null);
      if (remaining.length === 0) setMessages([]);
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
        onSelectChat={setActiveChat}
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
