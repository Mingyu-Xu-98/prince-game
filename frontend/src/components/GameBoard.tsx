// 主游戏面板组件 - 支持关卡系统

import { useState } from 'react';
import { PowerMeter } from './PowerMeter';
import { RobotCard } from './RobotCard';
import { ChatPanel } from './ChatPanel';
import type { GameState, ChapterScene, DialogueEntry, DecisionResult } from '../types/game';

interface GameBoardProps {
  gameState: GameState;
  currentChapter: ChapterScene;
  dialogueHistory: DialogueEntry[];
  isLoading: boolean;
  onSubmitDecision: (input: string, followedAdvisor?: string) => Promise<DecisionResult | null>;
}

export function GameBoard({
  gameState,
  currentChapter,
  dialogueHistory,
  isLoading,
  onSubmitDecision,
}: GameBoardProps) {
  const [selectedAdvisor, setSelectedAdvisor] = useState<string | null>(null);

  const handleSubmit = async (input: string) => {
    await onSubmitDecision(input, selectedAdvisor || undefined);
    setSelectedAdvisor(null);
  };

  // 从 council_debate 获取顾问建议
  const lionSuggestion = currentChapter.council_debate?.lion;
  const foxSuggestion = currentChapter.council_debate?.fox;
  const balanceSuggestion = currentChapter.council_debate?.balance;

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '320px 1fr 380px',
      gap: '20px',
      height: 'calc(100vh - 80px)',
      padding: '20px',
    }}>
      {/* 左侧：权力面板 + 关卡信息 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
        {/* 权力三维 */}
        <PowerMeter power={gameState.power} hideValues={currentChapter.hide_values} />

        {/* 关卡信息 */}
        <div style={{
          padding: '16px',
          backgroundColor: '#1a1a2e',
          borderRadius: '8px',
          border: '1px solid #333',
        }}>
          <h4 style={{
            margin: '0 0 12px 0',
            color: '#ffd700',
            fontSize: '14px',
          }}>
            📜 {currentChapter.name}
          </h4>
          <div style={{
            color: '#888',
            fontSize: '12px',
            lineHeight: '1.6',
            marginBottom: '12px',
          }}>
            {currentChapter.dilemma}
          </div>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            paddingTop: '12px',
            borderTop: '1px solid #333',
          }}>
            <span style={{ color: '#888', fontSize: '12px' }}>回合进度</span>
            <span style={{ color: '#ffd700', fontSize: '14px' }}>
              {currentChapter.current_turn} / {currentChapter.max_turns}
            </span>
          </div>
        </div>

        {/* 信用积分 */}
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
            <span style={{ color: '#888', fontSize: '13px' }}>💳 信用积分</span>
            <span style={{
              color: gameState.credit_score > 50 ? '#4ade80' : gameState.credit_score > 20 ? '#ffd700' : '#ef4444',
              fontSize: '18px',
              fontWeight: 'bold',
            }}>
              {gameState.credit_score.toFixed(0)}
            </span>
          </div>
          {gameState.active_promises > 0 && (
            <div style={{
              marginTop: '8px',
              color: '#888',
              fontSize: '12px',
            }}>
              📝 待履行承诺: {gameState.active_promises}
            </div>
          )}
          {gameState.leverages_against_you > 0 && (
            <div style={{
              marginTop: '4px',
              color: '#ef4444',
              fontSize: '12px',
            }}>
              📎 被握把柄: {gameState.leverages_against_you}
            </div>
          )}
        </div>

        {/* 警告信息 */}
        {gameState.warnings && gameState.warnings.length > 0 && (
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
            <div style={{ fontSize: '24px', marginBottom: '8px' }}>💀</div>
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
        onSubmit={handleSubmit}
        isLoading={isLoading}
        disabled={gameState.game_over}
      />

      {/* 右侧：顾问建议 */}
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
          👥 顾问建议
        </h3>

        <p style={{
          color: '#888',
          fontSize: '12px',
          marginBottom: '16px',
        }}>
          点击顾问卡片采纳其建议（可选）
        </p>

        {/* 狮子建议 */}
        {lionSuggestion && (
          <div
            onClick={() => setSelectedAdvisor(selectedAdvisor === 'lion' ? null : 'lion')}
            style={{
              marginBottom: '16px',
              padding: '16px',
              backgroundColor: selectedAdvisor === 'lion' ? '#2d1515' : '#1a1a2e',
              borderRadius: '12px',
              border: `2px solid ${selectedAdvisor === 'lion' ? '#ef4444' : '#333'}`,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '12px',
            }}>
              <span style={{ fontSize: '24px' }}>🦁</span>
              <span style={{ color: '#ef4444', fontWeight: 'bold' }}>狮子 (Leo)</span>
              {selectedAdvisor === 'lion' && (
                <span style={{
                  marginLeft: 'auto',
                  color: '#ef4444',
                  fontSize: '12px',
                  padding: '2px 8px',
                  backgroundColor: '#ef444420',
                  borderRadius: '4px',
                }}>
                  已选择
                </span>
              )}
            </div>
            <div style={{
              color: '#fff',
              fontSize: '14px',
              marginBottom: '8px',
              lineHeight: '1.5',
            }}>
              "{lionSuggestion.suggestion}"
            </div>
            <div style={{
              color: '#888',
              fontSize: '12px',
              fontStyle: 'italic',
            }}>
              {lionSuggestion.reasoning}
            </div>
          </div>
        )}

        {/* 狐狸建议 */}
        {foxSuggestion && (
          <div
            onClick={() => setSelectedAdvisor(selectedAdvisor === 'fox' ? null : 'fox')}
            style={{
              marginBottom: '16px',
              padding: '16px',
              backgroundColor: selectedAdvisor === 'fox' ? '#1a1a2d' : '#1a1a2e',
              borderRadius: '12px',
              border: `2px solid ${selectedAdvisor === 'fox' ? '#a855f7' : '#333'}`,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '12px',
            }}>
              <span style={{ fontSize: '24px' }}>🦊</span>
              <span style={{ color: '#a855f7', fontWeight: 'bold' }}>狐狸 (Vulpes)</span>
              {selectedAdvisor === 'fox' && (
                <span style={{
                  marginLeft: 'auto',
                  color: '#a855f7',
                  fontSize: '12px',
                  padding: '2px 8px',
                  backgroundColor: '#a855f720',
                  borderRadius: '4px',
                }}>
                  已选择
                </span>
              )}
            </div>
            <div style={{
              color: '#fff',
              fontSize: '14px',
              marginBottom: '8px',
              lineHeight: '1.5',
            }}>
              "{foxSuggestion.suggestion}"
            </div>
            <div style={{
              color: '#888',
              fontSize: '12px',
              fontStyle: 'italic',
            }}>
              {foxSuggestion.reasoning}
            </div>
          </div>
        )}

        {/* 天平建议（如果存在） */}
        {balanceSuggestion && (
          <div
            onClick={() => setSelectedAdvisor(selectedAdvisor === 'balance' ? null : 'balance')}
            style={{
              marginBottom: '16px',
              padding: '16px',
              backgroundColor: selectedAdvisor === 'balance' ? '#0a1a0a' : '#1a1a2e',
              borderRadius: '12px',
              border: `2px solid ${selectedAdvisor === 'balance' ? '#22c55e' : '#333'}`,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '12px',
            }}>
              <span style={{ fontSize: '24px' }}>⚖️</span>
              <span style={{ color: '#22c55e', fontWeight: 'bold' }}>天平 (Libra)</span>
              {selectedAdvisor === 'balance' && (
                <span style={{
                  marginLeft: 'auto',
                  color: '#22c55e',
                  fontSize: '12px',
                  padding: '2px 8px',
                  backgroundColor: '#22c55e20',
                  borderRadius: '4px',
                }}>
                  已选择
                </span>
              )}
            </div>
            <div style={{
              color: '#fff',
              fontSize: '14px',
              marginBottom: '8px',
              lineHeight: '1.5',
            }}>
              "{balanceSuggestion.suggestion}"
            </div>
            <div style={{
              color: '#888',
              fontSize: '12px',
              fontStyle: 'italic',
            }}>
              {balanceSuggestion.reasoning}
            </div>
          </div>
        )}

        {/* 顾问关系状态 */}
        <div style={{
          marginTop: '24px',
          padding: '16px',
          backgroundColor: '#1a1a2e',
          borderRadius: '8px',
          border: '1px solid #333',
        }}>
          <h4 style={{
            margin: '0 0 12px 0',
            color: '#888',
            fontSize: '12px',
          }}>
            顾问关系
          </h4>
          <RobotCard
            type="lion"
            response=""
            relation={gameState.relations.lion}
            compact
          />
          <RobotCard
            type="fox"
            response=""
            relation={gameState.relations.fox}
            compact
          />
          <RobotCard
            type="balance"
            response=""
            relation={gameState.relations.balance}
            compact
          />
        </div>
      </div>
    </div>
  );
}
