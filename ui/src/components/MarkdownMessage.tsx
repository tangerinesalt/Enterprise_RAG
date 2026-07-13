import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import styles from './MarkdownMessage.module.css';

const SUPPORTED_LANGUAGES = ['python', 'javascript', 'js', 'typescript', 'ts', 'bash', 'sh', 'json', 'sql', 'yaml', 'yml', 'markdown', 'md', 'text', 'powershell', 'ps1', 'dockerfile', 'diff', 'xml', 'html', 'css'];

interface SourceItem {
  text: string;
  score: number;
}

interface Props {
  content: string;
  sources?: SourceItem[];
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).catch(() => {});
}

export default function MarkdownMessage({ content, sources }: Props) {
  const [sourcesOpen, setSourcesOpen] = useState(false);

  return (
    <>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeSanitize]}
        components={{
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            const lang = match ? match[1] : '';
            const codeStr = String(children).replace(/\n$/, '');

            if (match && SUPPORTED_LANGUAGES.includes(lang)) {
              return (
                <div className={styles.codeBlock}>
                  <div className={styles.codeHeader}>
                    <span>{lang}</span>
                    <button
                      onClick={() => copyToClipboard(codeStr)}
                      className={styles.copyBtn}
                      title="复制代码"
                    >
                      复制
                    </button>
                  </div>
                  <SyntaxHighlighter
                    style={oneLight}
                    language={lang}
                    PreTag="div"
                    customStyle={{ margin: 0, borderRadius: 0, fontSize: 13 }}
                  >
                    {codeStr}
                  </SyntaxHighlighter>
                </div>
              );
            }

            if (!match) {
              return (
                <code className={styles.inlineCode} {...props}>
                  {children}
                </code>
              );
            }

            return (
              <pre className={styles.preBlock}>
                <code className={className} {...props}>{children}</code>
              </pre>
            );
          },
          h1: ({ children }) => <h1 className={styles.h1}>{children}</h1>,
          h2: ({ children }) => <h2 className={styles.h2}>{children}</h2>,
          h3: ({ children }) => <h3 className={styles.h3}>{children}</h3>,
          ul: ({ children }) => <ul className={styles.list}>{children}</ul>,
          ol: ({ children }) => <ol className={styles.list}>{children}</ol>,
          li: ({ children }) => <li className={styles.listItem}>{children}</li>,
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer" className={styles.link}>
              {children}
            </a>
          ),
          blockquote: ({ children }) => (
            <blockquote className={styles.blockquote}>
              {children}
            </blockquote>
          ),
          table: ({ children }) => (
            <div className={styles.tableWrapper}>
              <table className={styles.table}>
                {children}
              </table>
            </div>
          ),
          th: ({ children }) => (
            <th className={styles.th}>
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className={styles.td}>
              {children}
            </td>
          ),
          hr: () => <hr className={styles.hr} />,
          p: ({ children }) => <p className={styles.paragraph}>{children}</p>,
        }}
      >
        {content}
      </ReactMarkdown>

      {sources && sources.length > 0 && (
        <div className={styles.sourcesSection}>
          <div
            className={styles.sourcesTitle}
            onClick={() => setSourcesOpen(!sourcesOpen)}
          >
            <span className={`${styles.sourceArrow} ${sourcesOpen ? styles.open : ''}`}>›</span>
            来源 ({sources.length})
          </div>
          {sourcesOpen && (
            <div className={styles.sourceBody}>
              {sources.map((s, i) => (
                <div key={i} className={styles.sourceItem}>
                  <span className={styles.scoreBadge}>{s.score?.toFixed(2) ?? 'N/A'}</span>
                  <span className={styles.sourceText}>{s.text}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </>
  );
}
