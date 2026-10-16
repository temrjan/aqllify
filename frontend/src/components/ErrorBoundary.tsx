import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: string;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: '' };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error: error.message };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '24px',
          textAlign: 'center',
          color: 'var(--tg-text)',
          background: 'var(--tg-bg)',
          minHeight: '60vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '12px',
        }}>
          <div style={{ fontSize: '48px' }}>{'⚠️'}</div>
          <h2>Произошла ошибка</h2>
          <p style={{ fontSize: '13px', color: 'var(--tg-hint)', maxWidth: '300px', wordBreak: 'break-word' }}>
            {this.state.error}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: '' });
              window.location.href = '/';
            }}
            style={{
              marginTop: '12px',
              padding: '12px 24px',
              background: 'var(--accent)',
              color: 'var(--on-accent)',
              border: 'none',
              borderRadius: '12px',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            На главную
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
