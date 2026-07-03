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
  return (
    <div className={styles.chatListSection}>
      <button onClick={onNewChat} className={styles.btnNewChat}>＋ 新聊天</button>
      <div className={styles.chatListHeader}>聊天列表</div>
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
              onDelete(c.file);
            }}
            className={styles.chatDeleteBtn}
            title="删除聊天"
          >🗑️</button>
        </div>
      ))}
    </div>
  );
}
