// 权力三维显示组件

import type { PowerVector } from '../types/game';

interface PowerMeterProps {
  power: PowerVector;
  changes?: { authority: number; fear: number; love: number };
  hideValues?: boolean;
}

export function PowerMeter({ power, changes, hideValues = false }: PowerMeterProps) {
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
            {hideValues ? '???' : value.toFixed(1)}
            {!hideValues && changeText && (
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
            width: hideValues ? '50%' : `${value}%`,
            backgroundColor: hideValues ? '#666' : color,
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
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '16px',
      }}>
        <h3 style={{ margin: 0, color: '#ffd700', fontSize: '16px' }}>
          ⚔️ 权力三维
        </h3>
        {hideValues && (
          <span style={{
            fontSize: '11px',
            color: '#a855f7',
            padding: '2px 8px',
            backgroundColor: '#a855f720',
            borderRadius: '4px',
          }}>
            🔮 黑箱模式
          </span>
        )}
      </div>

      {renderBar(
        '掌控力 (A)',
        power.authority.value,
        changes?.authority,
        '#ef4444',
        '#5f1e1e'
      )}

      {renderBar(
        '畏惧值 (F)',
        power.fear.value,
        changes?.fear,
        '#a855f7',
        '#3f1e5f'
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
          color: hideValues ? '#666' : power.total < 100 ? '#ef4444' : '#ffd700',
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
          backgroundColor: '#ef444420',
          borderRadius: '4px',
          color: '#ef4444',
          fontSize: '12px',
          textAlign: 'center',
        }}>
          ⚠️ 总值低于100，统治岌岌可危！
        </div>
      )}
    </div>
  );
}
