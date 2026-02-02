// 主游戏面板组件

import { PowerMeter } from './PowerMeter';
import { RobotCard } from './RobotCard';
import { ChatPanel } from './ChatPanel';
import { EventModal } from './EventModal';
import type { GameState, TurnResult, GameEvent, DialogueEntry } from '../types/game';

interface GameBoardProps {
  gameState: GameState;
  dialogueHistory: DialogueEntry[];
  lastTurnResult: TurnResult | null;
  currentEvent: GameEvent | null;
  isLoading: boolean;
  onSubmitTurn: (input: string) => void;
  onEventChoice: (choiceId: string) => void;
}

export function GameBoard({
  gameState,
  dialogueHistory,
  lastTurnResult,
  currentEvent,
  isLoading,
  onSubmitTurn,
  onEventChoice,
}: GameBoardProps) {
  const powerChanges = lastTurnResult?.settlement.power_changes;

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '300px 1fr 350px',
      gap: '20px',
      height: 'calc(100vh - 120px)',
      padding: '20px',
    }}>
      {/* 左侧：权力面板 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* 权力三维 */}
        <PowerMeter power={gameState.power} changes={powerChanges} />

        {/* 回合信息 */}
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
          }}>
            <span style={{ color: '#888', fontSize: '14px' }}>当前回合</span>
            <span style={{ color: '#ffd700', fontSize: '24px', fontWeight: 'bold' }}>
              {gameState.turn}
            </span>
          </div>
        </div>

        {/* 警告信息 */}
        {gameState.warnings.length > 0 && (
          <div style={{
            padding: '16px',
            backgroundColor: '#2d1515',
            borderRadius: '8px',
            border: '1px solid #ef444450',
          }}>
            <h4 style={{ margin: '0 0 8px 0', color: '#ef4444', fontSize: '14px' }}>
              ⚠️ 警告
            </h4>
            {gameState.warnings.map((warning, index) => (
              <div
                key={index}
                style={{
                  color: '#fca5a5',
                  fontSize: '13px',
                  marginBottom: '4px',
                }}
              >
                • {warning}
              </div>
            ))}
          </div>
        )}

        {/* 游戏结束 */}
        {gameState.game_over && (
          <div style={{
            padding: '20px',
            backgroundColor: '#1a0a0a',
            borderRadius: '8px',
            border: '2px solid #ef4444',
            textAlign: 'center',
          }}>
            <div style={{
              fontSize: '24px',
              marginBottom: '8px',
            }}>
              💀
            </div>
            <div style={{
              color: '#ef4444',
              fontSize: '18px',
              fontWeight: 'bold',
              marginBottom: '8px',
            }}>
              统治终结
            </div>
            <div style={{
              color: '#fca5a5',
              fontSize: '14px',
              lineHeight: '1.5',
            }}>
              {gameState.game_over_reason}
            </div>
          </div>
        )}
      </div>

      {/* 中间：对话面板 */}
      <ChatPanel
        history={dialogueHistory}
        onSubmit={onSubmitTurn}
        isLoading={isLoading}
        disabled={gameState.game_over}
      />

      {/* 右侧：顾问面板 */}
      <div style={{
        overflowY: 'auto',
        paddingRight: '8px',
      }}>
        <h3 style={{
          margin: '0 0 16px 0',
          color: '#ffd700',
          fontSize: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}>
          👥 三顾问评议
        </h3>

        <RobotCard
          type="lion"
          response={lastTurnResult?.robot_responses.lion || '等待你的第一道政令...'}
          relation={gameState.relations.lion}
          assessment={lastTurnResult?.audit_summary.skill_reports.lion.assessment}
        />

        <RobotCard
          type="fox"
          response={lastTurnResult?.robot_responses.fox || '我在倾听，也在记录...'}
          relation={gameState.relations.fox}
          assessment={lastTurnResult?.audit_summary.skill_reports.fox.assessment}
        />

        <RobotCard
          type="balance"
          response={lastTurnResult?.robot_responses.balance || '天平在等待...'}
          relation={gameState.relations.balance}
          assessment={lastTurnResult?.audit_summary.skill_reports.balance.assessment}
        />
      </div>

      {/* 事件弹窗 */}
      {currentEvent && (
        <EventModal
          event={currentEvent}
          onChoice={onEventChoice}
          isLoading={isLoading}
        />
      )}
    </div>
  );
}
