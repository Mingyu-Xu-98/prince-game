import { useGameState } from './hooks/useGameState';
import { SetupScreen, GameBoard, ChapterSelect, FinalAuditPanel } from './components';

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
    apiKey,
    setApiKey,
    model,
    setModel,
    startNewGame,
    startChapter,
    submitDecision,
  } = useGameState();

  // 如果没有开始游戏，显示设置界面
  if (!sessionId || !gameState) {
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

  // 如果有最终审计结果，显示通关界面
  if (finalAudit) {
    return (
      <FinalAuditPanel
        audit={finalAudit}
        onNewGame={startNewGame}
      />
    );
  }

  // 游戏主界面
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0a0a14',
    }}>
      {/* 顶部标题栏 */}
      <header style={{
        padding: '16px 24px',
        backgroundColor: '#0f0f1a',
        borderBottom: '1px solid #222',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <h1 style={{
            color: '#ffd700',
            fontSize: '20px',
            margin: 0,
            fontWeight: '400',
            letterSpacing: '2px',
          }}>
            👑 君主论
          </h1>
          {currentChapter && (
            <span style={{
              color: '#888',
              fontSize: '14px',
              padding: '4px 12px',
              backgroundColor: '#1a1a2e',
              borderRadius: '4px',
            }}>
              📜 {currentChapter.chapter_name} - 回合 {currentChapter.current_turn}/{currentChapter.max_turns}
            </span>
          )}
          <span style={{
            color: '#555',
            fontSize: '12px',
          }}>
            SESSION: {sessionId.slice(0, 8)}...
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {error && (
            <span style={{
              color: '#fca5a5',
              fontSize: '13px',
              padding: '6px 12px',
              backgroundColor: '#2d1515',
              borderRadius: '4px',
            }}>
              ⚠️ {error}
            </span>
          )}
          <button
            onClick={startNewGame}
            style={{
              padding: '8px 16px',
              backgroundColor: 'transparent',
              border: '1px solid #333',
              borderRadius: '6px',
              color: '#888',
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            🔄 新游戏
          </button>
        </div>
      </header>

      {/* 如果没有当前关卡，显示关卡选择或介绍 */}
      {!currentChapter ? (
        <ChapterSelect
          intro={intro}
          chapters={availableChapters}
          gameState={gameState}
          onSelectChapter={startChapter}
          isLoading={isLoading}
        />
      ) : (
        /* 游戏主面板 */
        <GameBoard
          gameState={gameState}
          currentChapter={currentChapter}
          dialogueHistory={dialogueHistory}
          isLoading={isLoading}
          onSubmitDecision={submitDecision}
        />
      )}
    </div>
  );
}

export default App;
