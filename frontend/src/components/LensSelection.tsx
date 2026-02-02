// 观测透镜选择组件

import type { ObservationLensChoice } from '../types/game';

interface LensSelectionProps {
  scene: string;
  lensChoices: Record<string, ObservationLensChoice>;
  onSelect: (lens: string) => void;
  isLoading: boolean;
}

export function LensSelection({ scene, lensChoices, onSelect, isLoading }: LensSelectionProps) {
  return (
    <div className="lens-selection">
      {/* 场景描述 */}
      <div className="scene-text">
        <pre>{scene}</pre>
      </div>

      {/* 透镜选项 */}
      <div className="lens-choices">
        <h3>选择你的观测透镜</h3>
        <p className="warning-text">
          注意：这个选择将影响你看到的"现实"，不同的视角将创造不同的命运。
        </p>

        <div className="lens-grid">
          {Object.entries(lensChoices).map(([key, choice]) => (
            <div
              key={key}
              className={`lens-card lens-${key}`}
              onClick={() => !isLoading && onSelect(key)}
            >
              <h4>{choice.name}</h4>
              <p className="description">{choice.description}</p>
              <div className="effect">
                <strong>效果：</strong> {choice.effect}
              </div>
              <div className="warning">
                <em>⚠️ {choice.warning}</em>
              </div>
            </div>
          ))}
        </div>
      </div>

      <style>{`
        .lens-selection {
          max-width: 900px;
          margin: 0 auto;
          padding: 20px;
          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
          min-height: 100vh;
          color: #e0e0e0;
        }

        .scene-text {
          font-family: 'Courier New', monospace;
          font-size: 12px;
          line-height: 1.4;
          white-space: pre-wrap;
          background: rgba(0, 0, 0, 0.5);
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 30px;
          border: 1px solid #333;
          overflow-x: auto;
        }

        .scene-text pre {
          margin: 0;
          color: #00ff88;
        }

        .lens-choices h3 {
          text-align: center;
          color: #ffd700;
          font-size: 24px;
          margin-bottom: 10px;
        }

        .warning-text {
          text-align: center;
          color: #ff6b6b;
          font-style: italic;
          margin-bottom: 30px;
        }

        .lens-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
          gap: 20px;
        }

        .lens-card {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 12px;
          padding: 20px;
          cursor: pointer;
          transition: all 0.3s ease;
          border: 2px solid transparent;
        }

        .lens-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        .lens-suspicion {
          border-color: #9b59b6;
        }
        .lens-suspicion:hover {
          background: rgba(155, 89, 182, 0.2);
          border-color: #8e44ad;
        }

        .lens-expansion {
          border-color: #e74c3c;
        }
        .lens-expansion:hover {
          background: rgba(231, 76, 60, 0.2);
          border-color: #c0392b;
        }

        .lens-balance {
          border-color: #3498db;
        }
        .lens-balance:hover {
          background: rgba(52, 152, 219, 0.2);
          border-color: #2980b9;
        }

        .lens-card h4 {
          font-size: 20px;
          margin-bottom: 10px;
          color: #fff;
        }

        .lens-card .description {
          font-size: 14px;
          color: #bbb;
          margin-bottom: 15px;
          line-height: 1.5;
        }

        .lens-card .effect {
          font-size: 13px;
          color: #2ecc71;
          margin-bottom: 10px;
          padding: 8px;
          background: rgba(46, 204, 113, 0.1);
          border-radius: 4px;
        }

        .lens-card .warning {
          font-size: 12px;
          color: #e74c3c;
        }

        @media (max-width: 768px) {
          .lens-grid {
            grid-template-columns: 1fr;
          }

          .scene-text {
            font-size: 10px;
          }
        }
      `}</style>
    </div>
  );
}
