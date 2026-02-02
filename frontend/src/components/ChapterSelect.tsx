// 关卡选择组件

import type { ChapterInfo, GameState } from '../types/game';

interface ChapterSelectProps {
  intro: string;
  chapters: ChapterInfo[];
  gameState: GameState;
  onSelectChapter: (chapterId: string) => void;
  isLoading: boolean;
  mountainView?: string;
}

export function ChapterSelect({
  intro,
  chapters,
  gameState,
  onSelectChapter,
  isLoading,
  mountainView,
}: ChapterSelectProps) {
  const getComplexityStars = (complexity: number) => {
    return '★'.repeat(complexity) + '☆'.repeat(5 - complexity);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return '#4ade80';
      case 'active': return '#ffd700';
      case 'completed': return '#60a5fa';
      case 'failed': return '#ef4444';
      default: return '#555';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'available': return '可进入';
      case 'active': return '进行中';
      case 'completed': return '已通关';
      case 'failed': return '已失败';
      default: return '锁定';
    }
  };

  return (
    <div style={{
      padding: '40px',
      maxWidth: '1200px',
      margin: '0 auto',
    }}>
      {/* 山峰视图（如果有）*/}
      {mountainView && (
        <div style={{
          backgroundColor: '#0f0f1a',
          border: '1px solid #333',
          borderRadius: '12px',
          padding: '16px',
          marginBottom: '24px',
          fontFamily: 'monospace',
          overflow: 'auto',
        }}>
          <pre style={{
            color: '#00ff88',
            whiteSpace: 'pre',
            margin: 0,
            fontSize: '11px',
            lineHeight: '1.3',
          }}>
            {mountainView}
          </pre>
        </div>
      )}

      {/* 游戏介绍 */}
      <div style={{
        backgroundColor: '#0f0f1a',
        border: '1px solid #333',
        borderRadius: '12px',
        padding: '24px',
        marginBottom: '32px',
        fontFamily: 'monospace',
      }}>
        <pre style={{
          color: '#ffd700',
          whiteSpace: 'pre-wrap',
          margin: 0,
          fontSize: '12px',
          lineHeight: '1.6',
        }}>
          {intro}
        </pre>
      </div>

      {/* 权力状态概览 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '16px',
        marginBottom: '32px',
      }}>
        <div style={{
          backgroundColor: '#1a1a2e',
          borderRadius: '8px',
          padding: '16px',
          textAlign: 'center',
          border: '1px solid #333',
        }}>
          <div style={{ color: '#888', fontSize: '12px', marginBottom: '8px' }}>掌控力 (A)</div>
          <div style={{ color: '#ef4444', fontSize: '24px', fontWeight: 'bold' }}>
            {gameState.power.authority.value.toFixed(0)}%
          </div>
        </div>
        <div style={{
          backgroundColor: '#1a1a2e',
          borderRadius: '8px',
          padding: '16px',
          textAlign: 'center',
          border: '1px solid #333',
        }}>
          <div style={{ color: '#888', fontSize: '12px', marginBottom: '8px' }}>畏惧值 (F)</div>
          <div style={{ color: '#a855f7', fontSize: '24px', fontWeight: 'bold' }}>
            {gameState.power.fear.value.toFixed(0)}%
          </div>
        </div>
        <div style={{
          backgroundColor: '#1a1a2e',
          borderRadius: '8px',
          padding: '16px',
          textAlign: 'center',
          border: '1px solid #333',
        }}>
          <div style={{ color: '#888', fontSize: '12px', marginBottom: '8px' }}>爱戴值 (L)</div>
          <div style={{ color: '#22c55e', fontSize: '24px', fontWeight: 'bold' }}>
            {gameState.power.love.value.toFixed(0)}%
          </div>
        </div>
        <div style={{
          backgroundColor: '#1a1a2e',
          borderRadius: '8px',
          padding: '16px',
          textAlign: 'center',
          border: '1px solid #333',
        }}>
          <div style={{ color: '#888', fontSize: '12px', marginBottom: '8px' }}>信用积分</div>
          <div style={{ color: '#ffd700', fontSize: '24px', fontWeight: 'bold' }}>
            {gameState.credit_score.toFixed(0)}
          </div>
        </div>
      </div>

      {/* 关卡选择 */}
      <h2 style={{
        color: '#ffd700',
        fontSize: '20px',
        marginBottom: '24px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
      }}>
        📜 选择关卡
      </h2>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
        gap: '20px',
      }}>
        {chapters.map((chapter) => (
          <div
            key={chapter.id}
            style={{
              backgroundColor: '#1a1a2e',
              borderRadius: '12px',
              padding: '24px',
              border: `2px solid ${chapter.status === 'available' ? '#4ade80' : '#333'}`,
              cursor: chapter.status === 'available' || chapter.status === 'active' ? 'pointer' : 'not-allowed',
              opacity: chapter.status === 'locked' ? 0.5 : 1,
              transition: 'all 0.2s',
            }}
            onClick={() => {
              if ((chapter.status === 'available' || chapter.status === 'active') && !isLoading) {
                onSelectChapter(chapter.id);
              }
            }}
          >
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              marginBottom: '12px',
            }}>
              <div>
                <h3 style={{
                  margin: 0,
                  color: '#fff',
                  fontSize: '18px',
                }}>
                  {chapter.name}
                </h3>
                {chapter.subtitle && (
                  <div style={{
                    color: '#888',
                    fontSize: '13px',
                    marginTop: '4px',
                  }}>
                    {chapter.subtitle}
                  </div>
                )}
              </div>
              <span style={{
                color: getStatusColor(chapter.status),
                fontSize: '12px',
                padding: '4px 8px',
                backgroundColor: `${getStatusColor(chapter.status)}20`,
                borderRadius: '4px',
              }}>
                {getStatusText(chapter.status)}
              </span>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}>
              <span style={{
                color: '#ffd700',
                fontSize: '14px',
                letterSpacing: '2px',
              }}>
                {getComplexityStars(chapter.complexity)}
              </span>
              <span style={{
                color: '#666',
                fontSize: '12px',
              }}>
                难度 {chapter.complexity}/5
              </span>
            </div>

            {(chapter.status === 'available' || chapter.status === 'active') && (
              <button
                disabled={isLoading}
                style={{
                  marginTop: '16px',
                  width: '100%',
                  padding: '12px',
                  backgroundColor: isLoading ? '#333' : '#4ade80',
                  color: isLoading ? '#888' : '#000',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  cursor: isLoading ? 'not-allowed' : 'pointer',
                }}
              >
                {isLoading ? '加载中...' : '▶ 开始挑战'}
              </button>
            )}
          </div>
        ))}

        {/* 锁定的关卡提示 */}
        {chapters.length === 1 && (
          <div style={{
            backgroundColor: '#1a1a2e',
            borderRadius: '12px',
            padding: '24px',
            border: '2px dashed #333',
            opacity: 0.6,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '150px',
          }}>
            <div style={{ fontSize: '32px', marginBottom: '12px' }}>🔒</div>
            <div style={{ color: '#666', fontSize: '14px', textAlign: 'center' }}>
              通过当前关卡解锁更多内容
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
