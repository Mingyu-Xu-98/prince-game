import { useGameState } from './hooks/useGameState';
import { SetupScreen, GameBoard } from './components';

function App() {
  const {
    sessionId,
    gameState,
    dialogueHistory,
    currentEvent,
    isLoading,
    error,
    lastTurnResult,
    apiKey,
    setApiKey,
    model,
    setModel,
    startNewGame,
    submitTurn,
    handleEventChoice,
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

      {/* 游戏主面板 */}
      <GameBoard
        gameState={gameState}
        dialogueHistory={dialogueHistory}
        lastTurnResult={lastTurnResult}
        currentEvent={currentEvent}
        isLoading={isLoading}
        onSubmitTurn={submitTurn}
        onEventChoice={handleEventChoice}
      />
    </div>
  );
}

export default App;
