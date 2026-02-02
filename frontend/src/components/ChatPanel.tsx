// 对话面板组件

import { useState, useRef, useEffect } from 'react';
import type { DialogueEntry } from '../types/game';

interface ChatPanelProps {
  history: DialogueEntry[];
  onSubmit: (input: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

const SPEAKER_CONFIG: Record<string, { icon: string; name: string; color: string }> = {
  player: { icon: '👑', name: '君主', color: '#ffd700' },
  lion: { icon: '🦁', name: '狮子', color: '#ef4444' },
  fox: { icon: '🦊', name: '狐狸', color: '#f97316' },
  balance: { icon: '⚖️', name: '天平', color: '#22c55e' },
};

export function ChatPanel({ history, onSubmit, isLoading, disabled }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const historyEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    historyEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || disabled) return;

    onSubmit(input.trim());
    setInput('');
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: '#0a0a14',
      borderRadius: '8px',
      border: '1px solid #333',
      overflow: 'hidden',
    }}>
      {/* 对话历史 */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
      }}>
        {history.length === 0 && (
          <div style={{
            color: '#666',
            textAlign: 'center',
            padding: '40px 20px',
            fontSize: '14px',
          }}>
            输入你的第一道政令，开始你的统治...
          </div>
        )}

        {history.map((entry, index) => {
          const config = SPEAKER_CONFIG[entry.speaker] || SPEAKER_CONFIG.player;
          const isPlayer = entry.speaker === 'player';

          return (
            <div
              key={index}
              style={{
                marginBottom: '16px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: isPlayer ? 'flex-end' : 'flex-start',
              }}
            >
              {/* 说话者标签 */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                marginBottom: '4px',
                gap: '4px',
              }}>
                <span style={{ fontSize: '14px' }}>{config.icon}</span>
                <span style={{ color: config.color, fontSize: '12px', fontWeight: 'bold' }}>
                  {config.name}
                </span>
                <span style={{ color: '#555', fontSize: '11px' }}>
                  回合 {entry.turn}
                </span>
              </div>

              {/* 消息气泡 */}
              <div style={{
                maxWidth: '85%',
                padding: '10px 14px',
                borderRadius: '12px',
                backgroundColor: isPlayer ? '#1a3a5f' : '#1a1a2e',
                color: '#e0e0e0',
                fontSize: '14px',
                lineHeight: '1.5',
                whiteSpace: 'pre-wrap',
                border: `1px solid ${isPlayer ? '#2a4a6f' : '#333'}`,
              }}>
                {entry.content}
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div style={{
            textAlign: 'center',
            color: '#888',
            padding: '20px',
          }}>
            <span className="loading-dots">三位顾问正在审议...</span>
          </div>
        )}

        <div ref={historyEndRef} />
      </div>

      {/* 输入区 */}
      <form onSubmit={handleSubmit} style={{
        padding: '16px',
        borderTop: '1px solid #333',
        backgroundColor: '#0f0f1a',
      }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={disabled ? '游戏已结束' : '输入你的政令...'}
            disabled={isLoading || disabled}
            style={{
              flex: 1,
              padding: '12px 16px',
              backgroundColor: '#1a1a2e',
              border: '1px solid #333',
              borderRadius: '8px',
              color: '#fff',
              fontSize: '14px',
              outline: 'none',
            }}
          />
          <button
            type="submit"
            disabled={isLoading || disabled || !input.trim()}
            style={{
              padding: '12px 24px',
              backgroundColor: isLoading || disabled || !input.trim() ? '#333' : '#ffd700',
              color: isLoading || disabled || !input.trim() ? '#666' : '#000',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 'bold',
              cursor: isLoading || disabled || !input.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            {isLoading ? '...' : '发布'}
          </button>
        </div>
      </form>
    </div>
  );
}
