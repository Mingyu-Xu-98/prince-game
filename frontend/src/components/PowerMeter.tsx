// 权力三维显示组件

import type { PowerVector } from '../types/game';

interface PowerMeterProps {
  power: PowerVector;
  changes?: { authority: number; fear: number; love: number };
}

export function PowerMeter({ power, changes }: PowerMeterProps) {
  const renderBar = (
    label: string,
    value: number,
    change: number | undefined,
    color: string,
    bgColor: string
  ) => {
    const changeText = change !== undefined && change !== 0
      ? `(${change > 0 ? '+' : ''}${change.toFixed(1)})`
      : '';
    const changeColor = change && change > 0 ? '#4ade80' : change && change < 0 ? '#f87171' : '#888';

    return (
      <div style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
          <span style={{ color: '#ccc', fontSize: '14px' }}>{label}</span>
          <span style={{ color: '#fff', fontSize: '14px' }}>
            {value.toFixed(1)}
            {changeText && (
              <span style={{ color: changeColor, marginLeft: '4px', fontSize: '12px' }}>
                {changeText}
              </span>
            )}
          </span>
        </div>
        <div style={{
          height: '8px',
          backgroundColor: bgColor,
          borderRadius: '4px',
          overflow: 'hidden',
        }}>
          <div style={{
            height: '100%',
            width: `${value}%`,
            backgroundColor: color,
            borderRadius: '4px',
            transition: 'width 0.5s ease',
          }} />
        </div>
      </div>
    );
  };

  return (
    <div style={{
      padding: '16px',
      backgroundColor: '#1a1a2e',
      borderRadius: '8px',
      border: '1px solid #333',
    }}>
      <h3 style={{ margin: '0 0 16px 0', color: '#ffd700', fontSize: '16px' }}>
        ⚔️ 权力三维
      </h3>

      {renderBar(
        '掌控力 (A)',
        power.authority.value,
        changes?.authority,
        '#3b82f6',
        '#1e3a5f'
      )}

      {renderBar(
        '畏惧值 (F)',
        power.fear.value,
        changes?.fear,
        '#ef4444',
        '#5f1e1e'
      )}

      {renderBar(
        '爱戴值 (L)',
        power.love.value,
        changes?.love,
        '#22c55e',
        '#1e5f2f'
      )}

      <div style={{
        marginTop: '16px',
        paddingTop: '12px',
        borderTop: '1px solid #333',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <span style={{ color: '#888', fontSize: '14px' }}>总值</span>
        <span style={{
          color: power.total < 100 ? '#ef4444' : '#ffd700',
          fontSize: '18px',
          fontWeight: 'bold',
        }}>
          {power.total.toFixed(1)}
        </span>
      </div>
    </div>
  );
}
