// 攀登式关卡选择组件 - 浅色主题

import { useState } from 'react';
import type { ChapterInfo, GameState, PendingConsequence } from '../types/game';
import { theme } from '../theme';

interface ChapterSelectProps {
  intro: string;
  chapters: ChapterInfo[];
  gameState: GameState;
  onSelectChapter: (chapterId: string) => void;
  isLoading: boolean;
  mountainView?: string;
  apiKey?: string;
  onApiKeyChange?: (key: string) => void;
  model?: string;
  onModelChange?: (model: string) => void;
  onExit?: () => void;
  pendingConsequences?: PendingConsequence[];
  onNewGame?: () => void;  // 新游戏回调
}

const AVAILABLE_MODELS = [
  { id: '', label: '默认模型' },
  { id: 'anthropic/claude-3.5-sonnet', label: 'Claude 3.5 Sonnet' },
  { id: 'anthropic/claude-sonnet-4', label: 'Claude Sonnet 4' },
  { id: 'openai/gpt-4-turbo', label: 'GPT-4 Turbo' },
  { id: 'openai/gpt-4o', label: 'GPT-4o' },
  { id: 'google/gemini-2.0-flash-001', label: 'Gemini 2.0 Flash' },
];

// 关卡配置 - 更新为浅色主题颜色
const CHAPTER_CONFIG: Record<string, { icon: string; theme: string; color: string }> = {
  chapter_1: { icon: '💰', theme: '权力的入场券', color: '#38A169' },
  chapter_2: { icon: '🦠', theme: '情感与理智', color: '#3182CE' },
  chapter_3: { icon: '⚔️', theme: '外交博弈', color: '#D69E2E' },
  chapter_4: { icon: '🗡️', theme: '内部博弈', color: '#E53E3E' },
  chapter_5: { icon: '⚖️', theme: '终极审判', color: '#805AD5' },
};

