import { useEffect, useRef, useState } from 'react';
import styles from '../pages/SessionChat.module.css';
import MarkdownMessage from './MarkdownMessage';
import ChatInput from './ChatInput';

// ── 加载动画参数 ───────────────────────────
const LOADING_TEXTS = ['Thinking', 'Searching', 'Loading', 'Researching'];
const DOT_CYCLE = [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]; // 1→6→1 点模式
const STEPS_PER_CYCLE = DOT_CYCLE.length;                // 11
const CYCLES_PER_TEXT = 3;                               // 每个文字点循环次数
const STEPS_PER_TEXT = STEPS_PER_CYCLE * CYCLES_PER_TEXT; // 33
const ANIMATION_INTERVAL_MS = 250;

interface Message {
  role: string;
  content: string;
  sources?: { text: string; score: number }[];
}

interface Props {
  messages: Message[];
  activeChat: string | null;
  chatsCount: number;
  loading: boolean;
  input: string;
  onInputChange: (v: string) => void;
  onSubmit: () => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
}

export default function ChatArea({
  messages, activeChat, chatsCount, loading,
  input, onInputChange, onSubmit, onKeyDown,
}: Props) {
  const msgEndRef = useRef<HTMLDivElement>(null);

  // ── 加载动画状态 ─────────────────────────
  const [animStep, setAnimStep] = useState(0);

  // 最后一个 assistant 消息有内容 → 答案已开始出现，停止动画
  const lastMsg = messages[messages.length - 1];
  const hasAnswer = lastMsg?.role === 'assistant' && lastMsg.content.length > 0;

  useEffect(() => {
    if (!loading || hasAnswer) {
      setAnimStep(0);
      return;
    }
    const timer = setInterval(() => {
      setAnimStep(prev => prev + 1);
    }, ANIMATION_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [loading, hasAnswer]);

  // 从步数计算当前文字和点数
  const stepInText = animStep % STEPS_PER_TEXT;
  const textIndex = Math.floor(animStep / STEPS_PER_TEXT) % LOADING_TEXTS.length;
  const dotCount = DOT_CYCLE[stepInText % STEPS_PER_CYCLE];
  const statusText = LOADING_TEXTS[textIndex] + '.'.repeat(dotCount);

  useEffect(() => {
    msgEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div className={styles.chatArea}>
      {activeChat ? (
        <>
          <div className={styles.activeChatLabel}>{activeChat}</div>
          <div className={styles.messageList}>
            {messages.map((msg, i) => (
              <div key={i} className={`${styles.message} ${msg.role === 'user' ? styles.messageUser : styles.messageAssistant}`}>
                <div className={`${styles.roleLabel} ${msg.role === 'user' ? styles.roleUser : styles.roleAssistant}`}>
                  {msg.role === 'user' ? '👤 用户' : '🤖 助手'}
                </div>
                {msg.role === 'user' ? (
                  <div className={styles.userContent}>{msg.content}</div>
                ) : (
                  <div className={styles.assistantContent}>
                    <MarkdownMessage content={msg.content} sources={msg.sources} />
                  </div>
                )}
              </div>
            ))}
            {loading && !hasAnswer && (
              <div className={styles.statusLine}>{statusText}</div>
            )}
            <div ref={msgEndRef} />
          </div>
        </>
      ) : (
        <div className={styles.emptyMessages}>
          {chatsCount === 0 ? '输入问题自动创建新聊天' : '选择已有聊天，或直接输入问题'}
        </div>
      )}

      <ChatInput
        input={input}
        loading={loading}
        onChange={onInputChange}
        onSubmit={onSubmit}
        onKeyDown={onKeyDown}
      />
    </div>
  );
}
