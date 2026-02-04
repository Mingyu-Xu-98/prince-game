import { useState } from 'react';
import { useGameState } from './hooks/useGameState';
import { SetupScreen, GameBoard, ChapterSelect, FinalAuditPanel, LensSelection } from './components';
import { theme } from './theme';

// 设置面板组件 - 浅色主题
function SettingsPanel({
  apiKey,
  onApiKeyChange,
  model,
  onModelChange,
  onClose
}: {
  apiKey: string;
  onApiKeyChange: (key: string) => void;
  model: string;
  onModelChange: (model: string) => void;
  onClose: () => void;
}) {
  const [showApiKey, setShowApiKey] = useState(false);

  const AVAILABLE_MODELS = [
    { id: '', label: '默认模型' },
    { id: 'anthropic/claude-3.5-sonnet', label: 'Claude 3.5 Sonnet' },
    { id: 'anthropic/claude-sonnet-4', label: 'Claude Sonnet 4' },
    { id: 'openai/gpt-4-turbo', label: 'GPT-4 Turbo' },
    { id: 'openai/gpt-4o', label: 'GPT-4o' },
    { id: 'google/gemini-2.0-flash-001', label: 'Gemini 2.0 Flash' },
  ];

  return (
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
          onClick={onClose}
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

      {/* API Key 输入 */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{ display: 'block', fontSize: '12px', color: theme.text.secondary, marginBottom: '6px' }}>
          OpenRouter API Key
        </label>
        <div style={{ position: 'relative' }}>
          <input
            type={showApiKey ? 'text' : 'password'}
            value={apiKey}
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

      {/* 模型选择 */}
      <div>
        <label style={{ display: 'block', fontSize: '12px', color: theme.text.secondary, marginBottom: '6px' }}>
          AI 模型
        </label>
        <select
          value={model}
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
    </div>
  );
}

