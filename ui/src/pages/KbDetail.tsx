import { useEffect, useEffectEvent, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { kbApi } from '../api';
import type { FileItem } from '../api';
import styles from './KbDetail.module.css';

interface ProgressInfo {
  current: number;
  total: number;
  pct: number;
}

export default function KbDetail() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();
  const [files, setFiles] = useState<FileItem[]>([]);
  const [indexingProgress, setIndexingProgress] = useState<Record<string, ProgressInfo>>({});
  const [isIndexingAll, setIsIndexingAll] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const folderRef = useRef<HTMLInputElement>(null);

  const load = useEffectEvent(() => {
    if (!name) return;
    kbApi.get(name).then(d => setFiles(d.files)).catch(console.error);
  });

  useEffect(() => { load(); }, [name]);

  const handleUpload = async (isFolder: boolean) => {
    if (!name) return;
    const input = isFolder ? folderRef.current : fileRef.current;
    if (!input?.files?.length) return;
    await kbApi.upload(name, Array.from(input.files));
    input.value = '';
    load();
  };

  const handleDelete = async (target: string) => {
    if (!name || !confirm(`确定删除「${target}」？`)) return;
    await kbApi.deleteFile(name, target);
    setIndexingProgress(prev => {
      const next = { ...prev };
      delete next[target];
      return next;
    });
    load();
  };

  const handleReindex = async (target: string) => {
    if (!name) return;
    // 先显示索引中状态，再调用重新索引
    setIndexingProgress(prev => ({ ...prev, [target]: { current: 0, total: 1, pct: 0 } }));
    try {
      await kbApi.reindex(name, target);
      setIndexingProgress(prev => {
        const next = { ...prev };
        delete next[target];
        return next;
      });
      load();
    } catch (e) {
      console.error(`Reindex error for ${target}:`, e);
      // 清除 stuck 的进度状态，触发 load 刷新
      setIndexingProgress(prev => {
        const next = { ...prev };
        delete next[target];
        return next;
      });
      load();
    }
  };

  // SSE 流式索引单个文件
  const handleIndex = async (target: string) => {
    if (!name) return;
    // 在 SSE 请求之前就设置进度状态，确保 React 立即渲染"索引中"UI
    setIndexingProgress(prev => ({ ...prev, [target]: { current: 0, total: 1, pct: 0 } }));

    try {
      await kbApi.indexStream(name, {
        onStart: (file, totalChunks) => {
          setIndexingProgress(prev => ({ ...prev, [file]: { current: 0, total: totalChunks, pct: 0 } }));
        },
        onProgress: (file, current, total, pct) => {
          setIndexingProgress(prev => ({ ...prev, [file]: { current, total, pct } }));
        },
        onDone: (file, chunks) => {
          setIndexingProgress(prev => {
            const next = { ...prev };
            delete next[file];
            return next;
          });
          // 直接本地更新文件状态，避免 load() 的异步请求造成两次渲染覆盖进度
          setFiles(prev => prev.map(f =>
            f.name === file ? { ...f, indexed: 'indexed', chunks } : f
          ));
        },
        onError: (file, message) => {
          console.error(`Index error for ${file}: ${message}`);
          // 清除该文件的乐观进度，避免卡在"索引中"状态
          setIndexingProgress(prev => {
            const next = { ...prev };
            delete next[file];
            return next;
          });
          load();
        },
      }, target);
    } catch (e) {
      console.error(`Index request failed for ${target}:`, e);
      // 请求级失败：清除乐观进度
      setIndexingProgress(prev => {
        const next = { ...prev };
        delete next[target];
        return next;
      });
      load();
    }
  };

  // SSE 流式索引全部
  const handleIndexAll = async () => {
    if (!name) return;
    setIsIndexingAll(true);
    try {
      await kbApi.indexStream(name, {
        onStart: (file, totalChunks) => {
          setIndexingProgress(prev => ({ ...prev, [file]: { current: 0, total: totalChunks, pct: 0 } }));
        },
        onProgress: (file, current, total, pct) => {
          setIndexingProgress(prev => ({ ...prev, [file]: { current, total, pct } }));
        },
        onDone: (file, chunks) => {
          setIndexingProgress(prev => {
            const next = { ...prev };
            delete next[file];
            return next;
          });
          // 本地更新文件状态，让已完成文件立即显示"✓ 已索引"，不影响其他文件的进度
          setFiles(prev => prev.map(f =>
            f.name === file ? { ...f, indexed: 'indexed', chunks } : f
          ));
        },
        onAllDone: (_files) => {
          setIsIndexingAll(false);
          load(); // 全部完成，刷新状态
        },
        onError: (file, message) => {
          console.error(`Index error for ${file}: ${message}`);
          // 清除该文件的乐观进度，避免卡在"索引中"状态
          setIndexingProgress(prev => {
            const next = { ...prev };
            delete next[file];
            return next;
          });
          load();
        },
      }, undefined, true);
    } catch (e) {
      console.error('Index all request failed:', e);
      // 请求级失败：清除所有乐观进度和批量索引状态
      setIndexingProgress({});
      setIsIndexingAll(false);
      load();
    }
  };

  const getProgress = (fileName: string): ProgressInfo | undefined => indexingProgress[fileName];

  const getButtonState = (f: FileItem) => {
    const prog = getProgress(f.name);
    if (prog) return 'indexing';
    return f.indexed || 'pending';
  };

  // 汇总进度
  const pendingCount = files.filter(f => (f.indexed || 'pending') === 'pending' && !getProgress(f.name)).length;
  const indexingCount = Object.keys(indexingProgress).length;
  const indexedCount = files.filter(f => f.indexed === 'indexed' && !getProgress(f.name)).length;

  return (
    <div>
      <button onClick={() => navigate('/kb')} className={styles.backLink}>← 返回</button>
      <h2 className={styles.title}>📁 {name}</h2>

      <div className={styles.actions}>
        <button onClick={() => fileRef.current?.click()} className={styles.btnPrimary}>📄 上传文件</button>
        <button onClick={() => folderRef.current?.click()} className={styles.btnPrimary}>📁 上传文件夹</button>
        <button
          onClick={handleIndexAll}
          disabled={isIndexingAll}
          className={`${styles.btnSec} ${isIndexingAll ? styles.btnDisabled : ''}`}
        >
          ⚡ 索引全部
          {isIndexingAll && ` (${indexedCount + indexingCount}/${files.length})`}
        </button>
      </div>

      <input ref={fileRef} type="file" multiple style={{ display: 'none' }} onChange={() => handleUpload(false)} />
      <input ref={folderRef} type="file" style={{ display: 'none' }} onChange={() => handleUpload(true)} {...{ 'webkitdirectory': '' } as any} />

      {files.length === 0 && <p className={styles.empty}>暂无文件</p>}

      <div className={styles.fileList}>
        {files.map(f => {
          const prog = getProgress(f.name);
          const btnState = getButtonState(f);
          const isFolder = f.type === 'folder';
          return (
            <div key={f.name} className={styles.row}>
              <div className={styles.rowInfo}>
                <div className={styles.rowName}>
                  <span>{isFolder ? '📁' : '📄'} {f.name}</span>
                  <span className={styles.rowSize}>{f.size_str}</span>
                </div>
                {/* 进度条 */}
                {prog ? (
                  <div className={styles.progressContainer}>
                    <div className={styles.progressBar}>
                      <div className={styles.progressFill} style={{ width: `${prog.pct}%` }} />
                    </div>
                    <span className={styles.progressText}>{prog.pct}% 索引中 ({prog.current}/{prog.total} chunks)</span>
                  </div>
                ) : f.indexed === 'indexed' ? (
                  <div className={styles.progressContainer}>
                    <div className={styles.progressBar}>
                      <div className={styles.progressFillFull} />
                    </div>
                    <span className={styles.progressDone}>✓ 已索引{f.chunks != null ? ` (${f.chunks} chunks)` : ''}</span>
                  </div>
                ) : null}
              </div>
              <div className={styles.rowActions}>
                {!isFolder && (
                  <>
                    <button
                      onClick={() => btnState === 'indexed' ? handleReindex(f.name) : handleIndex(f.name)}
                      disabled={btnState === 'indexing'}
                      className={
                        btnState === 'indexed' ? styles.btnIndexed :
                        btnState === 'indexing' ? styles.btnIndexing :
                        styles.btnSmall
                      }
                    >
                      {btnState === 'indexed' ? '✓ 已索引' :
                       btnState === 'indexing' ? '索引中⋯' : '索引'}
                    </button>
                    {btnState === 'indexed' && (
                      <button
                        onClick={() => handleReindex(f.name)}
                        className={styles.btnRefresh}
                        title="重新索引"
                      >🔄</button>
                    )}
                  </>
                )}
                <button onClick={() => handleDelete(f.name)} className={styles.btnSmallDanger}>🗑️</button>
              </div>
            </div>
          );
        })}
      </div>

      {/* 汇总信息 */}
      {files.length > 0 && (
        <div className={styles.summary}>
          共 {files.length} 个文件 · 已索引 {indexedCount} · 待索引 {pendingCount}
          {indexingCount > 0 && ` · 索引中 ${indexingCount}`}
        </div>
      )}
    </div>
  );
}