export function ChapterSelect({
  chapters,
  gameState,
  onSelectChapter,
  isLoading,
  apiKey,
  onApiKeyChange,
  model,
  onModelChange,
  onExit,
  pendingConsequences = [],
  onNewGame,
}: ChapterSelectProps) {
  const [showSettings, setShowSettings] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);

  const getStatusInfo = (status: string) => {
    switch (status) {
      case 'available': return { text: '可挑战', color: theme.status.success, canClick: true };
      case 'active': return { text: '进行中', color: theme.status.warning, canClick: true };
      case 'completed': return { text: '已通关', color: theme.status.info, canClick: false };
      case 'failed': return { text: '已失败', color: theme.status.error, canClick: false };
      default: return { text: '未解锁', color: theme.text.muted, canClick: false };
    }
  };

  // 构建完整的5关数据
  const allChapters = [1, 2, 3, 4, 5].map(num => {
    const id = `chapter_${num}`;
    const existing = chapters.find(c => c.id === id);
    const config = CHAPTER_CONFIG[id];

    return {
      id,
      num,
      name: existing?.name || ['空饷危机', '瘟疫与流言', '和亲还是战争', '影子议会的背叛', '民众的审判'][num - 1],
      subtitle: existing?.subtitle || config.theme,
      complexity: existing?.complexity || num,
      status: existing?.status || 'locked',
      ...config,
    };
  });

  return (
    <div className="chapter-select-container">
      {/* 背景山脉 - 浅色版本 */}
      <div className="mountain-bg">
        <svg viewBox="0 0 1200 800" preserveAspectRatio="xMidYMax slice">
          <defs>
            <linearGradient id="mountainGrad1" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#E8DCC8" />
              <stop offset="100%" stopColor="#D4C4A8" />
            </linearGradient>
            <linearGradient id="mountainGrad2" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#D4C4A8" />
              <stop offset="100%" stopColor="#C9B896" />
            </linearGradient>
          </defs>
          <polygon points="0,800 200,400 400,600 600,200 800,500 1000,300 1200,800" fill="url(#mountainGrad1)" />
          <polygon points="0,800 300,500 500,650 700,350 900,550 1200,400 1200,800" fill="url(#mountainGrad2)" opacity="0.5" />
        </svg>
      </div>

      {/* 累积影响警告 */}
      {pendingConsequences.length > 0 && (
        <div style={{
          position: 'relative',
          zIndex: 10,
          padding: '12px 40px',
          backgroundColor: '#FEF3C7',
          borderBottom: `1px solid ${theme.accent.gold}40`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '12px',
        }}>
          <span style={{ fontSize: '18px' }}>⚠️</span>
          <span style={{ color: '#92400E', fontSize: '13px' }}>
            你有 <strong>{pendingConsequences.length}</strong> 项未处理的政令影响正在累积，
            它们可能会在后续关卡中以更严重的形式爆发！
          </span>
          <span style={{
            padding: '4px 10px',
            backgroundColor: '#F59E0B',
            color: '#FFFFFF',
            borderRadius: '4px',
            fontSize: '11px',
            fontWeight: 'bold',
          }}>
            {pendingConsequences.filter(c => c.consequence.severity === 'critical' || c.consequence.severity === 'high').length} 项严重
          </span>
        </div>
      )}

      {/* 顶部信息栏 */}
      <header className="top-bar">
        <div className="game-info">
          {/* 退出按钮 */}
          {onExit && (
            <button
              onClick={onExit}
              style={{
                padding: '8px 12px',
                backgroundColor: 'transparent',
                border: `1px solid ${theme.border.medium}`,
                borderRadius: '6px',
                color: theme.text.secondary,
                fontSize: '12px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                transition: 'all 0.2s',
                marginRight: '12px',
              }}
            >
              ← 退出
            </button>
          )}
          <h1 className="game-title">👁️ 影子执政者</h1>
          <span className="game-subtitle">五重试炼</span>
        </div>
        <div className="player-stats">
          <div className="stat-item">
            <span className="stat-label">掌控力</span>
            <span className="stat-value" style={{ color: theme.advisor.lion }}>{gameState.power.authority.value.toFixed(0)}%</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">畏惧值</span>
            <span className="stat-value" style={{ color: theme.advisor.fox }}>{gameState.power.fear.value.toFixed(0)}%</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">爱戴值</span>
            <span className="stat-value" style={{ color: theme.advisor.balance }}>{gameState.power.love.value.toFixed(0)}%</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <span className="stat-label">信用</span>
            <span className="stat-value" style={{ color: theme.accent.gold }}>{gameState.credit_score.toFixed(0)}</span>
          </div>
          {/* 新游戏按钮 */}
          {onNewGame && (
            <button
              onClick={onNewGame}
              style={{
                padding: '8px 16px',
                marginLeft: '16px',
                backgroundColor: 'transparent',
                border: `1px solid ${theme.border.medium}`,
                borderRadius: '6px',
                color: theme.text.secondary,
                fontSize: '12px',
                cursor: 'pointer',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
              title="重新开始新游戏"
            >
              🔄 新游戏
            </button>
          )}
          {/* 设置按钮 */}
          {onApiKeyChange && (
            <div style={{ position: 'relative', marginLeft: '8px' }}>
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="settings-btn"
                style={{
                  padding: '8px 16px',
                  backgroundColor: showSettings ? theme.bg.secondary : 'transparent',
                  border: `1px solid ${showSettings ? theme.accent.gold : theme.border.medium}`,
                  borderRadius: '6px',
                  color: showSettings ? theme.accent.goldDark : theme.text.secondary,
                  fontSize: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                ⚙️ 设置
              </button>
              {showSettings && (
                <div style={{
                  position: 'absolute',
                  top: '50px',
                  right: '0',
                  width: '320px',
                  background: theme.bg.card,
                  border: `1px solid ${theme.border.medium}`,
                  borderRadius: '12px',
                  padding: '20px',
                  boxShadow: theme.shadow.lg,
                  zIndex: 200,
                }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '16px',
                    color: theme.text.primary,
                    fontSize: '14px',
                    fontWeight: '600',
                  }}>
                    <span>⚙️ API 配置</span>
                    <button
                      onClick={() => setShowSettings(false)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: theme.text.muted,
                        fontSize: '20px',
                        cursor: 'pointer',
                        padding: '0 4px',
                      }}
                    >×</button>
                  </div>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', fontSize: '12px', color: theme.text.secondary, marginBottom: '6px' }}>
                      OpenRouter API Key
                    </label>
                    <div style={{ position: 'relative' }}>
                      <input
                        type={showApiKey ? 'text' : 'password'}
                        value={apiKey || ''}
                        onChange={(e) => onApiKeyChange(e.target.value)}
                        placeholder="sk-or-..."
                        style={{
                          width: '100%',
                          padding: '12px 40px 12px 14px',
                          background: theme.bg.input,
                          border: `1px solid ${theme.border.medium}`,
                          borderRadius: '8px',
                          color: theme.text.primary,
                          fontSize: '13px',
                          outline: 'none',
                          boxSizing: 'border-box',
                        }}
                      />
                      <button
                        type="button"
                        onClick={() => setShowApiKey(!showApiKey)}
                        style={{
                          position: 'absolute',
                          right: '10px',
                          top: '50%',
                          transform: 'translateY(-50%)',
                          background: 'none',
                          border: 'none',
                          color: theme.text.muted,
                          cursor: 'pointer',
                          fontSize: '14px',
                        }}
                      >
                        {showApiKey ? '🙈' : '👁️'}
                      </button>
                    </div>
                  </div>
                  {onModelChange && (
                    <div>
                      <label style={{ display: 'block', fontSize: '12px', color: theme.text.secondary, marginBottom: '6px' }}>
                        AI 模型
                      </label>
                      <select
                        value={model || ''}
                        onChange={(e) => onModelChange(e.target.value)}
                        style={{
                          width: '100%',
                          padding: '12px 14px',
                          background: theme.bg.input,
                          border: `1px solid ${theme.border.medium}`,
                          borderRadius: '8px',
                          color: theme.text.primary,
                          fontSize: '13px',
                          outline: 'none',
                          cursor: 'pointer',
                        }}
                      >
                        {AVAILABLE_MODELS.map((m) => (
                          <option key={m.id} value={m.id}>{m.label}</option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      {/* 攀登路径 */}
      <div className="climbing-path">
        {/* 路径连线 */}
        <svg className="path-lines" viewBox="0 0 400 700" preserveAspectRatio="xMidYMid meet">
          <path
            d="M200,650 C200,580 120,520 200,450 C280,380 120,320 200,250 C280,180 120,120 200,50"
            fill="none"
            stroke="#D4C4A8"
            strokeWidth="3"
            strokeDasharray="10,10"
          />
          {/* 发光路径 */}
          <path
            d="M200,650 C200,580 120,520 200,450 C280,380 120,320 200,250 C280,180 120,120 200,50"
            fill="none"
            stroke="url(#pathGlow)"
            strokeWidth="2"
            opacity="0.7"
          />
          <defs>
            <linearGradient id="pathGlow" x1="0%" y1="100%" x2="0%" y2="0%">
              <stop offset="0%" stopColor="#38A169" />
              <stop offset="50%" stopColor="#D69E2E" />
              <stop offset="100%" stopColor="#805AD5" />
            </linearGradient>
          </defs>
        </svg>

        {/* 关卡节点 */}
        <div className="chapter-nodes">
          {allChapters.map((chapter, index) => {
            const statusInfo = getStatusInfo(chapter.status);
            const yPosition = 85 - (index * 17); // 从下往上
            const xOffset = index % 2 === 0 ? -80 : 80; // 左右交错

            return (
              <div
                key={chapter.id}
                className={`chapter-node ${chapter.status} ${statusInfo.canClick ? 'clickable' : ''}`}
                style={{
                  top: `${yPosition}%`,
                  left: `calc(50% + ${xOffset}px)`,
                  '--chapter-color': chapter.color,
                } as React.CSSProperties}
                onClick={() => statusInfo.canClick && !isLoading && onSelectChapter(chapter.id)}
              >
                {/* 光环效果 */}
                {chapter.status === 'available' && (
                  <div className="node-glow" />
                )}

                {/* 节点主体 */}
                <div className="node-body">
                  <div className="node-icon">{chapter.icon}</div>
                  <div className="node-number">{chapter.num}</div>
                </div>

                {/* 信息卡片 */}
                <div className="node-info">
                  <h3 className="chapter-name">{chapter.name}</h3>
                  <p className="chapter-theme">{chapter.subtitle}</p>
                  <div className="chapter-meta">
                    <span className="complexity">
                      {'★'.repeat(chapter.complexity)}{'☆'.repeat(5 - chapter.complexity)}
                    </span>
                    <span className="status-badge" style={{ color: statusInfo.color }}>
                      {statusInfo.text}
                    </span>
                  </div>
                  {statusInfo.canClick && (
                    <button className="start-btn" disabled={isLoading}>
                      {isLoading ? '加载中...' : '开始挑战'}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* 山顶标志 */}
        <div className="summit-marker">
          <div className="summit-icon">🏔️</div>
          <span className="summit-text">权力巅峰</span>
        </div>

        {/* 起点标志 */}
        <div className="start-marker">
          <div className="start-icon">🚩</div>
          <span className="start-text">你在这里</span>
        </div>
      </div>

      <style>{`
        .chapter-select-container {
          min-height: 100vh;
          background: linear-gradient(180deg, ${theme.bg.primary} 0%, ${theme.bg.secondary} 100%);
          position: relative;
          overflow: hidden;
        }

        .mountain-bg {
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          height: 60%;
          opacity: 0.5;
          pointer-events: none;
        }

        .mountain-bg svg {
          width: 100%;
          height: 100%;
        }

        .top-bar {
          position: relative;
          z-index: 10;
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px 40px;
          background: ${theme.bg.card};
          border-bottom: 1px solid ${theme.border.light};
          box-shadow: ${theme.shadow.sm};
        }

        .game-info {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .game-title {
          font-size: 24px;
          font-weight: 600;
          color: ${theme.accent.goldDark};
          margin: 0;
          letter-spacing: 4px;
        }

        .game-subtitle {
          font-size: 14px;
          color: ${theme.text.secondary};
          padding: 4px 12px;
          background: ${theme.bg.secondary};
          border-radius: 4px;
        }

        .player-stats {
          display: flex;
          align-items: center;
          gap: 24px;
        }

        .stat-item {
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .stat-label {
          font-size: 11px;
          color: ${theme.text.muted};
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .stat-value {
          font-size: 20px;
          font-weight: 600;
        }

        .stat-divider {
          width: 1px;
          height: 40px;
          background: ${theme.border.light};
        }

        .climbing-path {
          position: relative;
          height: calc(100vh - 80px);
          max-width: 600px;
          margin: 0 auto;
        }

        .path-lines {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
        }

        .chapter-nodes {
          position: relative;
          height: 100%;
        }

        .chapter-node {
          position: absolute;
          transform: translate(-50%, -50%);
          z-index: 5;
        }

        .chapter-node.clickable {
          cursor: pointer;
        }

        .node-glow {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 100px;
          height: 100px;
          background: radial-gradient(circle, var(--chapter-color) 0%, transparent 70%);
          opacity: 0.3;
          animation: pulse-glow 2s ease-in-out infinite;
        }

        @keyframes pulse-glow {
          0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.3; }
          50% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.5; }
        }

        .node-body {
          position: relative;
          width: 70px;
          height: 70px;
          background: ${theme.bg.card};
          border: 3px solid ${theme.border.medium};
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.3s ease;
          box-shadow: ${theme.shadow.md};
        }

        .chapter-node.available .node-body {
          border-color: var(--chapter-color);
          box-shadow: 0 0 20px var(--chapter-color);
        }

        .chapter-node.completed .node-body {
          border-color: ${theme.status.info};
          background: ${theme.status.infoBg};
        }

        .chapter-node.locked .node-body {
          opacity: 0.4;
        }

        .chapter-node.clickable:hover .node-body {
          transform: scale(1.1);
          box-shadow: 0 0 30px var(--chapter-color);
        }

        .node-icon {
          font-size: 28px;
        }

        .node-number {
          position: absolute;
          bottom: -8px;
          right: -8px;
          width: 24px;
          height: 24px;
          background: var(--chapter-color);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          font-weight: bold;
          color: #fff;
        }

        .node-info {
          position: absolute;
          top: 50%;
          transform: translateY(-50%);
          width: 200px;
          padding: 16px;
          background: ${theme.bg.card};
          border: 1px solid ${theme.border.light};
          border-radius: 12px;
          opacity: 0;
          pointer-events: none;
          transition: all 0.3s ease;
          box-shadow: ${theme.shadow.lg};
        }

        .chapter-node:nth-child(odd) .node-info {
          left: 100px;
        }

        .chapter-node:nth-child(even) .node-info {
          right: 100px;
        }

        .chapter-node.clickable:hover .node-info {
          opacity: 1;
          pointer-events: auto;
        }

        .chapter-name {
          font-size: 16px;
          color: ${theme.text.primary};
          margin: 0 0 4px 0;
          font-weight: 600;
        }

        .chapter-theme {
          font-size: 12px;
          color: ${theme.text.secondary};
          margin: 0 0 12px 0;
        }

        .chapter-meta {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .complexity {
          font-size: 12px;
          color: ${theme.accent.gold};
          letter-spacing: 2px;
        }

        .status-badge {
          font-size: 11px;
          font-weight: 500;
        }

        .start-btn {
          width: 100%;
          padding: 10px;
          background: var(--chapter-color);
          border: none;
          border-radius: 6px;
          color: #fff;
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .start-btn:hover:not(:disabled) {
          filter: brightness(1.1);
          transform: translateY(-2px);
        }

        .start-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .summit-marker {
          position: absolute;
          top: 3%;
          left: 50%;
          transform: translateX(-50%);
          text-align: center;
          z-index: 10;
        }

        .summit-icon {
          font-size: 48px;
          animation: float 3s ease-in-out infinite;
        }

        @keyframes float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }

        .summit-text {
          display: block;
          font-size: 14px;
          color: ${theme.advisor.fox};
          margin-top: 8px;
          letter-spacing: 4px;
          font-weight: 500;
        }

        .start-marker {
          position: absolute;
          bottom: 8%;
          left: 50%;
          transform: translateX(-50%);
          text-align: center;
          z-index: 10;
        }

        .start-icon {
          font-size: 32px;
        }

        .start-text {
          display: block;
          font-size: 12px;
          color: ${theme.status.success};
          margin-top: 4px;
          font-weight: 500;
        }

        @media (max-width: 768px) {
          .top-bar {
            flex-direction: column;
            gap: 16px;
            padding: 16px;
          }

          .player-stats {
            flex-wrap: wrap;
            justify-content: center;
          }

          .climbing-path {
            max-width: 100%;
            padding: 0 20px;
          }

          .node-info {
            display: none;
          }

          .chapter-node.clickable:hover .node-body {
            transform: scale(1.05);
          }
        }
      `}</style>
    </div>
  );
}
