import styles from '../pages/SessionChat.module.css';

interface Props {
  input: string;
  loading: boolean;
  onChange: (v: string) => void;
  onSubmit: () => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
}

export default function ChatInput({ input, loading, onChange, onSubmit, onKeyDown }: Props) {
  return (
    <div className={styles.inputArea}>
      <textarea
        value={input}
        onChange={e => onChange(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
        rows={2}
        className={styles.chatInput}
      />
      <button
        onClick={onSubmit}
        disabled={loading || !input.trim()}
        className={`${styles.btnSend} ${loading ? styles.btnSendLoading : styles.btnSendIdle}`}
      >
        {loading ? '...' : '↵ 发送'}
      </button>
    </div>
  );
}