function App() {
  const {
    sessionId,
    gameState,
    currentChapter,
    dialogueHistory,
    availableChapters,
    isLoading,
    error,
    intro,
    finalAudit,
    // 新裁决系统状态
    gamePhase,
    initializationScene,
    lensChoices,
    selectedLens,
    mountainView,
    // API Key 配置
    apiKey,
    setApiKey,
    model,
    setModel,
    // 累积的未处理影响
    pendingConsequences,
    // 状态更新器
    setGameState,
    // 操作
    startNewGame,
    selectObservationLens,
    startChapter,
    submitDecision,
    privateAudience,
    backToChapterSelect,
    exitToSetup,
    skipConsequences,
    continueWithConsequences,
    goToNextChapter,
  } = useGameState();

  // 设置面板显示状态
  const [showSettings, setShowSettings] = useState(false);

  // 如果没有开始游戏，显示设置界面
  if (!sessionId || !gameState || gamePhase === 'setup') {
    return (
      <SetupScreen
        apiKey={apiKey}
        onApiKeyChange={setApiKey}
        model={model}
        onModelChange={setModel}
        onStartGame={startNewGame}
        isLoading={isLoading}
        error={error}
      />
    );
  }

  // 观测透镜选择阶段
  if (gamePhase === 'lens_selection') {
    return (
      <LensSelection
        scene={initializationScene}
        lensChoices={lensChoices}
        onSelect={selectObservationLens}
        isLoading={isLoading}
        onBack={exitToSetup}
      />
    );
  }

  // 如果有最终审计结果，显示通关界面
  if (finalAudit) {
    return (
      <FinalAuditPanel
        audit={finalAudit}
        onNewGame={startNewGame}
      />
    );
  }

  // 获取透镜显示名称
  const getLensDisplayName = (lens: string | null) => {
    if (!lens) return null;
    const names: Record<string, string> = {
      suspicion: '🔍 怀疑',
      expansion: '⚔️ 扩张',
      balance: '⚖️ 平衡',
    };
    return names[lens] || lens;
  };

  // 游戏主界面 - 浅色主题
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: theme.bg.primary,
    }}>
      {/* 如果没有当前关卡，显示关卡选择 */}
      {!currentChapter ? (
        <ChapterSelect
          intro={intro}
          chapters={availableChapters}
          gameState={gameState}
          onSelectChapter={startChapter}
          isLoading={isLoading}
          mountainView={mountainView}
          apiKey={apiKey}
          onApiKeyChange={setApiKey}
          model={model}
          onModelChange={setModel}
          onExit={exitToSetup}
          pendingConsequences={pendingConsequences}
          onNewGame={startNewGame}
        />
      ) : (
        <>
          {/* 顶部标题栏 - 浅色 */}
          <header style={{
            padding: '12px 24px',
            backgroundColor: theme.bg.card,
            borderBottom: `1px solid ${theme.border.light}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            position: 'sticky',
            top: 0,
            zIndex: 100,
            boxShadow: theme.shadow.sm,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              {/* 返回按钮 */}
              <button
                onClick={backToChapterSelect}
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
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = theme.border.dark;
                  e.currentTarget.style.color = theme.text.primary;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = theme.border.medium;
                  e.currentTarget.style.color = theme.text.secondary;
                }}
              >
                ← 返回
              </button>
              <h1 style={{
                color: theme.accent.goldDark,
                fontSize: '18px',
                margin: 0,
                fontWeight: '600',
                letterSpacing: '2px',
              }}>
                👁️ 影子执政者
              </h1>
              {currentChapter && (
                <span style={{
                  color: theme.text.secondary,
                  fontSize: '13px',
                  padding: '4px 12px',
                  backgroundColor: theme.bg.secondary,
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}>
                  <span>{currentChapter.name}</span>
                  <span style={{ color: theme.border.medium }}>|</span>
                  <span style={{ color: theme.accent.gold }}>回合 {currentChapter.current_turn}/{currentChapter.max_turns}</span>
                </span>
              )}
              {selectedLens && (
                <span style={{
                  color: theme.advisor.fox,
                  fontSize: '12px',
                  padding: '4px 8px',
                  backgroundColor: theme.advisor.foxBg,
                  borderRadius: '4px',
                  border: `1px solid ${theme.advisor.fox}30`,
                }}>
                  {getLensDisplayName(selectedLens)}
                </span>
              )}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', position: 'relative' }}>
              {error && (
                <span style={{
                  color: theme.status.error,
                  fontSize: '12px',
                  padding: '6px 12px',
                  backgroundColor: theme.status.errorBg,
                  borderRadius: '4px',
                  border: `1px solid ${theme.status.error}30`,
                }}>
                  ⚠️ {error}
                </span>
              )}
              {/* 设置按钮 */}
              <button
                onClick={() => setShowSettings(!showSettings)}
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
                onMouseEnter={(e) => {
                  if (!showSettings) {
                    e.currentTarget.style.borderColor = theme.border.dark;
                    e.currentTarget.style.color = theme.text.primary;
                  }
                }}
                onMouseLeave={(e) => {
                  if (!showSettings) {
                    e.currentTarget.style.borderColor = theme.border.medium;
                    e.currentTarget.style.color = theme.text.secondary;
                  }
                }}
              >
                ⚙️ 设置
              </button>
              {/* 设置面板 */}
              {showSettings && (
                <SettingsPanel
                  apiKey={apiKey}
                  onApiKeyChange={setApiKey}
                  model={model}
                  onModelChange={setModel}
                  onClose={() => setShowSettings(false)}
                />
              )}
              <button
                onClick={startNewGame}
                style={{
                  padding: '8px 16px',
                  backgroundColor: 'transparent',
                  border: `1px solid ${theme.border.medium}`,
                  borderRadius: '6px',
                  color: theme.text.secondary,
                  fontSize: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = theme.border.dark;
                  e.currentTarget.style.color = theme.text.primary;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = theme.border.medium;
                  e.currentTarget.style.color = theme.text.secondary;
                }}
              >
                🔄 新游戏
              </button>
            </div>
          </header>

          {/* 游戏主面板 */}
          <GameBoard
            gameState={gameState}
            currentChapter={currentChapter}
            dialogueHistory={dialogueHistory}
            isLoading={isLoading}
            sessionId={sessionId}
            apiKey={apiKey}
            model={model}
            onSubmitDecision={submitDecision}
            onPrivateAudience={privateAudience}
            onNextChapter={goToNextChapter}
            onSkipConsequences={skipConsequences}
            onContinueWithConsequences={continueWithConsequences}
            onUpdateGameState={setGameState}
          />
        </>
      )}
    </div>
  );
}

export default App;
