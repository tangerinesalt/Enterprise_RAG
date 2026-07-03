import { useEffect, useRef } from 'react';
import styles from '../pages/SessionChat.module.css';
import MarkdownMessage from './MarkdownMessage';
import ChatInput from './ChatInput';

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

  useEffect(() => {
    msgEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className={styles.chatArea}>
      {activeChat ? (
        <>
          <div className={styles.activeChatLabel}>{activeChat}</div>
          <div className={styles.messageList}>
            {messages.map((msg, i) => (
              <div key={i} className={styles.message}>
                <div className={`${styles.roleLabel} ${msg.role === 'user' ? styles.roleUser : styles.roleAssistant}`}>
                  {msg.role === 'user' ? '👤 用户' : '🤖 助手'}
                </div>
                {msg.role === 'user' ? (
                  <div className={styles.userContent}>{msg.content}</div>
                ) : (
                  <div className={styles.assistantContent}>
                    <MarkdownMessage content={msg.content} />
                    {msg.sources && msg.sources.length > 0 && (
                      <details className={styles.sourcesDetails}>
                        <summary className={styles.sourcesSummary}>
                          📎 来源 ({msg.sources.length})
                        </summary>
                        {msg.sources.map((s, i) => (
                          <div key={i} className={styles.sourceItem}>
                            <div className={styles.sourceScore}>
                              相关度: {s.score ?? 'N/A'}
                            </div>
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
