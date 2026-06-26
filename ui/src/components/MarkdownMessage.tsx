import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';

// Only load common languages to keep bundle small
const SUPPORTED_LANGUAGES = ['python', 'javascript', 'js', 'typescript', 'ts', 'bash', 'sh', 'json', 'sql', 'yaml', 'yml', 'markdown', 'md', 'text', 'powershell', 'ps1', 'dockerfile', 'diff', 'xml', 'html', 'css'];

interface Props {
  content: string;
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text).catch(() => {});
}

export default function MarkdownMessage({ content }: Props) {
  return (
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
              <div style={{ position: 'relative', margin: '12px 0', borderRadius: 6, overflow: 'hidden', border: '1px solid #e5e7eb' }}>
                <div style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '4px 12px', background: '#f3f4f6', fontSize: 12, color: '#6b7280',
                }}>
                  <span>{lang}</span>
                  <button
                    onClick={() => copyToClipboard(codeStr)}
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      fontSize: 12, color: '#6b7280', padding: '2px 6px',
                    }}
                    title="复制代码"
                  >📋</button>
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

          // Inline code or unsupported language
          if (!match) {
            return (
              <code style={{
                background: '#f3f4f6', padding: '2px 6px', borderRadius: 3,
                fontSize: '0.9em', fontFamily: "'Fira Code', 'Cascadia Code', 'Consolas', monospace",
              }} {...props}>
                {children}
              </code>
            );
          }

          // Fallback: plain pre/code for unsupported languages
          return (
            <pre style={{
              background: '#f9fafb', padding: 12, borderRadius: 6,
              overflow: 'auto', fontSize: 13, border: '1px solid #e5e7eb',
            }}>
              <code className={className} {...props}>{children}</code>
            </pre>
          );
        },
        // Style other markdown elements
        h1: ({ children }) => <h1 style={{ fontSize: 20, margin: '16px 0 8px', borderBottom: '1px solid #e5e7eb', paddingBottom: 4 }}>{children}</h1>,
        h2: ({ children }) => <h2 style={{ fontSize: 18, margin: '14px 0 6px' }}>{children}</h2>,
        h3: ({ children }) => <h3 style={{ fontSize: 16, margin: '12px 0 4px' }}>{children}</h3>,
        ul: ({ children }) => <ul style={{ paddingLeft: 24, margin: '8px 0' }}>{children}</ul>,
        ol: ({ children }) => <ol style={{ paddingLeft: 24, margin: '8px 0' }}>{children}</ol>,
        li: ({ children }) => <li style={{ margin: '2px 0' }}>{children}</li>,
        a: ({ href, children }) => (
          <a href={href} target="_blank" rel="noopener noreferrer"
            style={{ color: '#2563eb', textDecoration: 'underline' }}>
            {children}
          </a>
        ),
        blockquote: ({ children }) => (
          <blockquote style={{
            borderLeft: '3px solid #d1d5db', margin: '8px 0',
            padding: '4px 12px', color: '#6b7280', background: '#f9fafb',
          }}>
            {children}
          </blockquote>
        ),
        table: ({ children }) => (
          <div style={{ overflowX: 'auto', margin: '8px 0' }}>
            <table style={{ borderCollapse: 'collapse', fontSize: 13, width: '100%' }}>
              {children}
            </table>
          </div>
        ),
        th: ({ children }) => (
          <th style={{ border: '1px solid #d1d5db', padding: '6px 10px', background: '#f3f4f6', fontWeight: 600, textAlign: 'left' }}>
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td style={{ border: '1px solid #d1d5db', padding: '6px 10px' }}>
            {children}
          </td>
        ),
        hr: () => <hr style={{ border: 'none', borderTop: '1px solid #e5e7eb', margin: '16px 0' }} />,
        p: ({ children }) => <p style={{ margin: '8px 0' }}>{children}</p>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
