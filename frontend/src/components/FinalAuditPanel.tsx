// 最终审计结果面板

import type { FinalAudit } from '../types/game';

interface FinalAuditPanelProps {
  audit: FinalAudit;
  onNewGame: () => void;
}

export function FinalAuditPanel({ audit, onNewGame }: FinalAuditPanelProps) {
  const getReputationColor = (reputation: string) => {
    switch (reputation) {
      case '明君': return '#4ade80';
      case '暴君': return '#ef4444';
      case '骗子': return '#a855f7';
      case '庸主': return '#888';
      default: return '#ffd700';
    }
  };

  const getReputationEmoji = (reputation: string) => {
    switch (reputation) {
      case '明君': return '👑';
      case '暴君': return '🗡️';
      case '骗子': return '🎭';
      case '庸主': return '😐';
      default: return '⚖️';
    }
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(1)}%`;

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0a0a14',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px',
    }}>
      <div style={{
        maxWidth: '800px',
        width: '100%',
        backgroundColor: '#0f0f1a',
        borderRadius: '16px',
        border: '2px solid #333',
        overflow: 'hidden',
      }}>
        {/* 头部 */}
        <div style={{
          padding: '40px',
          textAlign: 'center',
          borderBottom: '1px solid #333',
          background: 'linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%)',
        }}>
          <div style={{
            fontSize: '64px',
            marginBottom: '16px',
          }}>
            {getReputationEmoji(audit.reputation)}
          </div>
          <h1 style={{
            margin: 0,
            color: getReputationColor(audit.reputation),
            fontSize: '36px',
            fontWeight: 'bold',
          }}>
            {audit.reputation}
          </h1>
          <p style={{
            margin: '12px 0 0 0',
            color: '#888',
            fontSize: '16px',
          }}>
            五重试炼完成 - 最终审计报告
          </p>
        </div>

        {/* 总分 */}
        <div style={{
          padding: '32px',
          textAlign: 'center',
          borderBottom: '1px solid #333',
        }}>
          <div style={{
            color: '#ffd700',
            fontSize: '64px',
            fontWeight: 'bold',
          }}>
            {audit.final_score}
          </div>
          <div style={{
            color: '#888',
            fontSize: '14px',
          }}>
            最终评分
          </div>
        </div>

        {/* 统计数据 */}
        <div style={{
          padding: '32px',
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '24px',
        }}>
          {/* 决策统计 */}
          <div style={{
            backgroundColor: '#1a1a2e',
            borderRadius: '12px',
            padding: '20px',
          }}>
            <h3 style={{
              margin: '0 0 16px 0',
              color: '#ffd700',
              fontSize: '14px',
            }}>
              📊 决策统计
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>总决策数</span>
                <span style={{ color: '#fff' }}>{audit.total_decisions}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>暴力决策</span>
                <span style={{ color: '#ef4444' }}>{audit.violent_decisions}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>欺骗决策</span>
                <span style={{ color: '#a855f7' }}>{audit.deceptive_decisions}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>公正决策</span>
                <span style={{ color: '#4ade80' }}>{audit.fair_decisions}</span>
              </div>
            </div>
          </div>

          {/* 承诺统计 */}
          <div style={{
            backgroundColor: '#1a1a2e',
            borderRadius: '12px',
            padding: '20px',
          }}>
            <h3 style={{
              margin: '0 0 16px 0',
              color: '#ffd700',
              fontSize: '14px',
            }}>
              🤝 承诺记录
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>承诺总数</span>
                <span style={{ color: '#fff' }}>{audit.promises_made}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>违背承诺</span>
                <span style={{ color: '#ef4444' }}>{audit.promises_broken}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>承诺可靠度</span>
                <span style={{ color: '#4ade80' }}>{formatPercent(audit.promise_reliability)}</span>
              </div>
            </div>
          </div>

          {/* 把柄与秘密 */}
          <div style={{
            backgroundColor: '#1a1a2e',
            borderRadius: '12px',
            padding: '20px',
          }}>
            <h3 style={{
              margin: '0 0 16px 0',
              color: '#ffd700',
              fontSize: '14px',
            }}>
              🔒 秘密与把柄
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>秘密泄露</span>
                <span style={{ color: '#ef4444' }}>{audit.secrets_leaked} 次</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>被握把柄</span>
                <span style={{ color: '#a855f7' }}>{audit.leverages_held} 个</span>
              </div>
            </div>
          </div>

          {/* 比率统计 */}
          <div style={{
            backgroundColor: '#1a1a2e',
            borderRadius: '12px',
            padding: '20px',
          }}>
            <h3 style={{
              margin: '0 0 16px 0',
              color: '#ffd700',
              fontSize: '14px',
            }}>
              📈 行为倾向
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: '#888' }}>暴力倾向</span>
                  <span style={{ color: '#ef4444' }}>{formatPercent(audit.violence_ratio)}</span>
                </div>
                <div style={{
                  height: '4px',
                  backgroundColor: '#333',
                  borderRadius: '2px',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    width: `${audit.violence_ratio * 100}%`,
                    height: '100%',
                    backgroundColor: '#ef4444',
                  }} />
                </div>
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: '#888' }}>欺骗倾向</span>
                  <span style={{ color: '#a855f7' }}>{formatPercent(audit.deception_ratio)}</span>
                </div>
                <div style={{
                  height: '4px',
                  backgroundColor: '#333',
                  borderRadius: '2px',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    width: `${audit.deception_ratio * 100}%`,
                    height: '100%',
                    backgroundColor: '#a855f7',
                  }} />
                </div>
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: '#888' }}>公正倾向</span>
                  <span style={{ color: '#4ade80' }}>{formatPercent(audit.fairness_ratio)}</span>
                </div>
                <div style={{
                  height: '4px',
                  backgroundColor: '#333',
                  borderRadius: '2px',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    width: `${audit.fairness_ratio * 100}%`,
                    height: '100%',
                    backgroundColor: '#4ade80',
                  }} />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 底部按钮 */}
        <div style={{
          padding: '24px 32px 32px',
        }}>
          <button
            onClick={onNewGame}
            style={{
              width: '100%',
              padding: '16px',
              backgroundColor: '#ffd700',
              color: '#000',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: 'bold',
              cursor: 'pointer',
            }}
          >
            🔄 开始新的统治
          </button>
        </div>
      </div>
    </div>
  );
}
