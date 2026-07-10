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
      <div className={styles.inputContainer}>
        <textarea
          value={input}
          onChange={e => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="输入问题..."
          rows={1}
          className={styles.chatInput}
        />
        <button
          onClick={onSubmit}
          disabled={loading || !input.trim()}
          className={`${styles.btnSend} ${loading ? styles.btnSendLoading : styles.btnSendIdle}`}
        >
          ↵
        </button>
      </div>
    </div>
  );
}
