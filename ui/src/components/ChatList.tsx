import { useState, useRef, useEffect } from 'react';
import styles from '../pages/SessionChat.module.css';
import type { ChatFile } from '../api';

interface Props {
  chats: ChatFile[];
  activeChat: string | null;
  onSelect: (file: string) => void;
  onDelete: (file: string) => void;
  onNewChat: () => void;
}

export default function ChatList({ chats, activeChat, onSelect, onDelete, onNewChat }: Props) {
  const [menuOpen, setMenuOpen] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // 点击外部关闭菜单
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(null);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleDelete = (file: string) => {
    setMenuOpen(null);
    if (confirm(`确定删除聊天「${file}」？`)) {
      onDelete(file);
    }
  };

  return (
    <div className={styles.chatListSection}>
      <button onClick={onNewChat} className={styles.btnNewChat}>＋ 新聊天</button>
      <div className={styles.chatListHeader}>历史对话</div>
      {chats.map(c => (
        <div
          key={c.file}
          className={`${styles.chatRow} ${activeChat === c.file ? styles.chatRowActive : styles.chatRowInactive}`}
        >
          <div
            onClick={() => onSelect(c.file)}
            className={styles.chatLabel}
          >
            {c.preview || c.file}
          </div>
          <button
            onClick={e => {
              e.stopPropagation();
              setMenuOpen(menuOpen === c.file ? null : c.file);
            }}
            className={styles.chatMenuBtn}
            title="更多"
          >⋯</button>

          {menuOpen === c.file && (
            <div className={`${styles.chatMenu} ${styles.open}`} ref={menuRef}>
              <button
                className={`${styles.chatMenuItem} ${styles.chatMenuItemDanger}`}
                onClick={() => handleDelete(c.file)}
              >
                🗑️ 删除
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
