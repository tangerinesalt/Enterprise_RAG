import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'center', minHeight: '60vh', gap: 16,
          color: '#6b7280', padding: 24,
        }}>
          <div style={{ fontSize: 48 }}>⚠️</div>
          <h2 style={{ margin: 0, color: '#1f2937', fontSize: 18 }}>页面出现异常</h2>
          <p style={{ margin: 0, textAlign: 'center', maxWidth: 400, fontSize: 14 }}>
            {this.state.error?.message || '发生了未知错误'}
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '8px 24px', background: '#2563eb', color: '#fff',
              border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 14,
            }}
          >
            重新加载
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
