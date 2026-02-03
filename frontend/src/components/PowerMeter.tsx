// 权力三维显示组件 - 浅色主题

import type { PowerVector } from '../types/game';
import { theme } from '../theme';

interface PowerMeterProps {
  power: PowerVector;
  changes?: { authority: number; fear: number; love: number };
  hideValues?: boolean;
  compact?: boolean;
}

export function PowerMeter({ power, changes, hideValues = false, compact = false }: PowerMeterProps) {
  const renderBar = (
    label: string,
    shortLabel: string,
    value: number,
    change: number | undefined,
    color: string,
    bgColor: string
  ) => {
    const changeText = change !== undefined && change !== 0
      ? `(${change > 0 ? '+' : ''}${change.toFixed(1)})`
      : '';
    const changeColor = change && change > 0 ? theme.status.success : change && change < 0 ? theme.status.error : theme.text.muted;

    return (
      <div style={{ marginBottom: compact ? '8px' : '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
          <span style={{ color: theme.text.secondary, fontSize: compact ? '12px' : '14px' }}>
            {compact ? shortLabel : label}
          </span>
          <span style={{ color: theme.text.primary, fontSize: compact ? '12px' : '14px', fontWeight: '500' }}>
            {hideValues ? '???' : value.toFixed(1)}
            {!hideValues && changeText && !compact && (
              <span style={{ color: changeColor, marginLeft: '4px', fontSize: '12px' }}>
                {changeText}
              </span>
            )}
          </span>
        </div>
        <div style={{
          height: compact ? '4px' : '8px',
          backgroundColor: bgColor,
          borderRadius: '4px',
          overflow: 'hidden',
        }}>
          <div style={{
            height: '100%',
            width: hideValues ? '50%' : `${value}%`,
            backgroundColor: hideValues ? theme.text.muted : color,
            borderRadius: '4px',
            transition: 'width 0.5s ease',
          }} />
        </div>
      </div>
    );
  };

  // 紧凑模式
  if (compact) {
    return (
      <div>
        {renderBar('掌控力', 'A 掌控', power.authority.value, changes?.authority, theme.advisor.lion, theme.advisor.lionBg)}
        {renderBar('畏惧值', 'F 畏惧', power.fear.value, changes?.fear, theme.advisor.fox, theme.advisor.foxBg)}
        {renderBar('爱戴值', 'L 爱戴', power.love.value, changes?.love, theme.advisor.balance, theme.advisor.balanceBg)}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: '8px',
          paddingTop: '8px',
          borderTop: `1px solid ${theme.border.light}`,
        }}>
          <span style={{ color: theme.text.muted, fontSize: '11px' }}>总值</span>
          <span style={{
            color: hideValues ? theme.text.muted : power.total < 100 ? theme.status.error : theme.accent.gold,
            fontSize: '14px',
            fontWeight: 'bold',
          }}>
            {hideValues ? '???' : power.total.toFixed(1)}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      padding: '16px',
      backgroundColor: theme.bg.card,
      borderRadius: '8px',
      border: `1px solid ${theme.border.light}`,
      boxShadow: theme.shadow.sm,
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px',
      }}>
        <h3 style={{ margin: 0, color: theme.accent.goldDark, fontSize: '16px', fontWeight: '600' }}>
          ⚔️ 权力三维
        </h3>
        {hideValues && (
          <span style={{
            fontSize: '11px',
            color: theme.advisor.fox,
            padding: '2px 8px',
            backgroundColor: theme.advisor.foxBg,
            borderRadius: '4px',
          }}>
            🔮 黑箱模式
          </span>
        )}
      </div>

      {renderBar('掌控力 (A)', 'A', power.authority.value, changes?.authority, theme.advisor.lion, theme.advisor.lionBg)}
      {renderBar('畏惧值 (F)', 'F', power.fear.value, changes?.fear, theme.advisor.fox, theme.advisor.foxBg)}
      {renderBar('爱戴值 (L)', 'L', power.love.value, changes?.love, theme.advisor.balance, theme.advisor.balanceBg)}

      <div style={{
        marginTop: '16px',
        paddingTop: '12px',
        borderTop: `1px solid ${theme.border.light}`,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <span style={{ color: theme.text.muted, fontSize: '14px' }}>总值</span>
        <span style={{
          color: hideValues ? theme.text.muted : power.total < 100 ? theme.status.error : theme.accent.gold,
          fontSize: '18px',
          fontWeight: 'bold',
        }}>
          {hideValues ? '???' : power.total.toFixed(1)}
        </span>
      </div>

      {!hideValues && power.total < 100 && (
        <div style={{
          marginTop: '8px',
          padding: '8px',
          backgroundColor: theme.status.errorBg,
          borderRadius: '4px',
          color: theme.status.error,
          fontSize: '12px',
          textAlign: 'center',
          border: `1px solid ${theme.status.error}30`,
        }}>
          ⚠️ 总值低于100，统治岌岌可危！
        </div>
      )}
    </div>
  );
}
