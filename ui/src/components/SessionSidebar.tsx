import { useNavigate } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import styles from '../pages/SessionChat.module.css';
import ParameterPanel from './ParameterPanel';
import ChatList from './ChatList';
import type { ChatFile, KbItem, SessionItem } from '../api';

interface Props {
  name: string;
  sessionInfo: SessionItem | null;
  // chat list
  chats: ChatFile[];
  activeChat: string | null;
  onSelectChat: (file: string) => void;
  onDeleteChat: (file: string) => void;
  onNewChat: () => void;
  // bind KB
  kbList: KbItem[];
  onBind: (kbName: string) => void;
  onShowBind: () => void;
  // params
  topK: number;
  topN: number;
  systemPrompt: string;
  saveStatus: 'idle' | 'saving' | 'saved' | 'error';
  onTopKChange: (v: number) => void;
  onTopNChange: (v: number) => void;
  onSystemPromptChange: (v: string) => void;
  onSaveConfig: () => void;
}

export default function SessionSidebar({
  name, sessionInfo,
  chats, activeChat, onSelectChat, onDeleteChat, onNewChat,
  kbList, onBind, onShowBind,
  topK, topN, systemPrompt, saveStatus,
  onTopKChange, onTopNChange, onSystemPromptChange, onSaveConfig,
}: Props) {
  const navigate = useNavigate();
  const [showKbDropdown, setShowKbDropdown] = useState(false);
  const kbRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭 KB 下拉
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (kbRef.current && !kbRef.current.contains(e.target as Node)) {
        setShowKbDropdown(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleKbClick = async () => {
    await onShowBind();
    setShowKbDropdown(prev => !prev);
  };

  const handleKbSelect = (kbName: string) => {
    onBind(kbName);
    setShowKbDropdown(false);
  };

  return (
    <div className={styles.sidebar}>
      <button onClick={() => navigate('/session')} className={styles.btnBack}>← 返回</button>
      <h3 className={styles.sessionTitle}>{name}</h3>

      {/* 知识库选择器 */}
      <div ref={kbRef} style={{ position: 'relative' }}>
        <div
          onClick={handleKbClick}
          style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '8px 12px', borderRadius: 'var(--md-radius-sm)',
            border: '1px solid var(--md-outline)',
            cursor: 'pointer', fontSize: 13,
            transition: 'border-color 150ms',
          }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--md-primary)'; }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--md-outline)'; }}
        >
          <span>📚</span>
          <span style={{ flex: 1 }}>{sessionInfo?.kb_name || '未绑定知识库'}</span>
          <span style={{ fontSize: 10, color: 'var(--md-text-muted)' }}>▾</span>
        </div>

        {showKbDropdown && (
          <div style={{
            position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 20,
            marginTop: 4,
            background: 'var(--md-surface)',
            border: '1px solid var(--md-outline)',
            borderRadius: 'var(--md-radius-sm)',
            boxShadow: 'var(--md-shadow-md)',
            overflow: 'hidden',
          }}>
            {kbList.length === 0 && (
              <div style={{ padding: '8px 12px', fontSize: 12, color: 'var(--md-text-muted)' }}>
                暂无知识库，请先创建
              </div>
            )}
            {kbList.map(kb => (
              <div
                key={kb.name}
                onClick={() => handleKbSelect(kb.name)}
                style={{
                  padding: '8px 12px', fontSize: 13, cursor: 'pointer',
                  background: sessionInfo?.kb_name === kb.name ? 'var(--md-primary-container)' : 'transparent',
                  fontWeight: sessionInfo?.kb_name === kb.name ? 500 : 400,
                }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'var(--md-surface-variant)'; }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLElement).style.background =
                    sessionInfo?.kb_name === kb.name ? 'var(--md-primary-container)' : 'transparent';
                }}
              >
                📁 {kb.name}
              </div>
            ))}
            <div
              onClick={() => { navigate('/kb'); setShowKbDropdown(false); }}
              style={{
                padding: '8px 12px', fontSize: 13, cursor: 'pointer',
                borderTop: '1px solid var(--md-outline)',
                color: 'var(--md-primary)',
              }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'var(--md-surface-variant)'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
            >
              ＋ 创建新知识库
            </div>
          </div>
        )}
      </div>

      <ParameterPanel
        topK={topK} topN={topN} systemPrompt={systemPrompt}
        saveStatus={saveStatus}
        onTopKChange={onTopKChange} onTopNChange={onTopNChange}
        onSystemPromptChange={onSystemPromptChange}
        onSave={onSaveConfig}
      />

      <ChatList
        chats={chats} activeChat={activeChat}
        onSelect={onSelectChat} onDelete={onDeleteChat}
        onNewChat={onNewChat}
      />
    </div>
  );
}
