// 事件弹窗组件

import type { GameEvent } from '../types/game';

interface EventModalProps {
  event: GameEvent;
  onChoice: (choiceId: string) => void;
  isLoading: boolean;
}

const EVENT_TYPE_CONFIG: Record<string, { icon: string; color: string }> = {
  riot: { icon: '🔥', color: '#ef4444' },
  coup: { icon: '⚔️', color: '#dc2626' },
  rebellion: { icon: '🏴', color: '#b91c1c' },
  famine: { icon: '🌾', color: '#f59e0b' },
  war: { icon: '🛡️', color: '#6366f1' },
  plague: { icon: '☠️', color: '#10b981' },
  conspiracy: { icon: '🗡️', color: '#8b5cf6' },
  betrayal: { icon: '💔', color: '#ec4899' },
  crisis: { icon: '📉', color: '#f97316' },
  invasion: { icon: '⚔️', color: '#ef4444' },
};

export function EventModal({ event, onChoice, isLoading }: EventModalProps) {
  const config = EVENT_TYPE_CONFIG[event.type] || { icon: '⚠️', color: '#ffd700' };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px',
    }}>
      <div style={{
        backgroundColor: '#1a1a2e',
        borderRadius: '12px',
        border: `2px solid ${config.color}`,
        maxWidth: '600px',
        width: '100%',
        overflow: 'hidden',
        boxShadow: `0 0 40px ${config.color}40`,
      }}>
        {/* 头部 */}
        <div style={{
          padding: '20px 24px',
          backgroundColor: `${config.color}20`,
          borderBottom: `1px solid ${config.color}40`,
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}>
            <span style={{ fontSize: '32px' }}>{config.icon}</span>
            <div>
              <div style={{
                color: config.color,
                fontSize: '12px',
                textTransform: 'uppercase',
                letterSpacing: '2px',
                marginBottom: '4px',
              }}>
                突发事件
              </div>
              <div style={{
                color: '#fff',
                fontSize: '20px',
                fontWeight: 'bold',
              }}>
                {event.title}
              </div>
            </div>
          </div>
        </div>

        {/* 事件描述 */}
        <div style={{
          padding: '24px',
          color: '#e0e0e0',
          fontSize: '15px',
          lineHeight: '1.8',
          whiteSpace: 'pre-wrap',
        }}>
          {event.narration}
        </div>

        {/* 选项 */}
        <div style={{
          padding: '0 24px 24px',
        }}>
          <div style={{
            color: '#888',
            fontSize: '12px',
            marginBottom: '12px',
            textTransform: 'uppercase',
            letterSpacing: '1px',
          }}>
            你的抉择
          </div>

          {event.choices.map((choice) => (
            <button
              key={choice.id}
              onClick={() => onChoice(choice.id)}
              disabled={isLoading}
              style={{
                width: '100%',
                padding: '14px 20px',
                marginBottom: '10px',
                backgroundColor: '#0a0a14',
                border: '1px solid #333',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '14px',
                textAlign: 'left',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                opacity: isLoading ? 0.5 : 1,
              }}
              onMouseEnter={(e) => {
                if (!isLoading) {
                  e.currentTarget.style.borderColor = config.color;
                  e.currentTarget.style.backgroundColor = '#1a1a2e';
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#333';
                e.currentTarget.style.backgroundColor = '#0a0a14';
              }}
            >
              <div style={{ fontWeight: '500', marginBottom: '4px' }}>
                {choice.text}
              </div>
              <div style={{
                fontSize: '12px',
                color: '#666',
                display: 'flex',
                gap: '12px',
              }}>
                {choice.impact.authority !== 0 && (
                  <span style={{ color: choice.impact.authority > 0 ? '#3b82f6' : '#ef4444' }}>
                    A: {choice.impact.authority > 0 ? '+' : ''}{choice.impact.authority}
                  </span>
                )}
                {choice.impact.fear !== 0 && (
                  <span style={{ color: choice.impact.fear > 0 ? '#ef4444' : '#22c55e' }}>
                    F: {choice.impact.fear > 0 ? '+' : ''}{choice.impact.fear}
                  </span>
                )}
                {choice.impact.love !== 0 && (
                  <span style={{ color: choice.impact.love > 0 ? '#22c55e' : '#ef4444' }}>
                    L: {choice.impact.love > 0 ? '+' : ''}{choice.impact.love}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
