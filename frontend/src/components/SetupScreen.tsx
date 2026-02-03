// 游戏设置/开始界面组件 - 浅色米色主题

import { useState } from 'react';

interface SetupScreenProps {
  apiKey: string;
  onApiKeyChange: (key: string) => void;
  model: string;
  onModelChange: (model: string) => void;
  onStartGame: () => void;
  isLoading: boolean;
  error: string | null;
}

const AVAILABLE_MODELS = [
  { id: '', label: '默认模型' },
  { id: 'anthropic/claude-3.5-sonnet', label: 'Claude 3.5 Sonnet' },
  { id: 'anthropic/claude-sonnet-4', label: 'Claude Sonnet 4' },
  { id: 'openai/gpt-4-turbo', label: 'GPT-4 Turbo' },
  { id: 'openai/gpt-4o', label: 'GPT-4o' },
  { id: 'google/gemini-2.0-flash-001', label: 'Gemini 2.0 Flash' },
];

export function SetupScreen({
  apiKey,
  onApiKeyChange,
  model,
  onModelChange,
  onStartGame,
  isLoading,
  error,
}: SetupScreenProps) {
  const [showApiKey, setShowApiKey] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  return (
    <div className="setup-container">
      {/* 背景装饰 */}
      <div className="bg-decoration">
        <div className="bg-circle circle-1" />
        <div className="bg-circle circle-2" />
        <div className="bg-circle circle-3" />
      </div>

      {/* 右上角API设置按钮 */}
      <div className="top-right-settings">
        <button
          className="settings-toggle"
          onClick={() => setShowSettings(!showSettings)}
        >
          ⚙️ {apiKey ? '已配置' : '设置API'}
        </button>

        {showSettings && (
          <div className="settings-dropdown">
            <div className="settings-header">
              <span>API 配置</span>
              <button className="close-btn" onClick={() => setShowSettings(false)}>×</button>
            </div>

            {/* API Key 输入 */}
            <div className="form-group">
              <label className="form-label">OpenRouter API Key</label>
              <div className="input-wrapper">
                <input
                  type={showApiKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={(e) => onApiKeyChange(e.target.value)}
                  placeholder="sk-or-..."
                  className="form-input"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="toggle-visibility"
                >
                  {showApiKey ? '🙈' : '👁️'}
                </button>
              </div>
              <p className="form-hint">
                从{' '}
                <a href="https://openrouter.ai/keys" target="_blank" rel="noopener noreferrer">
                  openrouter.ai
                </a>
                {' '}获取
              </p>
            </div>

            {/* 模型选择 */}
            <div className="form-group">
              <label className="form-label">AI 模型</label>
              <select
                value={model}
                onChange={(e) => onModelChange(e.target.value)}
                className="form-select"
              >
                {AVAILABLE_MODELS.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      <div className="setup-content">
        {/* 标题区 */}
        <div className="title-section">
          <div className="logo-icon">👁️</div>
          <h1 className="game-title">影子执政者</h1>
          <p className="game-subtitle">SHADOW REGENT</p>
        </div>

        {/* 引言 */}
        <div className="quote-box">
          <div className="quote-text">
            "君主必须既是狮子又是狐狸——狮子不能使自己免于陷阱，而狐狸则不能抵御豺狼。"
          </div>
          <div className="quote-author">—— 尼科洛·马基雅维利《君主论》</div>
        </div>

        {/* 三顾问预览 */}
        <div className="advisors-preview">
          <div className="advisor-item lion">
            <span className="advisor-icon">🦁</span>
            <span className="advisor-name">狮子</span>
            <span className="advisor-role">武力与威慑</span>
          </div>
          <div className="advisor-item fox">
            <span className="advisor-icon">🦊</span>
            <span className="advisor-name">狐狸</span>
            <span className="advisor-role">权谋与狡诈</span>
          </div>
          <div className="advisor-item balance">
            <span className="advisor-icon">⚖️</span>
            <span className="advisor-name">天平</span>
            <span className="advisor-role">正义与民心</span>
          </div>
        </div>

        {/* 游戏介绍 */}
        <div className="game-intro">
          <p>你是一位新晋的<span className="highlight">影子执政者</span>，在幕后操控着这个国家的命运。</p>
          <p>三位顾问将为你出谋划策，但最终的抉择，只在你手中。</p>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        {/* 底部开始按钮 */}
        <div className="bottom-section">
          <button
            onClick={onStartGame}
            disabled={!apiKey || isLoading}
            className={`start-button ${!apiKey || isLoading ? 'disabled' : ''}`}
          >
            {isLoading ? (
              <>
                <span className="loading-spinner" />
                正在进入...
              </>
            ) : !apiKey ? (
              <>请先配置 API Key ↗</>
            ) : (
              <>开始统治 👑</>
            )}
          </button>

          {!apiKey && (
            <p className="hint-text">点击右上角 ⚙️ 设置 API Key</p>
          )}
        </div>
      </div>

      <style>{`
        .setup-container {
          min-height: 100vh;
          background: linear-gradient(135deg, #FDF6E3 0%, #F5EBDC 50%, #EDE4D3 100%);
          position: relative;
          overflow: hidden;
        }

        .bg-decoration {
          position: absolute;
          inset: 0;
          pointer-events: none;
          overflow: hidden;
        }

        .bg-circle {
          position: absolute;
          border-radius: 50%;
          opacity: 0.15;
        }

        .circle-1 {
          width: 600px;
          height: 600px;
          background: radial-gradient(circle, #C9A227 0%, transparent 70%);
          top: -200px;
          right: -100px;
        }

        .circle-2 {
          width: 400px;
          height: 400px;
          background: radial-gradient(circle, #805AD5 0%, transparent 70%);
          bottom: -100px;
          left: -100px;
        }

        .circle-3 {
          width: 300px;
          height: 300px;
          background: radial-gradient(circle, #2F855A 0%, transparent 70%);
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
        }

        /* 右上角设置区域 */
        .top-right-settings {
          position: absolute;
          top: 20px;
          right: 20px;
          z-index: 100;
        }

        .settings-toggle {
          padding: 10px 16px;
          background: #FFFFFF;
          border: 1px solid #D4C4A8;
          border-radius: 8px;
          color: #3D3D3D;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.2s;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }

        .settings-toggle:hover {
          border-color: #C9A227;
          box-shadow: 0 4px 12px rgba(201, 162, 39, 0.15);
        }

        .settings-dropdown {
          position: absolute;
          top: 50px;
          right: 0;
          width: 320px;
          background: #FFFFFF;
          border: 1px solid #D4C4A8;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
        }

        .settings-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          color: #3D3D3D;
          font-size: 14px;
          font-weight: 600;
        }

        .close-btn {
          background: none;
          border: none;
          color: #9B9B9B;
          font-size: 20px;
          cursor: pointer;
          padding: 0 4px;
        }

        .close-btn:hover {
          color: #3D3D3D;
        }

        .setup-content {
          position: relative;
          z-index: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: space-between;
          padding: 80px 20px 60px;
          min-height: 100vh;
          box-sizing: border-box;
        }

        .title-section {
          text-align: center;
          margin-bottom: 24px;
        }

        .logo-icon {
          font-size: 72px;
          margin-bottom: 16px;
          animation: pulse 3s ease-in-out infinite;
        }

        @keyframes pulse {
          0%, 100% { transform: scale(1); filter: drop-shadow(0 0 20px rgba(201, 162, 39, 0.3)); }
          50% { transform: scale(1.05); filter: drop-shadow(0 0 40px rgba(201, 162, 39, 0.5)); }
        }

        .game-title {
          font-size: 52px;
          font-weight: 300;
          color: #8B6914;
          margin: 0;
          letter-spacing: 16px;
          text-shadow: 0 2px 10px rgba(139, 105, 20, 0.2);
        }

        .game-subtitle {
          font-size: 14px;
          color: #9B9B9B;
          letter-spacing: 10px;
          margin-top: 8px;
        }

        .quote-box {
          max-width: 550px;
          text-align: center;
          margin-bottom: 32px;
          padding: 24px 32px;
          background: #FFFFFF;
          border-radius: 12px;
          border: 1px solid #E8DCC8;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        }

        .quote-text {
          font-size: 16px;
          color: #6B6B6B;
          line-height: 1.8;
          font-style: italic;
        }

        .quote-author {
          font-size: 13px;
          color: #9B9B9B;
          margin-top: 12px;
        }

        .advisors-preview {
          display: flex;
          gap: 32px;
          margin-bottom: 32px;
        }

        .advisor-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 16px 24px;
          background: #FFFFFF;
          border-radius: 12px;
          border: 1px solid #E8DCC8;
          transition: all 0.3s ease;
          box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
        }

        .advisor-item:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
        }

        .advisor-item.lion:hover { border-color: #C53030; }
        .advisor-item.fox:hover { border-color: #805AD5; }
        .advisor-item.balance:hover { border-color: #2F855A; }

        .advisor-icon {
          font-size: 36px;
          margin-bottom: 8px;
        }

        .advisor-name {
          font-size: 14px;
          color: #3D3D3D;
          font-weight: 500;
        }

        .advisor-role {
          font-size: 11px;
          color: #9B9B9B;
          margin-top: 4px;
        }

        .game-intro {
          text-align: center;
          max-width: 500px;
          margin-bottom: 20px;
        }

        .game-intro p {
          color: #6B6B6B;
          font-size: 15px;
          line-height: 1.8;
          margin: 8px 0;
        }

        .game-intro .highlight {
          color: #8B6914;
          font-weight: 600;
        }

        .form-group {
          margin-bottom: 16px;
        }

        .form-label {
          display: block;
          font-size: 12px;
          color: #6B6B6B;
          margin-bottom: 6px;
        }

        .input-wrapper {
          position: relative;
        }

        .form-input {
          width: 100%;
          padding: 12px 40px 12px 14px;
          background: #FDF6E3;
          border: 1px solid #D4C4A8;
          border-radius: 8px;
          color: #3D3D3D;
          font-size: 13px;
          outline: none;
          box-sizing: border-box;
          transition: border-color 0.2s;
        }

        .form-input:focus {
          border-color: #C9A227;
        }

        .toggle-visibility {
          position: absolute;
          right: 10px;
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          color: #9B9B9B;
          cursor: pointer;
          font-size: 14px;
          transition: color 0.2s;
        }

        .toggle-visibility:hover {
          color: #3D3D3D;
        }

        .form-hint {
          font-size: 11px;
          color: #9B9B9B;
          margin: 6px 0 0 0;
        }

        .form-hint a {
          color: #3182CE;
          text-decoration: none;
        }

        .form-hint a:hover {
          text-decoration: underline;
        }

        .form-select {
          width: 100%;
          padding: 12px 14px;
          background: #FDF6E3;
          border: 1px solid #D4C4A8;
          border-radius: 8px;
          color: #3D3D3D;
          font-size: 13px;
          outline: none;
          cursor: pointer;
          transition: border-color 0.2s;
        }

        .form-select:focus {
          border-color: #C9A227;
        }

        .error-message {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          background: #FED7D7;
          border: 1px solid #FC8181;
          border-radius: 8px;
          color: #C53030;
          font-size: 13px;
          margin-bottom: 16px;
          max-width: 400px;
        }

        .bottom-section {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 12px;
          margin-top: auto;
        }

        .start-button {
          padding: 18px 60px;
          background: linear-gradient(135deg, #C9A227 0%, #E8C547 100%);
          border: none;
          border-radius: 12px;
          font-size: 18px;
          font-weight: 600;
          color: #FFFFFF;
          cursor: pointer;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          box-shadow: 0 4px 15px rgba(201, 162, 39, 0.3);
        }

        .start-button:hover:not(.disabled) {
          transform: translateY(-3px);
          box-shadow: 0 8px 25px rgba(201, 162, 39, 0.4);
        }

        .start-button.disabled {
          background: #D4C4A8;
          color: #9B9B9B;
          cursor: not-allowed;
          box-shadow: none;
        }

        .hint-text {
          color: #9B9B9B;
          font-size: 13px;
          margin: 0;
        }

        .loading-spinner {
          width: 18px;
          height: 18px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: #FFFFFF;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        @media (max-width: 600px) {
          .game-title {
            font-size: 36px;
            letter-spacing: 8px;
          }

          .advisors-preview {
            flex-direction: column;
            gap: 16px;
          }

          .advisor-item {
            flex-direction: row;
            gap: 16px;
            width: 100%;
            max-width: 280px;
          }

          .advisor-icon {
            margin-bottom: 0;
          }

          .settings-dropdown {
            width: 280px;
          }
        }
      `}</style>
    </div>
  );
}
