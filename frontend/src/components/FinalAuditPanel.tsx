// 最终审计结果面板 - 浅色主题

import type { FinalAudit } from '../types/game';
import { theme } from '../theme';

interface FinalAuditPanelProps {
  audit: FinalAudit;
  onNewGame: () => void;
}

export function FinalAuditPanel({ audit, onNewGame }: FinalAuditPanelProps) {
  const getReputationColor = (reputation: string) => {
    switch (reputation) {
      case '明君': return theme.status.success;
      case '暴君': return theme.status.error;
      case '骗子': return theme.advisor.fox;
      case '庸主': return theme.text.muted;
      default: return theme.accent.gold;
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
      backgroundColor: theme.bg.primary,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px',
    }}>
      <div style={{
        maxWidth: '800px',
        width: '100%',
        backgroundColor: theme.bg.card,
        borderRadius: '16px',
        border: `1px solid ${theme.border.light}`,
        overflow: 'hidden',
        boxShadow: theme.shadow.lg,
      }}>
        {/* 头部 */}
        <div style={{
          padding: '40px',
          textAlign: 'center',
          borderBottom: `1px solid ${theme.border.light}`,
          background: `linear-gradient(180deg, ${theme.bg.secondary} 0%, ${theme.bg.card} 100%)`,
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
            color: theme.text.secondary,
            fontSize: '16px',
          }}>
            五重试炼完成 - 最终审计报告
          </p>
        </div>

        {/* 总分 */}
        <div style={{
          padding: '32px',
          textAlign: 'center',
          borderBottom: `1px solid ${theme.border.light}`,
        }}>
          <div style={{
            color: theme.accent.gold,
            fontSize: '64px',
            fontWeight: 'bold',
          }}>
            {audit.final_score}
          </div>
          <div style={{
            color: theme.text.secondary,
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
            backgroundColor: theme.bg.secondary,
            borderRadius: '12px',
            padding: '20px',
            border: `1px solid ${theme.border.light}`,
          }}>
            <h3 style={{
              margin: '0 0 16px 0',
              color: theme.accent.goldDark,
              fontSize: '14px',
              fontWeight: '600',
            }}>
              📊 决策统计
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>总决策数</span>
                <span style={{ color: theme.text.primary, fontWeight: '500' }}>{audit.total_decisions}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>暴力决策</span>
                <span style={{ color: theme.status.error, fontWeight: '500' }}>{audit.violent_decisions}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>欺骗决策</span>
                <span style={{ color: theme.advisor.fox, fontWeight: '500' }}>{audit.deceptive_decisions}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>公正决策</span>
                <span style={{ color: theme.status.success, fontWeight: '500' }}>{audit.fair_decisions}</span>
              </div>
            </div>
          </div>

          {/* 承诺统计 */}
          <div style={{
            backgroundColor: theme.bg.secondary,
            borderRadius: '12px',
            padding: '20px',
            border: `1px solid ${theme.border.light}`,
          }}>
            <h3 style={{
              margin: '0 0 16px 0',
              color: theme.accent.goldDark,
              fontSize: '14px',
              fontWeight: '600',
            }}>
              🤝 承诺记录
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>承诺总数</span>
                <span style={{ color: theme.text.primary, fontWeight: '500' }}>{audit.promises_made}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>违背承诺</span>
                <span style={{ color: theme.status.error, fontWeight: '500' }}>{audit.promises_broken}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>承诺可靠度</span>
                <span style={{ color: theme.status.success, fontWeight: '500' }}>{formatPercent(audit.promise_reliability)}</span>
              </div>
            </div>
          </div>

          {/* 把柄与秘密 */}
          <div style={{
            backgroundColor: theme.bg.secondary,
            borderRadius: '12px',
            padding: '20px',
            border: `1px solid ${theme.border.light}`,
          }}>
            <h3 style={{
              margin: '0 0 16px 0',
              color: theme.accent.goldDark,
              fontSize: '14px',
              fontWeight: '600',
            }}>
              🔒 秘密与把柄
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>秘密泄露</span>
                <span style={{ color: theme.status.error, fontWeight: '500' }}>{audit.secrets_leaked} 次</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: theme.text.secondary }}>被握把柄</span>
                <span style={{ color: theme.advisor.fox, fontWeight: '500' }}>{audit.leverages_held} 个</span>
              </div>
            </div>
          </div>

          {/* 比率统计 */}
          <div style={{
            backgroundColor: theme.bg.secondary,
            borderRadius: '12px',
            padding: '20px',
            border: `1px solid ${theme.border.light}`,
          }}>
            <h3 style={{
              margin: '0 0 16px 0',
              color: theme.accent.goldDark,
              fontSize: '14px',
              fontWeight: '600',
            }}>
              📈 行为倾向
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: theme.text.secondary }}>暴力倾向</span>
                  <span style={{ color: theme.status.error, fontWeight: '500' }}>{formatPercent(audit.violence_ratio)}</span>
                </div>
                <div style={{
                  height: '4px',
                  backgroundColor: theme.status.errorBg,
                  borderRadius: '2px',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    width: `${audit.violence_ratio * 100}%`,
                    height: '100%',
                    backgroundColor: theme.status.error,
                  }} />
                </div>
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: theme.text.secondary }}>欺骗倾向</span>
                  <span style={{ color: theme.advisor.fox, fontWeight: '500' }}>{formatPercent(audit.deception_ratio)}</span>
                </div>
                <div style={{
                  height: '4px',
                  backgroundColor: theme.advisor.foxBg,
                  borderRadius: '2px',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    width: `${audit.deception_ratio * 100}%`,
                    height: '100%',
                    backgroundColor: theme.advisor.fox,
                  }} />
                </div>
              </div>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: theme.text.secondary }}>公正倾向</span>
                  <span style={{ color: theme.status.success, fontWeight: '500' }}>{formatPercent(audit.fairness_ratio)}</span>
                </div>
                <div style={{
                  height: '4px',
                  backgroundColor: theme.status.successBg,
                  borderRadius: '2px',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    width: `${audit.fairness_ratio * 100}%`,
                    height: '100%',
                    backgroundColor: theme.status.success,
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
              backgroundColor: theme.accent.gold,
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              fontSize: '16px',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'all 0.2s',
              boxShadow: theme.shadow.sm,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = theme.accent.goldDark;
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = theme.accent.gold;
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            🔄 开始新的统治
          </button>
        </div>
      </div>
    </div>
  );
}
