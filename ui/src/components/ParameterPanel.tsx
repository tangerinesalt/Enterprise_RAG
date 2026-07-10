import styles from '../pages/SessionChat.module.css';

interface Props {
  topK: number;
  topN: number;
  systemPrompt: string;
  saveStatus: 'idle' | 'saving' | 'saved' | 'error';
  onTopKChange: (v: number) => void;
  onTopNChange: (v: number) => void;
  onSystemPromptChange: (v: string) => void;
  onSave: () => void;
}

export default function ParameterPanel({
  topK, topN, systemPrompt, saveStatus,
  onTopKChange, onTopNChange, onSystemPromptChange, onSave,
}: Props) {
  return (
    <div className={styles.paramsSection}>
      <div className={styles.paramsBody}>
        <div className={styles.paramRow}>
          <span className={styles.paramLabel}>Top-K</span>
          <input
            type="number" min={1} value={topK}
            onChange={e => onTopKChange(Number(e.target.value))}
            className={styles.paramInput}
          />
          <span className={styles.paramHint}>初召</span>
        </div>
        <div className={styles.paramRow}>
          <span className={styles.paramLabel}>Top-N</span>
          <input
            type="number" min={1} value={topN}
            onChange={e => onTopNChange(Number(e.target.value))}
            className={styles.paramInput}
          />
          <span className={styles.paramHint}>保留</span>
        </div>

        <div className={styles.promptSection}>
          <label className={styles.promptLabel}>📝 系统提示词</label>
          <textarea
            value={systemPrompt}
            onChange={e => onSystemPromptChange(e.target.value)}
            placeholder="提示词内容（为空时使用默认提示）"
            rows={3}
            className={styles.promptTextarea}
          />
        </div>

        <div className={styles.saveRow}>
          <button
            onClick={onSave}
            disabled={saveStatus === 'saving'}
            className={styles.btnSave}
          >
            {saveStatus === 'saving' ? '保存中...' : '💾 保存全部配置'}
          </button>
          {saveStatus === 'saved' && <span className={styles.saveSuccess}>✓ 已保存</span>}
          {saveStatus === 'error' && <span className={styles.saveError}>保存失败，参数必须 ≥ 1</span>}
        </div>
      </div>
    </div>
  );
}
