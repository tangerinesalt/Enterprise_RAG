import { useNavigate } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import styles from '../pages/SessionChat.module.css';
import ParameterPanel from './ParameterPanel';
import ChatList from './ChatList';
import type { ChatFile, KbItem, SessionItem } from '../api';

interface Props {
  name: string;
  sessionInfo: SessionItem | null;
  chats: ChatFile[];
  activeChat: string | null;
  onSelectChat: (file: string) => void;
  onDeleteChat: (file: string) => void;
  onNewChat: () => void;
  kbList: KbItem[];
  onBind: (kbName: string) => void;
  onShowBind: () => void;
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
      <button onClick={() => navigate('/session')} className={styles.btnBack}>← 返回会话列表</button>
      <h3 className={styles.sessionTitle}>{name}</h3>

      <div ref={kbRef} className={styles.kbPickerWrap}>
        <button
          type="button"
          onClick={handleKbClick}
          className={styles.kbPicker}
        >
          <span className={styles.kbPickerIcon}>📁</span>
          <span className={styles.kbPickerName}>{sessionInfo?.kb_name || '未绑定知识库'}</span>
          <span className={styles.kbPickerChevron}>⌄</span>
        </button>

        {showKbDropdown && (
          <div className={styles.kbDropdown}>
            {kbList.length === 0 && (
              <div className={styles.kbDropdownEmpty}>
                暂无知识库，请先创建
              </div>
            )}
            {kbList.map(kb => (
              <button
                type="button"
                key={kb.name}
                onClick={() => handleKbSelect(kb.name)}
                className={`${styles.kbDropdownItem} ${sessionInfo?.kb_name === kb.name ? styles.kbDropdownItemActive : ''}`}
              >
                📁 {kb.name}
              </button>
            ))}
            <button
              type="button"
              onClick={() => { navigate('/kb'); setShowKbDropdown(false); }}
              className={styles.kbCreateItem}
            >
              + 创建新知识库
            </button>
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
