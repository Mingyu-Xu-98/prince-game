// 观测透镜选择组件 - 浅色主题

import type { ObservationLensChoice } from '../types/game';
import { theme } from '../theme';

interface LensSelectionProps {
  scene: string;
  lensChoices: Record<string, ObservationLensChoice>;
  onSelect: (lens: string) => void;
  isLoading: boolean;
}

export function LensSelection({ lensChoices, onSelect, isLoading }: LensSelectionProps) {
  // 透镜的神秘名称和意象，不透露具体效果
  const lensDisplay: Record<string, { icon: string; name: string; motto: string }> = {
    suspicion: {
      icon: '🔍',
      name: '疑虑之眼',
      motto: '"信任是弱者的避难所"'
    },
    expansion: {
      icon: '⚔️',
      name: '征服之眼',
      motto: '"唯有前进，方能生存"'
    },
    balance: {
      icon: '⚖️',
      name: '衡量之眼',
      motto: '"稳定是最大的美德"'
    },
  };

  const lensColors: Record<string, { primary: string; bg: string; glow: string }> = {
    suspicion: { primary: theme.advisor.fox, bg: theme.advisor.foxBg, glow: `${theme.advisor.fox}40` },
    expansion: { primary: theme.advisor.lion, bg: theme.advisor.lionBg, glow: `${theme.advisor.lion}40` },
    balance: { primary: theme.advisor.balance, bg: theme.advisor.balanceBg, glow: `${theme.advisor.balance}40` },
  };

  return (
    <div className="lens-container">
      {/* 背景装饰 */}
      <div className="bg-decoration">
        <div className="decoration-circle c1" />
        <div className="decoration-circle c2" />
        <div className="decoration-circle c3" />
      </div>

      {/* 主内容 */}
      <div className="lens-content">
        {/* 标题区域 */}
        <div className="title-section">
          <div className="game-logo">👁️</div>
          <h1 className="game-title">影子执政者</h1>
          <p className="game-subtitle">Shadow Regent</p>
        </div>

        {/* 三顾问动画展示 */}
        <div className="advisors-showcase">
          <div className="advisor-figure lion">
            <span className="advisor-icon">🦁</span>
            <span className="advisor-label">狮子</span>
          </div>
          <div className="advisor-figure fox">
            <span className="advisor-icon">🦊</span>
            <span className="advisor-label">狐狸</span>
          </div>
          <div className="advisor-figure balance">
            <span className="advisor-icon">⚖️</span>
            <span className="advisor-label">天平</span>
          </div>
        </div>

        {/* 场景描述 */}
        <div className="scene-description">
          <p className="narration">三位顾问在你面前静候，等待你的抉择...</p>
          <p className="question">"你将如何看待这个世界？"</p>
        </div>

        {/* 透镜选择 */}
        <div className="lens-selection-area">
          <h2 className="section-title">选择你的观测透镜</h2>
          <p className="section-hint">每一种视角都将塑造你眼中的现实</p>

          <div className="lens-cards">
            {Object.keys(lensChoices).map((key) => {
              const colors = lensColors[key];
              const display = lensDisplay[key];
              return (
                <div
                  key={key}
                  className={`lens-card ${isLoading ? 'disabled' : ''}`}
                  onClick={() => !isLoading && onSelect(key)}
                  style={{
                    '--card-color': colors.primary,
                    '--card-bg': colors.bg,
                    '--card-glow': colors.glow,
                  } as React.CSSProperties}
                >
                  <div className="card-icon">{display.icon}</div>
                  <h3 className="card-title">{display.name}</h3>
                  <p className="card-motto">{display.motto}</p>
                  <div className="card-mystery">
                    <span className="mystery-text">???</span>
                  </div>
                  <div className="card-select-hint">点击选择</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <style>{`
        .lens-container {
          min-height: 100vh;
          background: linear-gradient(135deg, ${theme.bg.primary} 0%, ${theme.bg.secondary} 50%, ${theme.bg.tertiary} 100%);
          position: relative;
          overflow: hidden;
        }

        .bg-decoration {
          position: absolute;
          inset: 0;
          pointer-events: none;
          overflow: hidden;
        }

        .decoration-circle {
          position: absolute;
          border-radius: 50%;
          opacity: 0.1;
        }

        .decoration-circle.c1 {
          width: 400px;
          height: 400px;
          background: ${theme.accent.gold};
          top: -100px;
          right: -100px;
        }

        .decoration-circle.c2 {
          width: 300px;
          height: 300px;
          background: ${theme.advisor.fox};
          bottom: -50px;
          left: -50px;
        }

        .decoration-circle.c3 {
          width: 200px;
          height: 200px;
          background: ${theme.advisor.balance};
          top: 50%;
          left: 10%;
        }

        .lens-content {
          position: relative;
          z-index: 1;
          max-width: 1000px;
          margin: 0 auto;
          padding: 40px 20px;
        }

        .title-section {
          text-align: center;
          margin-bottom: 40px;
        }

        .game-logo {
          font-size: 64px;
          margin-bottom: 16px;
          animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.1); }
        }

        .game-title {
          font-size: 48px;
          font-weight: 600;
          color: ${theme.accent.goldDark};
          margin: 0;
          letter-spacing: 12px;
        }

        .game-subtitle {
          font-size: 14px;
          color: ${theme.text.muted};
          letter-spacing: 8px;
          margin-top: 8px;
          text-transform: uppercase;
        }

        .advisors-showcase {
          display: flex;
          justify-content: center;
          gap: 60px;
          margin-bottom: 40px;
        }

        .advisor-figure {
          display: flex;
          flex-direction: column;
          align-items: center;
          animation: fade-in-up 0.8s ease-out;
        }

        .advisor-figure:nth-child(2) { animation-delay: 0.2s; }
        .advisor-figure:nth-child(3) { animation-delay: 0.4s; }

        @keyframes fade-in-up {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .advisor-icon {
          font-size: 48px;
          margin-bottom: 8px;
        }

        .advisor-label {
          font-size: 14px;
          color: ${theme.text.secondary};
          font-weight: 500;
        }

        .advisor-figure.lion .advisor-icon { filter: drop-shadow(0 0 10px ${theme.advisor.lion}); }
        .advisor-figure.fox .advisor-icon { filter: drop-shadow(0 0 10px ${theme.advisor.fox}); }
        .advisor-figure.balance .advisor-icon { filter: drop-shadow(0 0 10px ${theme.advisor.balance}); }

        .scene-description {
          text-align: center;
          margin-bottom: 50px;
        }

        .narration {
          font-size: 18px;
          color: ${theme.text.secondary};
          margin-bottom: 16px;
          font-style: italic;
        }

        .question {
          font-size: 24px;
          color: ${theme.accent.goldDark};
          font-weight: 500;
        }

        .lens-selection-area {
          text-align: center;
        }

        .section-title {
          font-size: 24px;
          color: ${theme.text.primary};
          font-weight: 600;
          margin-bottom: 8px;
        }

        .section-hint {
          font-size: 14px;
          color: ${theme.text.muted};
          margin-bottom: 32px;
        }

        .lens-cards {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 24px;
        }

        .lens-card {
          background: ${theme.bg.card};
          border: 2px solid ${theme.border.light};
          border-radius: 16px;
          padding: 28px 20px;
          cursor: pointer;
          transition: all 0.3s ease;
          position: relative;
          overflow: hidden;
          box-shadow: ${theme.shadow.sm};
        }

        .lens-card::before {
          content: '';
          position: absolute;
          inset: 0;
          background: linear-gradient(180deg, transparent 0%, var(--card-bg) 100%);
          opacity: 0;
          transition: opacity 0.3s;
        }

        .lens-card:hover {
          border-color: var(--card-color);
          transform: translateY(-8px);
          box-shadow: 0 20px 40px var(--card-glow);
        }

        .lens-card:hover::before {
          opacity: 1;
        }

        .lens-card.disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .card-icon {
          font-size: 48px;
          margin-bottom: 16px;
          position: relative;
          z-index: 1;
        }

        .card-title {
          font-size: 22px;
          color: var(--card-color);
          margin: 0 0 16px 0;
          font-weight: 600;
          position: relative;
          z-index: 1;
        }

        .card-motto {
          font-size: 14px;
          color: ${theme.text.secondary};
          line-height: 1.6;
          margin-bottom: 24px;
          font-style: italic;
          position: relative;
          z-index: 1;
        }

        .card-mystery {
          background: ${theme.bg.secondary};
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 8px;
          position: relative;
          z-index: 1;
        }

        .mystery-text {
          font-size: 18px;
          color: ${theme.text.muted};
          letter-spacing: 4px;
        }

        .card-select-hint {
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          padding: 12px;
          background: var(--card-color);
          color: #fff;
          font-size: 14px;
          font-weight: 500;
          transform: translateY(100%);
          transition: transform 0.3s ease;
        }

        .lens-card:hover .card-select-hint {
          transform: translateY(0);
        }

        @media (max-width: 900px) {
          .lens-cards {
            grid-template-columns: 1fr;
            max-width: 400px;
            margin: 0 auto;
          }

          .game-title {
            font-size: 32px;
            letter-spacing: 6px;
          }

          .advisors-showcase {
            gap: 30px;
          }
        }
      `}</style>
    </div>
  );
}
