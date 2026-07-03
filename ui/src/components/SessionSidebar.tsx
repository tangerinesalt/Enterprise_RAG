import { useNavigate } from 'react-router-dom';
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
  showBind: boolean;
  kbList: KbItem[];
  onBind: (kbName: string) => void;
  onShowBind: () => void;
  // params
  topK: number;
  topN: number;
  systemPrompt: string;
  saveStatus: 'idle' | 'saving' | 'saved' | 'error';
  showParams: boolean;
  onTopKChange: (v: number) => void;
  onTopNChange: (v: number) => void;
  onSystemPromptChange: (v: string) => void;
  onSaveConfig: () => void;
  onToggleParams: () => void;
}

export default function SessionSidebar({
  name, sessionInfo,
  chats, activeChat, onSelectChat, onDeleteChat, onNewChat,
  showBind, kbList, onBind, onShowBind,
  topK, topN, systemPrompt, saveStatus, showParams,
  onTopKChange, onTopNChange, onSystemPromptChange, onSaveConfig, onToggleParams,
}: Props) {
  const navigate = useNavigate();

  return (
    <div className={styles.sidebar}>
      <button onClick={() => navigate('/session')} className={styles.btnBack}>← 返回</button>
      <h3 className={styles.sessionTitle}>{name}</h3>

      <div className={styles.kbLabel}>
        KB: {sessionInfo?.kb_name || '未绑定'}
      </div>

      {sessionInfo?.kb_name ? null : (
        <button onClick={onShowBind} className={styles.btnSmall}>🔗 绑定知识库</button>
      )}

      {showBind && (
        <div className={styles.bindList}>
          {kbList.map(kb => (
            <div key={kb.name} onClick={() => onBind(kb.name)} className={styles.bindItem}>
              📁 {kb.name}
            </div>
          ))}
        </div>
      )}

      <ParameterPanel
        topK={topK} topN={topN} systemPrompt={systemPrompt}
        saveStatus={saveStatus} showParams={showParams}
        onTopKChange={onTopKChange} onTopNChange={onTopNChange}
        onSystemPromptChange={onSystemPromptChange}
        onSave={onSaveConfig} onToggle={onToggleParams}
      />

      <ChatList
        chats={chats} activeChat={activeChat}
        onSelect={onSelectChat} onDelete={onDeleteChat}
        onNewChat={onNewChat}
      />
    </div>
  );
}
