// 机器人顾问卡片组件

interface RobotCardProps {
  type: 'lion' | 'fox' | 'balance';
  response: string;
  relation?: { trust: number; hatred: number; is_hostile: boolean };
  assessment?: string;
}

const ROBOT_CONFIG = {
  lion: {
    icon: '🦁',
    name: '狮子',
    title: '武力与威慑',
    color: '#ef4444',
    bgColor: '#2d1515',
  },
  fox: {
    icon: '🦊',
    name: '狐狸',
    title: '权谋与狡诈',
    color: '#f97316',
    bgColor: '#2d2015',
  },
  balance: {
    icon: '⚖️',
    name: '天平',
    title: '正义与民心',
    color: '#22c55e',
    bgColor: '#152d1a',
  },
};

export function RobotCard({ type, response, relation, assessment }: RobotCardProps) {
  const config = ROBOT_CONFIG[type];

  return (
    <div style={{
      padding: '16px',
      backgroundColor: config.bgColor,
      borderRadius: '8px',
      border: `1px solid ${config.color}30`,
      marginBottom: '12px',
    }}>
      {/* 头部 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        marginBottom: '12px',
      }}>
        <span style={{ fontSize: '24px', marginRight: '8px' }}>{config.icon}</span>
        <div>
          <div style={{ color: config.color, fontWeight: 'bold', fontSize: '16px' }}>
            {config.name}
          </div>
          <div style={{ color: '#888', fontSize: '12px' }}>
            {config.title}
          </div>
        </div>

        {/* 关系指示器 */}
        {relation && (
          <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
            <div style={{
              fontSize: '11px',
              color: relation.trust > 0 ? '#22c55e' : relation.trust < 0 ? '#ef4444' : '#888',
            }}>
              信任: {relation.trust > 0 ? '+' : ''}{relation.trust.toFixed(0)}
            </div>
            {relation.is_hostile && (
              <div style={{ fontSize: '11px', color: '#ef4444' }}>
                ⚠️ 敌对
              </div>
            )}
          </div>
        )}
      </div>

      {/* 回应内容 */}
      <div style={{
        color: '#e0e0e0',
        fontSize: '14px',
        lineHeight: '1.6',
        padding: '12px',
        backgroundColor: '#00000030',
        borderRadius: '4px',
        whiteSpace: 'pre-wrap',
      }}>
        {response || '...'}
      </div>

      {/* 评估摘要 */}
      {assessment && (
        <div style={{
          marginTop: '8px',
          fontSize: '12px',
          color: '#888',
          fontStyle: 'italic',
        }}>
          {assessment}
        </div>
      )}
    </div>
  );
}
