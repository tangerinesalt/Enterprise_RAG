import styles from '../pages/SessionChat.module.css';

interface Props {
  topK: number;
  topN: number;
  systemPrompt: string;
  saveStatus: 'idle' | 'saving' | 'saved' | 'error';
  showParams: boolean;
  onTopKChange: (v: number) => void;
  onTopNChange: (v: number) => void;
  onSystemPromptChange: (v: string) => void;
  onSave: () => void;
  onToggle: () => void;
}

export default function ParameterPanel({
  topK, topN, systemPrompt, saveStatus, showParams,
  onTopKChange, onTopNChange, onSystemPromptChange, onSave, onToggle,
}: Props) {
  return (
    <div className={styles.paramsSection}>
      <div onClick={onToggle} className={styles.paramsToggle}>
        <span className={styles.paramsToggleLabel}>🔍 检索参数</span>
        <span className={styles.paramsToggleArrow}>{showParams ? '▼' : '▶'}</span>
      </div>

      {showParams && (
        <div className={styles.paramsBody}>
          <div className={styles.paramRow}>
            <label className={styles.paramLabel}>top_k:</label>
            <input
              type="number" min={1} value={topK}
              onChange={e => onTopKChange(Number(e.target.value))}
              className={styles.paramInput}
            />
            <span className={styles.paramHint}>召回数</span>
          </div>
          <div className={styles.paramRow}>
            <label className={styles.paramLabel}>top_n:</label>
            <input
              type="number" min={1} value={topN}
              onChange={e => onTopNChange(Number(e.target.value))}
              className={styles.paramInput}
            />
            <span className={styles.paramHint}>保留数</span>
          </div>

          <div className={styles.promptSection}>
            <label className={styles.promptLabel}>📝 提示词</label>
            <textarea
              value={systemPrompt}
              onChange={e => onSystemPromptChange(e.target.value)}
              placeholder="提示词内容（为空时使用默认提示）"
              rows={8}
              className={styles.promptTextarea}
            />
          </div>

          <div className={styles.saveRow}>
            <button
              onClick={onSave}
              disabled={saveStatus === 'saving'}
              className={`${styles.btnSave} ${styles.btnSaveIdle}`}
            >
              {saveStatus === 'saving' ? '保存中...' : '💾 保存'}
            </button>
            {saveStatus === 'saved' && <span className={styles.saveSuccess}>✓ 已保存</span>}
            {saveStatus === 'error' && <span className={styles.saveError}>保存失败，参数必须 ≥ 1</span>}
          </div>
        </div>
      )}
    </div>
  );
}
