// 主游戏面板组件 - 浅色米色主题

import { useState, useRef, useEffect } from 'react';
import { PowerMeter } from './PowerMeter';
import { theme, SPEAKER_CONFIG_LIGHT } from '../theme';
import { gameApi } from '../api/gameApi';
import type { GameState, ChapterScene, DialogueEntry, DecisionResult, DecreeConsequence } from '../types/game';

interface GameBoardProps {
  gameState: GameState;
  currentChapter: ChapterScene;
  dialogueHistory: DialogueEntry[];
  isLoading: boolean;
  sessionId: string;
  apiKey: string;
  model?: string;
  onSubmitDecision: (input: string, followedAdvisor?: string) => Promise<DecisionResult | null>;
  onPrivateAudience?: (advisor: string, message: string) => Promise<string | null>;
  onNextChapter?: () => Promise<void>;
  onSkipConsequences?: (consequences: DecreeConsequence[]) => void;
  onContinueWithConsequences?: (consequences: DecreeConsequence[]) => void;
  onEndChapterEarly?: (pendingConsequences: DecreeConsequence[]) => void;
  onUpdateGameState?: (state: GameState) => void;
}

// 游戏模式
type GameMode = 'council' | 'private_audience' | 'decree_result';

// 发布政令时的场景话语（移到组件外部避免重新创建）
const DECREE_SCENE_MESSAGES = [
  { icon: '📜', text: '政令正在拟定...', sub: '书吏们奋笔疾书' },
  { icon: '🏛️', text: '政令已送往各部...', sub: '大臣们正在传阅' },
  { icon: '⚔️', text: '门外士兵列队等候...', sub: '准备传令四方' },
  { icon: '🐎', text: '快马已备好...', sub: '信使整装待发' },
  { icon: '👥', text: '各方势力正在观望...', sub: '权衡利弊得失' },
  { icon: '🎭', text: '朝野上下议论纷纷...', sub: '风向悄然变化' },
  { icon: '⏳', text: '等待各方回应...', sub: '命运的车轮开始转动' },
];

export function GameBoard({
  gameState,
  currentChapter,
  dialogueHistory,
  isLoading,
  sessionId,
  apiKey,
  model,
  onSubmitDecision,
  onPrivateAudience,
  onNextChapter,
  onSkipConsequences,
  onContinueWithConsequences,
  onEndChapterEarly: _onEndChapterEarly, // 保留但标记为未使用（将来可能用于父组件回调）
  onUpdateGameState,
}: GameBoardProps) {
  const [gameMode, setGameMode] = useState<GameMode>('council');
  const [privateTarget, setPrivateTarget] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [decreeInput, setDecreeInput] = useState('');
  const [showDecreeModal, setShowDecreeModal] = useState(false);
  const [lastResult, setLastResult] = useState<DecisionResult | null>(null);
  const [privateMessages, setPrivateMessages] = useState<DialogueEntry[]>([]);
  const [privateLoading, setPrivateLoading] = useState(false);

  // 当前正在处理的后果
  const [activeConsequences, setActiveConsequences] = useState<DecreeConsequence[]>([]);

  // 保存最后发布的政令内容（用于继续回合时传递给API）
  const [lastDecreeContent, setLastDecreeContent] = useState<string>('');

  const historyEndRef = useRef<HTMLDivElement>(null);

  // 自动滚动到底部
  useEffect(() => {
    historyEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [dialogueHistory, privateMessages]);

  // 从 council_debate 获取顾问建议
  const councilDebate = currentChapter.council_debate;

  // 廷议中与顾问讨论
  const [councilLoading, setCouncilLoading] = useState(false);
  const [councilMessages, setCouncilMessages] = useState<DialogueEntry[]>([]);

  // 廷议气氛状态（用于未来的 UI 增强）
  // @ts-ignore - 保留供未来使用
  const [councilAtmosphere, setCouncilAtmosphere] = useState<string>('neutral');

  // 提前结束关卡确认弹窗
  const [showEndChapterConfirm, setShowEndChapterConfirm] = useState(false);
  const [endingChapter, setEndingChapter] = useState(false);

  // 正在加载下一关
  const [loadingNextChapter, setLoadingNextChapter] = useState(false);

  // 发布政令加载状态和场景话语索引
  const [decreeLoading, setDecreeLoading] = useState(false);
  const [decreeSceneIndex, setDecreeSceneIndex] = useState(0);

  // 政令加载时循环显示场景话语
  useEffect(() => {
    if (decreeLoading) {
      const interval = setInterval(() => {
        setDecreeSceneIndex(prev => (prev + 1) % DECREE_SCENE_MESSAGES.length);
      }, 2000); // 每2秒切换一次
      return () => clearInterval(interval);
    } else {
      setDecreeSceneIndex(0);
    }
  }, [decreeLoading]);

  const handleCouncilDiscuss = async () => {
    if (!input.trim() || councilLoading || !sessionId || !apiKey) return;

    const userMessage = input.trim();
    setInput('');
    setCouncilLoading(true);

    const playerMsg: DialogueEntry = {
      turn: currentChapter.current_turn,
      speaker: 'player',
      content: userMessage
    };
    setCouncilMessages(prev => [...prev, playerMsg]);

    try {
      // 使用新的 councilChat API 来分析玩家意图并生成回应
      const result = await gameApi.councilChat(
        sessionId,
        userMessage,
        councilMessages.map(m => ({ speaker: m.speaker, content: m.content })),
        apiKey,
        model
      );

      if (result.success) {
        // 添加顾问回应
        const responses = result.responses;
        const lionResponse = responses.lion;
        const foxResponse = responses.fox;
        const balanceResponse = responses.balance;

        if (lionResponse) {
          setCouncilMessages(prev => [...prev, {
            turn: currentChapter.current_turn,
            speaker: 'lion' as const,
            content: lionResponse
          }]);
        }
        if (foxResponse) {
          setCouncilMessages(prev => [...prev, {
            turn: currentChapter.current_turn,
            speaker: 'fox' as const,
            content: foxResponse
          }]);
        }
        if (balanceResponse) {
          setCouncilMessages(prev => [...prev, {
            turn: currentChapter.current_turn,
            speaker: 'balance' as const,
            content: balanceResponse
          }]);
        }

        // 更新廷议气氛（供将来使用）
        if (result.atmosphere) {
          setCouncilAtmosphere(result.atmosphere);
        }

        // 如果触发了冲突，显示冲突描述
        if (result.conflict_triggered && result.conflict_description) {
          setCouncilMessages(prev => [...prev, {
            turn: currentChapter.current_turn,
            speaker: 'system',
            content: `⚡ ${result.conflict_description}`
          }]);
        }

        // 更新游戏状态（信任度变化）
        if (onUpdateGameState && result.state) {
          onUpdateGameState(result.state);
        }
      }
    } catch (error) {
      console.error('廷议讨论失败:', error);
      // 回退到旧逻辑
      if (onPrivateAudience) {
        const advisors = ['lion', 'fox', 'balance'] as const;
        for (const advisor of advisors) {
          const response = await onPrivateAudience(advisor, userMessage);
          if (response) {
            setCouncilMessages(prev => [...prev, {
              turn: currentChapter.current_turn,
              speaker: advisor,
              content: response
            }]);
          }
        }
      }
    } finally {
      setCouncilLoading(false);
    }
  };

  // 发布政令
  const handleDecree = async () => {
    if (!decreeInput.trim() || isLoading || decreeLoading) return;

    // 保存政令内容用于后续继续回合
    const currentDecree = decreeInput.trim();
    setLastDecreeContent(currentDecree);

    // 开始加载状态，显示场景话语
    setDecreeLoading(true);

    try {
      const result = await onSubmitDecision(currentDecree);
      if (result) {
        // 后端会返回 decree_consequences，由 AI 基于《君主论》原则分析生成
        setLastResult(result);
        setGameMode('decree_result');
      }
    } finally {
      setDecreeLoading(false);
    }
    setDecreeInput('');
    setShowDecreeModal(false);
    setCouncilMessages([]);
  };

  // 开始密谈
  const handleStartPrivateAudience = (advisor: string) => {
    setPrivateTarget(advisor);
    setPrivateMessages([]);
    setGameMode('private_audience');
  };

  // 结束密谈
  const handleEndPrivateAudience = () => {
    setPrivateTarget(null);
    setPrivateMessages([]);
    setGameMode('council');
  };

  // 发送密谈消息
  const handlePrivateMessage = async () => {
    if (!input.trim() || privateLoading || !privateTarget) return;

    const userMessage = input.trim();

    const playerMsg: DialogueEntry = {
      turn: currentChapter.current_turn,
      speaker: 'player',
      content: userMessage
    };
    setPrivateMessages(prev => [...prev, playerMsg]);
    setInput('');
    setPrivateLoading(true);

    try {
      if (onPrivateAudience) {
        const response = await onPrivateAudience(privateTarget, userMessage);
        if (response) {
          const advisorResponse: DialogueEntry = {
            turn: currentChapter.current_turn,
            speaker: privateTarget as 'lion' | 'fox' | 'balance',
            content: response
          };
          setPrivateMessages(prev => [...prev, advisorResponse]);
        }
      }
    } catch (error) {
      console.error('密谈失败:', error);
    } finally {
      setPrivateLoading(false);
    }
  };

  // 继续当前回合时的场景更新状态
  const [sceneUpdate, setSceneUpdate] = useState<string>('');
  const [newDilemma, setNewDilemma] = useState<string>('');
  const [newAdvisorComments, setNewAdvisorComments] = useState<Record<string, { stance: string; comment: string; suggestion?: string }>>({});

  // 进入下一个场景（继续处理影响）
  const handleNextScene = async () => {
    if (!sessionId || !apiKey) {
      // 回退到旧逻辑
      if (lastResult?.decree_consequences && lastResult.decree_consequences.length > 0) {
        setActiveConsequences(lastResult.decree_consequences);
        if (onContinueWithConsequences) {
          onContinueWithConsequences(lastResult.decree_consequences);
        }
      }
      setLastResult(null);
      setGameMode('council');
      return;
    }

    // 保存当前的后果到活动后果列表
    const consequences = lastResult?.decree_consequences || [];
    if (consequences.length > 0) {
      setActiveConsequences(consequences);
    }

    try {
      // 调用 continueRound API 获取新场景和顾问评论
      // 使用保存的政令内容
      console.log('调用 continueRound API...', { sessionId, lastDecreeContent, consequences });

      const result = await gameApi.continueRound(
        sessionId,
        lastDecreeContent || '上一轮政令',
        consequences,
        apiKey,
        model
      );

      console.log('continueRound API 返回:', result);

      if (result.success) {
        // 设置新场景更新
        console.log('设置场景更新:', result.scene_update);
        console.log('设置新困境:', result.new_dilemma);
        console.log('设置顾问评论:', result.advisor_comments);

        setSceneUpdate(result.scene_update || '');
        setNewDilemma(result.new_dilemma || '');
        setNewAdvisorComments(result.advisor_comments || {});

        // 更新游戏状态
        if (onUpdateGameState && result.state) {
          onUpdateGameState(result.state);
        }

        // 通知父组件
        if (onContinueWithConsequences && consequences.length > 0) {
          onContinueWithConsequences(consequences);
        }
      } else {
        console.error('continueRound API 返回失败');
      }
    } catch (error) {
      console.error('继续回合失败:', error);
    }

    setLastResult(null);
    setGameMode('council');
    setCouncilMessages([]);  // 清空之前的廷议对话
  };

  // 提前结束关卡
  const handleEndChapterEarly = async () => {
    if (!sessionId || !apiKey) {
      setShowEndChapterConfirm(false);
      return;
    }

    setEndingChapter(true);

    try {
      // 收集所有未处理的后果
      const allPendingConsequences = [
        ...activeConsequences,
        ...(lastResult?.decree_consequences || []),
      ];

      const result = await gameApi.endChapterEarly(
        sessionId,
        allPendingConsequences,
        apiKey,
        model
      );

      if (result.success) {
        // 更新游戏状态
        if (onUpdateGameState && result.state) {
          onUpdateGameState(result.state);
        }

        // 通知父组件跳过后果
        if (onSkipConsequences && allPendingConsequences.length > 0) {
          onSkipConsequences(allPendingConsequences);
        }

        // 如果有下一关，进入下一关
        if (result.next_chapter_available && onNextChapter) {
          onNextChapter();
        }
      }
    } catch (error) {
      console.error('提前结束关卡失败:', error);
    } finally {
      setEndingChapter(false);
      setShowEndChapterConfirm(false);
    }
  };

  // 过滤对话历史
  const filteredDialogueHistory = dialogueHistory.filter(
    entry => entry.speaker !== 'system'
  );

  // 渲染顾问头像
  const renderAdvisorAvatars = () => (
    <div style={{
      position: 'absolute',
      right: '20px',
      top: '50%',
      transform: 'translateY(-50%)',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px',
      zIndex: 10,
    }}>
      {(['lion', 'fox', 'balance'] as const).map((advisor) => {
        const config = SPEAKER_CONFIG_LIGHT[advisor];
        const relationData = gameState.relations[advisor as keyof typeof gameState.relations];
        const trustValue = relationData?.trust ?? 50;
        const isSelected = privateTarget === advisor;

        return (
          <div
            key={advisor}
            onClick={() => gameMode === 'council' && handleStartPrivateAudience(advisor)}
            style={{
              width: '60px',
              height: '60px',
              borderRadius: '50%',
              backgroundColor: isSelected ? config.bgColor : theme.bg.card,
              border: `3px solid ${config.color}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: gameMode === 'council' ? 'pointer' : 'default',
              transition: 'all 0.3s ease',
              boxShadow: isSelected ? `0 0 20px ${config.color}40` : theme.shadow.md,
              opacity: gameMode === 'private_audience' && !isSelected ? 0.4 : 1,
            }}
            title={`单独召见${config.name} (信任: ${trustValue})`}
          >
            <span style={{ fontSize: '28px' }}>{config.icon}</span>
          </div>
        );
      })}

      {gameMode === 'council' && (
        <div style={{
          fontSize: '11px',
          color: theme.text.muted,
          textAlign: 'center',
          marginTop: '8px',
        }}>
          点击召见
        </div>
      )}
    </div>
  );

  // 渲染廷议模式
  const renderCouncilMode = () => (
    <>
      {/* 顶部 */}
      <div style={{
        padding: '16px 20px',
        borderBottom: `1px solid ${theme.border.light}`,
        backgroundColor: theme.bg.card,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '16px' }}>🏛️</span>
          <span style={{ color: theme.accent.goldDark, fontSize: '14px', fontWeight: 'bold' }}>廷议进行中</span>
          <span style={{ color: theme.text.muted, fontSize: '12px' }}>与顾问讨论后发布政令</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* 提前结束关卡按钮 */}
          <button
            onClick={() => setShowEndChapterConfirm(true)}
            disabled={isLoading || gameState.game_over}
            style={{
              padding: '10px 16px',
              background: 'transparent',
              color: theme.text.secondary,
              border: `1px solid ${theme.border.medium}`,
              borderRadius: '8px',
              fontSize: '13px',
              cursor: isLoading || gameState.game_over ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s',
            }}
            title="提前结束当前关卡，进入下一关（未处理的影响将累积）"
          >
            ⏭️ 结束关卡
          </button>
          <button
            onClick={() => setShowDecreeModal(true)}
            disabled={isLoading || gameState.game_over}
            style={{
              padding: '10px 24px',
              background: isLoading || gameState.game_over
                ? theme.border.medium
                : `linear-gradient(135deg, ${theme.accent.gold} 0%, ${theme.accent.goldLight} 100%)`,
              color: isLoading || gameState.game_over ? theme.text.muted : '#FFFFFF',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 'bold',
              cursor: isLoading || gameState.game_over ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: isLoading || gameState.game_over ? 'none' : theme.shadow.md,
            }}
          >
            📜 发布政令
          </button>
        </div>
      </div>

      {/* 廷议对话区 */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px',
        paddingRight: '100px',
        backgroundColor: theme.bg.secondary,
      }}>
        {/* 当前正在处理的后果提示 */}
        {activeConsequences.length > 0 && (
          <div style={{
            marginBottom: '20px',
            padding: '16px',
            backgroundColor: '#FFF7ED',
            borderRadius: '12px',
            border: '1px solid #FDBA7440',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '12px',
            }}>
              <span style={{ fontSize: '18px' }}>🌊</span>
              <span style={{ color: '#C2410C', fontWeight: 'bold', fontSize: '14px' }}>
                正在处理政令后续影响
              </span>
              <button
                onClick={() => setActiveConsequences([])}
                style={{
                  marginLeft: 'auto',
                  padding: '4px 8px',
                  backgroundColor: 'transparent',
                  border: '1px solid #FDBA74',
                  borderRadius: '4px',
                  color: '#C2410C',
                  fontSize: '11px',
                  cursor: 'pointer',
                }}
              >
                清除
              </button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {activeConsequences.map((c, idx) => {
                const severityInfo = getSeverityInfo(c.severity);
                return (
                  <div key={c.id || idx} style={{
                    padding: '10px 12px',
                    backgroundColor: 'rgba(255,255,255,0.6)',
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}>
                    <span style={{ fontSize: '14px' }}>{getTypeIcon(c.type)}</span>
                    <span style={{ color: severityInfo.color, fontWeight: 'bold', fontSize: '13px' }}>
                      {c.title}
                    </span>
                    <span style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      backgroundColor: severityInfo.color,
                      color: '#FFF',
                      borderRadius: '3px',
                    }}>
                      {severityInfo.label}
                    </span>
                  </div>
                );
              })}
            </div>
            <div style={{
              marginTop: '12px',
              fontSize: '12px',
              color: theme.text.muted,
            }}>
              💡 请针对这些影响与顾问讨论，然后发布新政令来应对
            </div>
          </div>
        )}

        {/* 场景更新提示（来自继续回合） */}
        {sceneUpdate && (
          <div style={{
            marginBottom: '20px',
            padding: '16px',
            backgroundColor: '#EBF4FF',
            borderRadius: '12px',
            border: '1px solid #93C5FD40',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '10px',
            }}>
              <span style={{ fontSize: '18px' }}>🎭</span>
              <span style={{ color: '#1E40AF', fontWeight: 'bold', fontSize: '14px' }}>
                局势变化
              </span>
              <button
                onClick={() => setSceneUpdate('')}
                style={{
                  marginLeft: 'auto',
                  padding: '4px 8px',
                  backgroundColor: 'transparent',
                  border: '1px solid #93C5FD',
                  borderRadius: '4px',
                  color: '#1E40AF',
                  fontSize: '11px',
                  cursor: 'pointer',
                }}
              >
                关闭
              </button>
            </div>
            <p style={{
              color: theme.text.secondary,
              fontSize: '14px',
              lineHeight: '1.7',
              margin: 0,
            }}>
              {sceneUpdate}
            </p>
            {newDilemma && (
              <div style={{
                marginTop: '12px',
                padding: '10px 12px',
                backgroundColor: 'rgba(255,255,255,0.6)',
                borderRadius: '6px',
                border: '1px solid #93C5FD30',
              }}>
                <div style={{ fontSize: '12px', color: '#1E40AF', marginBottom: '4px', fontWeight: 'bold' }}>
                  📋 新的问题
                </div>
                <div style={{ fontSize: '13px', color: theme.text.secondary }}>
                  {newDilemma}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 顾问针对上轮政令的新观点（来自继续回合） */}
        {Object.keys(newAdvisorComments).length > 0 && (
          <div style={{
            marginBottom: '24px',
            padding: '20px',
            backgroundColor: '#FEF3C7',
            borderRadius: '12px',
            border: `1px solid ${theme.accent.gold}30`,
            boxShadow: theme.shadow.sm,
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '16px',
            }}>
              <span style={{ fontSize: '16px' }}>💬</span>
              <span style={{ color: theme.accent.goldDark, fontWeight: 'bold', fontSize: '14px' }}>
                顾问们对上轮政令的反馈
              </span>
              <button
                onClick={() => setNewAdvisorComments({})}
                style={{
                  marginLeft: 'auto',
                  padding: '4px 8px',
                  backgroundColor: 'transparent',
                  border: `1px solid ${theme.accent.gold}`,
                  borderRadius: '4px',
                  color: theme.accent.goldDark,
                  fontSize: '11px',
                  cursor: 'pointer',
                }}
              >
                关闭
              </button>
            </div>

            {newAdvisorComments.lion && (
              <div style={{ marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <span style={{ fontSize: '18px' }}>🦁</span>
                  <span style={{ color: theme.advisor.lion, fontWeight: 'bold', fontSize: '13px' }}>狮子</span>
                  {newAdvisorComments.lion.stance && (
                    <span style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      backgroundColor: newAdvisorComments.lion.stance === '支持' ? '#D1FAE5' :
                        newAdvisorComments.lion.stance === '反对' ? '#FEE2E2' : '#F3F4F6',
                      color: newAdvisorComments.lion.stance === '支持' ? '#059669' :
                        newAdvisorComments.lion.stance === '反对' ? '#DC2626' : '#6B7280',
                      borderRadius: '3px',
                    }}>
                      {newAdvisorComments.lion.stance}
                    </span>
                  )}
                </div>
                <div style={{ color: theme.text.secondary, fontSize: '13px', lineHeight: '1.6', paddingLeft: '26px' }}>
                  "{newAdvisorComments.lion.comment}"
                </div>
                {newAdvisorComments.lion.suggestion && (
                  <div style={{
                    marginTop: '6px',
                    paddingLeft: '26px',
                    fontSize: '12px',
                    color: theme.advisor.lion,
                  }}>
                    💡 {newAdvisorComments.lion.suggestion}
                  </div>
                )}
              </div>
            )}

            {newAdvisorComments.fox && (
              <div style={{ marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <span style={{ fontSize: '18px' }}>🦊</span>
                  <span style={{ color: theme.advisor.fox, fontWeight: 'bold', fontSize: '13px' }}>狐狸</span>
                  {newAdvisorComments.fox.stance && (
                    <span style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      backgroundColor: newAdvisorComments.fox.stance === '支持' ? '#D1FAE5' :
                        newAdvisorComments.fox.stance === '反对' ? '#FEE2E2' : '#F3F4F6',
                      color: newAdvisorComments.fox.stance === '支持' ? '#059669' :
                        newAdvisorComments.fox.stance === '反对' ? '#DC2626' : '#6B7280',
                      borderRadius: '3px',
                    }}>
                      {newAdvisorComments.fox.stance}
                    </span>
                  )}
                </div>
                <div style={{ color: theme.text.secondary, fontSize: '13px', lineHeight: '1.6', paddingLeft: '26px' }}>
                  "{newAdvisorComments.fox.comment}"
                </div>
                {newAdvisorComments.fox.suggestion && (
                  <div style={{
                    marginTop: '6px',
                    paddingLeft: '26px',
                    fontSize: '12px',
                    color: theme.advisor.fox,
                  }}>
                    💡 {newAdvisorComments.fox.suggestion}
                  </div>
                )}
              </div>
            )}

            {newAdvisorComments.balance && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <span style={{ fontSize: '18px' }}>⚖️</span>
                  <span style={{ color: theme.advisor.balance, fontWeight: 'bold', fontSize: '13px' }}>天平</span>
                  {newAdvisorComments.balance.stance && (
                    <span style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      backgroundColor: newAdvisorComments.balance.stance === '支持' ? '#D1FAE5' :
                        newAdvisorComments.balance.stance === '反对' ? '#FEE2E2' : '#F3F4F6',
                      color: newAdvisorComments.balance.stance === '支持' ? '#059669' :
                        newAdvisorComments.balance.stance === '反对' ? '#DC2626' : '#6B7280',
                      borderRadius: '3px',
                    }}>
                      {newAdvisorComments.balance.stance}
                    </span>
                  )}
                </div>
                <div style={{ color: theme.text.secondary, fontSize: '13px', lineHeight: '1.6', paddingLeft: '26px' }}>
                  "{newAdvisorComments.balance.comment}"
                </div>
                {newAdvisorComments.balance.suggestion && (
                  <div style={{
                    marginTop: '6px',
                    paddingLeft: '26px',
                    fontSize: '12px',
                    color: theme.advisor.balance,
                  }}>
                    💡 {newAdvisorComments.balance.suggestion}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* 顾问建议（初始建议） */}
        {councilDebate && !sceneUpdate && Object.keys(newAdvisorComments).length === 0 && (
          <div style={{
            marginBottom: '24px',
            padding: '20px',
            backgroundColor: theme.bg.card,
            borderRadius: '12px',
            border: `1px solid ${theme.border.light}`,
            boxShadow: theme.shadow.sm,
          }}>
            {councilDebate.lion && (
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <span style={{ fontSize: '20px' }}>🦁</span>
                  <span style={{ color: theme.advisor.lion, fontWeight: 'bold', fontSize: '13px' }}>狮子</span>
                </div>
                <div style={{ color: theme.text.secondary, fontSize: '14px', lineHeight: '1.6', paddingLeft: '28px' }}>
                  "{councilDebate.lion.suggestion}"
                </div>
              </div>
            )}

            {councilDebate.fox && (
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <span style={{ fontSize: '20px' }}>🦊</span>
                  <span style={{ color: theme.advisor.fox, fontWeight: 'bold', fontSize: '13px' }}>狐狸</span>
                </div>
                <div style={{ color: theme.text.secondary, fontSize: '14px', lineHeight: '1.6', paddingLeft: '28px' }}>
                  "{councilDebate.fox.suggestion}"
                </div>
              </div>
            )}

            {councilDebate.balance && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                  <span style={{ fontSize: '20px' }}>⚖️</span>
                  <span style={{ color: theme.advisor.balance, fontWeight: 'bold', fontSize: '13px' }}>天平</span>
                </div>
                <div style={{ color: theme.text.secondary, fontSize: '14px', lineHeight: '1.6', paddingLeft: '28px' }}>
                  "{councilDebate.balance.suggestion}"
                </div>
              </div>
            )}
          </div>
        )}

        {/* 对话历史 */}
        {filteredDialogueHistory.map((entry, index) => {
          const config = SPEAKER_CONFIG_LIGHT[entry.speaker] || SPEAKER_CONFIG_LIGHT.system;
          const isPlayer = entry.speaker === 'player';

          return (
            <div
              key={index}
              style={{
                marginBottom: '16px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: isPlayer ? 'flex-end' : 'flex-start',
              }}
            >
              <div style={{
                display: 'flex',
                alignItems: 'center',
                marginBottom: '4px',
                gap: '4px',
              }}>
                <span style={{ fontSize: '14px' }}>{config.icon}</span>
                <span style={{ color: config.color, fontSize: '12px', fontWeight: 'bold' }}>
                  {config.name}
                </span>
              </div>

              <div style={{
                maxWidth: '80%',
                padding: '12px 16px',
                borderRadius: '12px',
                backgroundColor: isPlayer ? '#E8F4FD' : theme.bg.card,
                color: theme.text.primary,
                fontSize: '14px',
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap',
                border: `1px solid ${isPlayer ? '#B3D9F7' : theme.border.light}`,
                boxShadow: theme.shadow.sm,
              }}>
                {entry.content}
              </div>
            </div>
          );
        })}

        {/* 廷议讨论消息 */}
        {councilMessages.map((entry, index) => {
          const config = SPEAKER_CONFIG_LIGHT[entry.speaker] || SPEAKER_CONFIG_LIGHT.system;
          const isPlayer = entry.speaker === 'player';

          return (
            <div
              key={`council-${index}`}
              style={{
                marginBottom: '16px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: isPlayer ? 'flex-end' : 'flex-start',
              }}
            >
              <div style={{
                display: 'flex',
                alignItems: 'center',
                marginBottom: '4px',
                gap: '4px',
              }}>
                <span style={{ fontSize: '14px' }}>{config.icon}</span>
                <span style={{ color: config.color, fontSize: '12px', fontWeight: 'bold' }}>
                  {config.name}
                </span>
              </div>

              <div style={{
                maxWidth: '80%',
                padding: '12px 16px',
                borderRadius: '12px',
                backgroundColor: isPlayer ? '#E8F4FD' : config.bgColor,
                color: theme.text.primary,
                fontSize: '14px',
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap',
                border: `1px solid ${isPlayer ? '#B3D9F7' : theme.border.light}`,
                boxShadow: theme.shadow.sm,
              }}>
                {entry.content}
              </div>
            </div>
          );
        })}

        {(isLoading || councilLoading) && (
          <div style={{ textAlign: 'center', color: theme.text.muted, padding: '20px' }}>
            <span>顾问们正在思考...</span>
          </div>
        )}

        <div ref={historyEndRef} />
      </div>

      {renderAdvisorAvatars()}

      {/* 底部输入区 */}
      <div style={{
        padding: '16px 20px',
        borderTop: `1px solid ${theme.border.light}`,
        backgroundColor: theme.bg.card,
      }}>
        <div style={{ color: theme.text.muted, fontSize: '12px', marginBottom: '8px' }}>
          💬 与顾问讨论（点击右侧头像可单独召见，或直接输入与所有顾问对话）
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleCouncilDiscuss()}
            placeholder="向顾问们提问或讨论..."
            disabled={isLoading || gameState.game_over}
            style={{
              flex: 1,
              padding: '12px 16px',
              backgroundColor: theme.bg.input,
              border: `1px solid ${theme.border.medium}`,
              borderRadius: '8px',
              color: theme.text.primary,
              fontSize: '14px',
              outline: 'none',
            }}
          />
          <button
            onClick={handleCouncilDiscuss}
            disabled={isLoading || gameState.game_over || !input.trim()}
            style={{
              padding: '12px 20px',
              backgroundColor: isLoading || gameState.game_over || !input.trim() ? theme.border.medium : theme.status.info,
              color: isLoading || gameState.game_over || !input.trim() ? theme.text.muted : '#FFFFFF',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              cursor: isLoading || gameState.game_over || !input.trim() ? 'not-allowed' : 'pointer',
            }}
          >
            {councilLoading ? '...' : '发送'}
          </button>
        </div>
      </div>
    </>
  );

  // 渲染密谈模式
  const renderPrivateAudienceMode = () => {
    if (!privateTarget) return null;
    const config = SPEAKER_CONFIG_LIGHT[privateTarget];

    return (
      <>
        <div style={{
          padding: '16px 20px',
          backgroundColor: config.bgColor,
          borderBottom: `2px solid ${config.color}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '32px' }}>{config.icon}</span>
            <div>
              <div style={{ color: config.color, fontSize: '18px', fontWeight: 'bold' }}>
                单独召见 - {config.name}
              </div>
              <div style={{ color: theme.text.muted, fontSize: '12px' }}>
                私密对话中... 其他顾问无法听到
              </div>
            </div>
          </div>
          <button
            onClick={handleEndPrivateAudience}
            style={{
              padding: '8px 16px',
              backgroundColor: theme.bg.card,
              color: theme.text.primary,
              border: `1px solid ${theme.border.medium}`,
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '13px',
            }}
          >
            结束密谈
          </button>
        </div>

        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          paddingRight: '100px',
          backgroundColor: theme.bg.secondary,
        }}>
          {privateMessages.length === 0 && (
            <div style={{
              textAlign: 'center',
              color: theme.text.muted,
              padding: '40px 20px',
              fontSize: '14px',
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>{config.icon}</div>
              <div>"{config.name}恭敬地等待您的问话..."</div>
              <div style={{
                marginTop: '16px',
                padding: '16px',
                backgroundColor: theme.bg.card,
                borderRadius: '8px',
                fontSize: '12px',
                color: theme.text.secondary,
                textAlign: 'left',
                border: `1px solid ${theme.border.light}`,
              }}>
                <div style={{ marginBottom: '8px', color: config.color, fontWeight: 'bold' }}>💡 密谈提示：</div>
                {privateTarget === 'lion' && (
                  <div>狮子崇尚武力与威慑，相信"宁可被人畏惧，也不要被人爱戴"。在密谈中，他可能会透露一些强硬的建议...</div>
                )}
                {privateTarget === 'fox' && (
                  <div>狐狸精通权谋与欺诈，相信"目的可以证明手段正当"。在密谈中，他可能会提供一些...不太光明的计策...</div>
                )}
                {privateTarget === 'balance' && (
                  <div>天平追求公正与稳定，相信"明智的君主应当建立在人民的支持之上"。在密谈中，他会给出更为中庸的建议...</div>
                )}
              </div>
            </div>
          )}

          {privateMessages.map((entry, index) => {
            const msgConfig = SPEAKER_CONFIG_LIGHT[entry.speaker];
            const isPlayer = entry.speaker === 'player';

            return (
              <div
                key={index}
                style={{
                  marginBottom: '16px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: isPlayer ? 'flex-end' : 'flex-start',
                }}
              >
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  marginBottom: '4px',
                  gap: '4px',
                }}>
                  <span style={{ fontSize: '14px' }}>{msgConfig.icon}</span>
                  <span style={{ color: msgConfig.color, fontSize: '12px', fontWeight: 'bold' }}>
                    {msgConfig.name}
                  </span>
                </div>

                <div style={{
                  maxWidth: '80%',
                  padding: '12px 16px',
                  borderRadius: '12px',
                  backgroundColor: isPlayer ? '#E8F4FD' : config.bgColor,
                  color: theme.text.primary,
                  fontSize: '14px',
                  lineHeight: '1.6',
                  border: `1px solid ${isPlayer ? '#B3D9F7' : theme.border.light}`,
                  whiteSpace: 'pre-wrap',
                  boxShadow: theme.shadow.sm,
                }}>
                  {entry.content}
                </div>
              </div>
            );
          })}

          {privateLoading && (
            <div style={{ textAlign: 'center', color: config.color, padding: '20px' }}>
              <span>{config.name}正在思考...</span>
            </div>
          )}

          <div ref={historyEndRef} />
        </div>

        {renderAdvisorAvatars()}

        <div style={{
          padding: '16px 20px',
          borderTop: `1px solid ${theme.border.light}`,
          backgroundColor: theme.bg.card,
        }}>
          <div style={{ display: 'flex', gap: '12px' }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handlePrivateMessage()}
              placeholder={`与${config.name}密谈...`}
              disabled={privateLoading}
              style={{
                flex: 1,
                padding: '12px 16px',
                backgroundColor: theme.bg.input,
                border: `1px solid ${config.color}40`,
                borderRadius: '8px',
                color: theme.text.primary,
                fontSize: '14px',
                outline: 'none',
              }}
            />
            <button
              onClick={handlePrivateMessage}
              disabled={privateLoading || !input.trim()}
              style={{
                padding: '12px 24px',
                backgroundColor: privateLoading || !input.trim() ? theme.border.medium : config.color,
                color: privateLoading || !input.trim() ? theme.text.muted : '#FFFFFF',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: 'bold',
                cursor: privateLoading || !input.trim() ? 'not-allowed' : 'pointer',
              }}
            >
              {privateLoading ? '...' : '发送'}
            </button>
          </div>
        </div>
      </>
    );
  };

  // 获取影响严重程度的颜色和图标
  const getSeverityInfo = (severity: string) => {
    switch (severity) {
      case 'critical': return { color: '#DC2626', bgColor: '#FEE2E2', icon: '🔥', label: '危急' };
      case 'high': return { color: '#EA580C', bgColor: '#FFEDD5', icon: '⚠️', label: '严重' };
      case 'medium': return { color: '#D97706', bgColor: '#FEF3C7', icon: '📢', label: '中等' };
      default: return { color: '#059669', bgColor: '#D1FAE5', icon: '📋', label: '轻微' };
    }
  };

  // 获取影响类型的图标
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'political': return '🏛️';
      case 'economic': return '💰';
      case 'military': return '⚔️';
      case 'social': return '👥';
      case 'diplomatic': return '🤝';
      default: return '📜';
    }
  };

  // 重置所有本地状态，准备进入新关卡
  const resetLocalState = () => {
    setLastResult(null);
    setGameMode('council');
    setActiveConsequences([]);
    setSceneUpdate('');
    setNewDilemma('');
    setNewAdvisorComments({});
    setCouncilMessages([]);
    setLastDecreeContent('');
    setPrivateMessages([]);
    setPrivateTarget(null);
    setInput('');
    setDecreeInput('');
    setShowDecreeModal(false);
  };

  // 处理跳过后续影响，直接进入下一关
  const handleSkipConsequences = async () => {
    if (lastResult?.decree_consequences && onSkipConsequences) {
      onSkipConsequences(lastResult.decree_consequences);
    }

    // 显示加载状态
    setLoadingNextChapter(true);

    // 重置游戏模式和状态，准备进入下一关
    resetLocalState();

    if (onNextChapter) {
      await onNextChapter();
    }

    setLoadingNextChapter(false);
  };

  // 处理进入下一关（关卡结束后）
  const handleGoToNextChapter = async () => {
    // 显示加载状态
    setLoadingNextChapter(true);

    // 重置游戏模式和状态
    resetLocalState();

    if (onNextChapter) {
      await onNextChapter();
    }

    setLoadingNextChapter(false);
  };

  // 渲染政令结果
  const renderDecreeResult = () => {
    if (!lastResult) return null;

    // 判断关卡是否结束
    const chapterEnded = lastResult.chapter_result?.chapter_ended;
    const hasNextChapter = lastResult.next_chapter_available;
    const isVictory = lastResult.chapter_result?.victory;

    // 获取政令后续影响
    const consequences = lastResult.decree_consequences || [];
    const hasConsequences = consequences.length > 0;

    return (
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'flex-start',
        padding: '40px',
        overflowY: 'auto',
        backgroundColor: theme.bg.secondary,
      }}>
        <div style={{
          maxWidth: '700px',
          width: '100%',
          backgroundColor: theme.bg.card,
          borderRadius: '16px',
          border: `1px solid ${theme.border.light}`,
          padding: '32px',
          boxShadow: theme.shadow.lg,
        }}>
          <h2 style={{
            color: theme.accent.goldDark,
            fontSize: '24px',
            textAlign: 'center',
            marginBottom: '24px',
          }}>
            📜 政令已发布
          </h2>

          {/* 关卡结束提示 */}
          {chapterEnded && (
            <div style={{
              padding: '16px',
              marginBottom: '20px',
              borderRadius: '12px',
              backgroundColor: isVictory ? theme.status.successBg : theme.status.errorBg,
              border: `1px solid ${isVictory ? theme.status.success : theme.status.error}30`,
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>
                {isVictory ? '🎉' : '💀'}
              </div>
              <div style={{
                color: isVictory ? theme.status.success : theme.status.error,
                fontSize: '18px',
                fontWeight: 'bold',
              }}>
                {isVictory ? '关卡通过！' : '关卡失败'}
              </div>
              {lastResult.chapter_result?.reason && (
                <div style={{
                  color: theme.text.secondary,
                  fontSize: '14px',
                  marginTop: '8px',
                }}>
                  {lastResult.chapter_result.reason}
                </div>
              )}
            </div>
          )}

          {lastResult.judgment_metadata && (
            <div style={{
              backgroundColor: '#FEF3C7',
              borderRadius: '12px',
              padding: '20px',
              marginBottom: '20px',
              border: `1px solid ${theme.accent.gold}30`,
            }}>
              <h3 style={{ color: theme.accent.goldDark, fontSize: '16px', marginBottom: '16px' }}>
                📊 君主论审视
              </h3>
              <div style={{ color: theme.text.secondary, fontSize: '14px', lineHeight: '1.8' }}>
                <p style={{ fontStyle: 'italic', marginBottom: '16px' }}>
                  "{lastResult.judgment_metadata.machiavelli_critique}"
                </p>
                <div style={{ display: 'grid', gap: '8px' }}>
                  <div><span style={{ color: theme.text.muted }}>策略风格:</span> {lastResult.judgment_metadata.player_strategy}</div>
                  <div><span style={{ color: theme.text.muted }}>展现特质:</span> {lastResult.judgment_metadata.machiavelli_traits.join('、')}</div>
                  <div><span style={{ color: theme.text.muted }}>结局评级:</span> {lastResult.judgment_metadata.outcome_level}</div>
                </div>
              </div>
            </div>
          )}

          {lastResult.power_changes && (
            <div style={{
              backgroundColor: theme.bg.secondary,
              borderRadius: '12px',
              padding: '20px',
              marginBottom: '20px',
              border: `1px solid ${theme.border.light}`,
            }}>
              <h3 style={{ color: theme.text.secondary, fontSize: '14px', marginBottom: '12px' }}>
                权力变化
              </h3>
              <div style={{ display: 'flex', justifyContent: 'space-around' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ color: lastResult.power_changes.authority >= 0 ? theme.status.success : theme.status.error, fontSize: '20px', fontWeight: 'bold' }}>
                    {lastResult.power_changes.authority >= 0 ? '+' : ''}{lastResult.power_changes.authority}
                  </div>
                  <div style={{ color: theme.text.muted, fontSize: '12px' }}>权威</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ color: lastResult.power_changes.fear >= 0 ? theme.status.success : theme.status.error, fontSize: '20px', fontWeight: 'bold' }}>
                    {lastResult.power_changes.fear >= 0 ? '+' : ''}{lastResult.power_changes.fear}
                  </div>
                  <div style={{ color: theme.text.muted, fontSize: '12px' }}>恐惧</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ color: lastResult.power_changes.love >= 0 ? theme.status.success : theme.status.error, fontSize: '20px', fontWeight: 'bold' }}>
                    {lastResult.power_changes.love >= 0 ? '+' : ''}{lastResult.power_changes.love}
                  </div>
                  <div style={{ color: theme.text.muted, fontSize: '12px' }}>民心</div>
                </div>
              </div>
            </div>
          )}

          {lastResult.advisor_responses && (
            <div style={{
              backgroundColor: theme.bg.secondary,
              borderRadius: '12px',
              padding: '20px',
              marginBottom: '20px',
              border: `1px solid ${theme.border.light}`,
            }}>
              <h3 style={{ color: theme.text.secondary, fontSize: '14px', marginBottom: '12px' }}>
                顾问反应
              </h3>
              {lastResult.advisor_responses.lion && (
                <div style={{ marginBottom: '12px' }}>
                  <span style={{ color: theme.advisor.lion, fontWeight: 'bold' }}>🦁 狮子:</span>
                  <span style={{ color: theme.text.secondary, marginLeft: '8px' }}>{lastResult.advisor_responses.lion}</span>
                </div>
              )}
              {lastResult.advisor_responses.fox && (
                <div style={{ marginBottom: '12px' }}>
                  <span style={{ color: theme.advisor.fox, fontWeight: 'bold' }}>🦊 狐狸:</span>
                  <span style={{ color: theme.text.secondary, marginLeft: '8px' }}>{lastResult.advisor_responses.fox}</span>
                </div>
              )}
              {lastResult.advisor_responses.balance && (
                <div>
                  <span style={{ color: theme.advisor.balance, fontWeight: 'bold' }}>⚖️ 天平:</span>
                  <span style={{ color: theme.text.secondary, marginLeft: '8px' }}>{lastResult.advisor_responses.balance}</span>
                </div>
              )}
            </div>
          )}

          {/* 政令后续影响 */}
          {hasConsequences && (
            <div style={{
              backgroundColor: '#FFF7ED',
              borderRadius: '12px',
              padding: '20px',
              marginBottom: '20px',
              border: `1px solid #FDBA7440`,
            }}>
              <h3 style={{
                color: '#C2410C',
                fontSize: '16px',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}>
                🌊 政令后续影响
                <span style={{
                  fontSize: '12px',
                  fontWeight: 'normal',
                  color: theme.text.muted,
                }}>
                  （共 {consequences.length} 项需要关注）
                </span>
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {consequences.map((consequence, index) => {
                  const severityInfo = getSeverityInfo(consequence.severity);
                  const typeIcon = getTypeIcon(consequence.type);

                  return (
                    <div
                      key={consequence.id || index}
                      style={{
                        backgroundColor: severityInfo.bgColor,
                        borderRadius: '8px',
                        padding: '16px',
                        border: `1px solid ${severityInfo.color}30`,
                      }}
                    >
                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'flex-start',
                        marginBottom: '8px',
                      }}>
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                        }}>
                          <span style={{ fontSize: '18px' }}>{typeIcon}</span>
                          <span style={{
                            color: severityInfo.color,
                            fontWeight: 'bold',
                            fontSize: '14px',
                          }}>
                            {consequence.title}
                          </span>
                        </div>
                        <span style={{
                          fontSize: '11px',
                          padding: '2px 8px',
                          backgroundColor: severityInfo.color,
                          color: '#FFFFFF',
                          borderRadius: '4px',
                          fontWeight: 'bold',
                        }}>
                          {severityInfo.icon} {severityInfo.label}
                        </span>
                      </div>

                      <p style={{
                        color: theme.text.secondary,
                        fontSize: '13px',
                        lineHeight: '1.6',
                        margin: '0 0 12px 0',
                      }}>
                        {consequence.description}
                      </p>

                      {consequence.potential_outcomes && consequence.potential_outcomes.length > 0 && (
                        <div style={{
                          backgroundColor: 'rgba(255,255,255,0.5)',
                          borderRadius: '6px',
                          padding: '10px 12px',
                        }}>
                          <div style={{
                            fontSize: '11px',
                            color: theme.text.muted,
                            marginBottom: '6px',
                          }}>
                            可能的后果：
                          </div>
                          <ul style={{
                            margin: 0,
                            paddingLeft: '16px',
                            fontSize: '12px',
                            color: theme.text.secondary,
                          }}>
                            {consequence.potential_outcomes.map((outcome, i) => (
                              <li key={i} style={{ marginBottom: '4px' }}>{outcome}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {consequence.deadline_turns && (
                        <div style={{
                          marginTop: '10px',
                          fontSize: '11px',
                          color: severityInfo.color,
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}>
                          ⏰ 若不处理，将在 {consequence.deadline_turns} 回合后自动触发
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* 提示 */}
              <div style={{
                marginTop: '16px',
                padding: '12px',
                backgroundColor: 'rgba(255,255,255,0.6)',
                borderRadius: '8px',
                fontSize: '12px',
                color: theme.text.secondary,
                lineHeight: '1.6',
              }}>
                💡 <strong>提示：</strong>你可以选择继续处理这些影响，或者跳过它们直接进入下一关。
                跳过的影响将会累积，可能在后续关卡中以更严重的形式爆发。
              </div>
            </div>
          )}

          {/* 底部按钮区域 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {/* 有后续影响时的选项 */}
            {hasConsequences && !chapterEnded && (
              <>
                <button
                  onClick={handleNextScene}
                  style={{
                    width: '100%',
                    padding: '16px',
                    background: `linear-gradient(135deg, ${theme.accent.gold} 0%, ${theme.accent.goldLight} 100%)`,
                    color: '#FFFFFF',
                    border: 'none',
                    borderRadius: '10px',
                    fontSize: '16px',
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    boxShadow: theme.shadow.md,
                  }}
                >
                  🔄 继续处理影响
                </button>
                <button
                  onClick={handleSkipConsequences}
                  style={{
                    width: '100%',
                    padding: '14px',
                    background: theme.bg.secondary,
                    color: theme.text.secondary,
                    border: `1px solid ${theme.border.medium}`,
                    borderRadius: '10px',
                    fontSize: '14px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                  }}
                >
                  ⏭️ 跳过影响，进入下一关
                  <span style={{
                    fontSize: '11px',
                    color: theme.status.warning,
                  }}>
                    （影响将累积）
                  </span>
                </button>
              </>
            )}

            {/* 无后续影响且关卡未结束时 */}
            {!hasConsequences && !chapterEnded && (
              <button
                onClick={handleNextScene}
                style={{
                  width: '100%',
                  padding: '16px',
                  background: `linear-gradient(135deg, ${theme.accent.gold} 0%, ${theme.accent.goldLight} 100%)`,
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: '10px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  boxShadow: theme.shadow.md,
                }}
              >
                继续 →
              </button>
            )}

            {/* 关卡结束且有下一关时显示进入下一关按钮 */}
            {chapterEnded && hasNextChapter && onNextChapter && (
              <button
                onClick={handleGoToNextChapter}
                style={{
                  width: '100%',
                  padding: '16px',
                  background: `linear-gradient(135deg, ${theme.status.success} 0%, #38A169 100%)`,
                  color: '#FFFFFF',
                  border: 'none',
                  borderRadius: '10px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                  boxShadow: theme.shadow.md,
                }}
              >
                🚀 进入下一关
              </button>
            )}

            {/* 关卡结束但没有下一关（失败或通关）时返回关卡选择 */}
            {chapterEnded && !hasNextChapter && onNextChapter && (
              <button
                onClick={handleGoToNextChapter}
                style={{
                  width: '100%',
                  padding: '16px',
                  background: theme.bg.secondary,
                  color: theme.text.primary,
                  border: `1px solid ${theme.border.medium}`,
                  borderRadius: '10px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                }}
              >
                返回关卡选择
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '280px 1fr',
      gap: '0',
      height: 'calc(100vh - 60px)',
      backgroundColor: theme.bg.primary,
    }}>
      {/* 左侧栏 */}
      <div style={{
        backgroundColor: theme.bg.card,
        borderRight: `1px solid ${theme.border.light}`,
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
      }}>
        {/* 关卡信息 */}
        <div style={{
          padding: '16px',
          borderBottom: `1px solid ${theme.border.light}`,
          backgroundColor: '#FEF3C7',
        }}>
          <div style={{ color: theme.accent.goldDark, fontSize: '14px', fontWeight: 'bold', marginBottom: '4px' }}>
            📜 {currentChapter.name}
          </div>
          <div style={{ color: theme.text.muted, fontSize: '12px' }}>
            回合 {currentChapter.current_turn}/{currentChapter.max_turns}
          </div>
        </div>

        {/* 回合背景 */}
        <div style={{ padding: '16px', borderBottom: `1px solid ${theme.border.light}` }}>
          <h4 style={{ color: theme.text.secondary, fontSize: '12px', margin: '0 0 10px 0' }}>📖 当前困境</h4>
          <div style={{ color: theme.text.primary, fontSize: '13px', lineHeight: '1.7' }}>
            {currentChapter.dilemma}
          </div>
        </div>

        {/* 场景快照 */}
        {currentChapter.scene_snapshot && (
          <div style={{ padding: '16px', borderBottom: `1px solid ${theme.border.light}` }}>
            <h4 style={{ color: theme.text.secondary, fontSize: '12px', margin: '0 0 10px 0' }}>🎭 场景</h4>
            <div style={{ color: theme.text.secondary, fontSize: '12px', lineHeight: '1.6', fontStyle: 'italic' }}>
              {currentChapter.scene_snapshot}
            </div>
          </div>
        )}

        {/* 权力状态 */}
        <div style={{ padding: '16px', borderBottom: `1px solid ${theme.border.light}` }}>
          <h4 style={{ color: theme.text.secondary, fontSize: '12px', margin: '0 0 12px 0' }}>⚔️ 权力状态</h4>
          <PowerMeter power={gameState.power} hideValues={currentChapter.hide_values} compact />

          <div style={{
            marginTop: '12px',
            padding: '10px',
            backgroundColor: theme.bg.secondary,
            borderRadius: '6px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <span style={{ color: theme.text.muted, fontSize: '12px' }}>💳 信用</span>
            <span style={{
              color: gameState.credit_score > 50 ? theme.status.success : gameState.credit_score > 20 ? theme.status.warning : theme.status.error,
              fontSize: '14px',
              fontWeight: 'bold',
            }}>
              {gameState.credit_score.toFixed(0)}
            </span>
          </div>

          {(gameState.active_promises > 0 || gameState.leverages_against_you > 0) && (
            <div style={{ marginTop: '8px', fontSize: '11px' }}>
              {gameState.active_promises > 0 && (
                <div style={{ color: theme.text.muted }}>📝 待履行承诺: {gameState.active_promises}</div>
              )}
              {gameState.leverages_against_you > 0 && (
                <div style={{ color: theme.status.error }}>📎 被握把柄: {gameState.leverages_against_you}</div>
              )}
            </div>
          )}
        </div>

        {/* 顾问关系 */}
        <div style={{ padding: '16px', flex: 1 }}>
          <h4 style={{ color: theme.text.secondary, fontSize: '12px', margin: '0 0 12px 0' }}>👥 顾问关系</h4>

          {(['lion', 'fox', 'balance'] as const).map((advisor) => {
            const config = SPEAKER_CONFIG_LIGHT[advisor];
            const relationData = gameState.relations[advisor as keyof typeof gameState.relations];
            const trustValue = relationData?.trust ?? 50;

            return (
              <div
                key={advisor}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '8px',
                  marginBottom: '6px',
                  backgroundColor: theme.bg.secondary,
                  borderRadius: '6px',
                  border: privateTarget === advisor ? `1px solid ${config.color}` : `1px solid ${theme.border.light}`,
                }}
              >
                <span style={{ fontSize: '18px', marginRight: '8px' }}>{config.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ color: config.color, fontSize: '12px', fontWeight: 'bold' }}>{config.name}</div>
                  <div style={{
                    marginTop: '3px',
                    height: '3px',
                    backgroundColor: theme.border.light,
                    borderRadius: '2px',
                    overflow: 'hidden',
                  }}>
                    <div style={{
                      width: `${Math.max(0, Math.min(100, trustValue))}%`,
                      height: '100%',
                      backgroundColor: trustValue > 50 ? theme.status.success : trustValue > 20 ? theme.status.warning : theme.status.error,
                      transition: 'width 0.3s ease',
                    }} />
                  </div>
                </div>
                <span style={{
                  color: trustValue > 50 ? theme.status.success : trustValue > 20 ? theme.status.warning : theme.status.error,
                  fontSize: '12px',
                  fontWeight: 'bold',
                  marginLeft: '8px',
                  minWidth: '24px',
                  textAlign: 'right',
                }}>
                  {trustValue}
                </span>
              </div>
            );
          })}
        </div>

        {/* 警告 */}
        {gameState.warnings && gameState.warnings.length > 0 && (
          <div style={{
            padding: '12px 16px',
            backgroundColor: theme.status.errorBg,
            borderTop: `1px solid ${theme.status.error}50`,
          }}>
            <h4 style={{ color: theme.status.error, fontSize: '11px', margin: '0 0 6px 0' }}>⚠️ 警告</h4>
            {gameState.warnings.map((warning, index) => (
              <div key={index} style={{ color: theme.status.error, fontSize: '11px', marginBottom: '3px' }}>
                • {warning}
              </div>
            ))}
          </div>
        )}

        {/* 游戏结束 */}
        {gameState.game_over && (
          <div style={{
            padding: '16px',
            backgroundColor: theme.status.errorBg,
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '28px', marginBottom: '6px' }}>💀</div>
            <div style={{ color: theme.status.error, fontSize: '14px', fontWeight: 'bold' }}>统治终结</div>
            <div style={{ color: theme.status.error, fontSize: '12px', marginTop: '6px' }}>
              {gameState.game_over_reason}
            </div>
          </div>
        )}
      </div>

      {/* 右侧：主对话区域 */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* 加载下一关的全屏遮罩 */}
        {loadingNextChapter && (
          <div style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
          }}>
            <div style={{ fontSize: '48px', marginBottom: '20px' }}>🏰</div>
            <div style={{
              color: theme.accent.goldDark,
              fontSize: '20px',
              fontWeight: 'bold',
              marginBottom: '12px',
            }}>
              正在进入下一关...
            </div>
            <div style={{
              color: theme.text.muted,
              fontSize: '14px',
            }}>
              顾问们正在准备新的议题
            </div>
            <div style={{
              marginTop: '24px',
              width: '200px',
              height: '4px',
              backgroundColor: theme.border.light,
              borderRadius: '2px',
              overflow: 'hidden',
            }}>
              <div style={{
                width: '30%',
                height: '100%',
                backgroundColor: theme.accent.gold,
                borderRadius: '2px',
                animation: 'loading 1.5s ease-in-out infinite',
              }} />
            </div>
            <style>{`
              @keyframes loading {
                0% { width: 0%; margin-left: 0%; }
                50% { width: 50%; margin-left: 25%; }
                100% { width: 0%; margin-left: 100%; }
              }
            `}</style>
          </div>
        )}
        {gameMode === 'council' && renderCouncilMode()}
        {gameMode === 'private_audience' && renderPrivateAudienceMode()}
        {gameMode === 'decree_result' && renderDecreeResult()}
      </div>

      {/* 发布政令弹窗 */}
      {showDecreeModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            width: '500px',
            backgroundColor: theme.bg.card,
            borderRadius: '16px',
            border: `2px solid ${theme.accent.gold}`,
            padding: '32px',
            boxShadow: theme.shadow.lg,
            position: 'relative',
            overflow: 'hidden',
          }}>
            {/* 政令发布中的加载遮罩 */}
            {decreeLoading && (
              <div style={{
                position: 'absolute',
                inset: 0,
                backgroundColor: 'rgba(255, 253, 245, 0.98)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 10,
                borderRadius: '14px',
              }}>
                {/* 场景图标 - 带动画 */}
                <div style={{
                  fontSize: '56px',
                  marginBottom: '20px',
                  animation: 'pulse 1.5s ease-in-out infinite',
                }}>
                  {DECREE_SCENE_MESSAGES[decreeSceneIndex].icon}
                </div>

                {/* 主文字 */}
                <div
                  key={`decree-text-${decreeSceneIndex}`}
                  style={{
                    color: theme.accent.goldDark,
                    fontSize: '20px',
                    fontWeight: 'bold',
                    marginBottom: '8px',
                    textAlign: 'center',
                    animation: 'fadeIn 0.5s ease-out',
                  }}
                >
                  {DECREE_SCENE_MESSAGES[decreeSceneIndex].text}
                </div>

                {/* 副文字 */}
                <div style={{
                  color: theme.text.muted,
                  fontSize: '14px',
                  marginBottom: '24px',
                  textAlign: 'center',
                  animation: 'fadeIn 0.5s ease-out 0.1s',
                }}>
                  {DECREE_SCENE_MESSAGES[decreeSceneIndex].sub}
                </div>

                {/* 进度指示器 */}
                <div style={{
                  display: 'flex',
                  gap: '8px',
                  marginBottom: '20px',
                }}>
                  {DECREE_SCENE_MESSAGES.map((_, idx) => (
                    <div
                      key={idx}
                      style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        backgroundColor: idx === decreeSceneIndex ? theme.accent.gold : theme.border.light,
                        transition: 'all 0.3s ease',
                        transform: idx === decreeSceneIndex ? 'scale(1.2)' : 'scale(1)',
                      }}
                    />
                  ))}
                </div>

                {/* 加载条 */}
                <div style={{
                  width: '200px',
                  height: '4px',
                  backgroundColor: theme.border.light,
                  borderRadius: '2px',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    width: '100%',
                    height: '100%',
                    backgroundColor: theme.accent.gold,
                    borderRadius: '2px',
                    animation: 'loadingBar 2s ease-in-out infinite',
                  }} />
                </div>

                <style>{`
                  @keyframes pulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.1); }
                  }
                  @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                  }
                  @keyframes loadingBar {
                    0% { transform: translateX(-100%); }
                    50% { transform: translateX(0); }
                    100% { transform: translateX(100%); }
                  }
                `}</style>
              </div>
            )}

            <h2 style={{
              color: theme.accent.goldDark,
              fontSize: '24px',
              margin: '0 0 8px 0',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}>
              📜 发布政令
            </h2>
            <p style={{ color: theme.text.muted, fontSize: '14px', margin: '0 0 24px 0' }}>
              政令一经发布，本回合即结束。请谨慎决策。
            </p>

            <textarea
              value={decreeInput}
              onChange={(e) => setDecreeInput(e.target.value)}
              placeholder="输入你的政令..."
              autoFocus
              disabled={decreeLoading}
              style={{
                width: '100%',
                height: '150px',
                padding: '16px',
                backgroundColor: theme.bg.secondary,
                border: `1px solid ${theme.border.medium}`,
                borderRadius: '8px',
                color: theme.text.primary,
                fontSize: '14px',
                resize: 'none',
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />

            <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
              <button
                onClick={() => setShowDecreeModal(false)}
                disabled={decreeLoading}
                style={{
                  flex: 1,
                  padding: '14px',
                  backgroundColor: theme.bg.secondary,
                  color: theme.text.primary,
                  border: `1px solid ${theme.border.medium}`,
                  borderRadius: '8px',
                  fontSize: '14px',
                  cursor: decreeLoading ? 'not-allowed' : 'pointer',
                  opacity: decreeLoading ? 0.5 : 1,
                }}
              >
                取消
              </button>
              <button
                onClick={handleDecree}
                disabled={!decreeInput.trim() || isLoading || decreeLoading}
                style={{
                  flex: 1,
                  padding: '14px',
                  background: !decreeInput.trim() || isLoading || decreeLoading
                    ? theme.border.medium
                    : `linear-gradient(135deg, ${theme.accent.gold} 0%, ${theme.accent.goldLight} 100%)`,
                  color: !decreeInput.trim() || isLoading || decreeLoading ? theme.text.muted : '#FFFFFF',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  cursor: !decreeInput.trim() || isLoading || decreeLoading ? 'not-allowed' : 'pointer',
                }}
              >
                {isLoading || decreeLoading ? '发布中...' : '确认发布'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 提前结束关卡确认弹窗 */}
      {showEndChapterConfirm && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            width: '450px',
            backgroundColor: theme.bg.card,
            borderRadius: '16px',
            border: `2px solid ${theme.status.warning}`,
            padding: '32px',
            boxShadow: theme.shadow.lg,
          }}>
            <h2 style={{
              color: theme.status.warning,
              fontSize: '20px',
              margin: '0 0 8px 0',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
            }}>
              ⏭️ 提前结束关卡
            </h2>
            <p style={{ color: theme.text.secondary, fontSize: '14px', margin: '0 0 20px 0', lineHeight: '1.6' }}>
              确定要提前结束当前关卡吗？
            </p>

            {/* 警告信息 */}
            <div style={{
              backgroundColor: '#FFF7ED',
              borderRadius: '8px',
              padding: '16px',
              marginBottom: '20px',
              border: '1px solid #FDBA7440',
            }}>
              <div style={{ fontSize: '13px', color: '#C2410C', lineHeight: '1.6' }}>
                <div style={{ marginBottom: '8px', fontWeight: 'bold' }}>⚠️ 注意事项：</div>
                <ul style={{ margin: 0, paddingLeft: '20px' }}>
                  <li>未处理的政令影响将会累积到后续关卡</li>
                  <li>累积的影响可能会以更严重的形式爆发</li>
                  <li>提前结束可能会影响最终评分</li>
                </ul>
              </div>
            </div>

            {/* 当前未处理的影响 */}
            {(activeConsequences.length > 0 || (lastResult?.decree_consequences?.length ?? 0) > 0) && (
              <div style={{
                backgroundColor: theme.bg.secondary,
                borderRadius: '8px',
                padding: '12px',
                marginBottom: '20px',
                border: `1px solid ${theme.border.light}`,
              }}>
                <div style={{ fontSize: '12px', color: theme.text.muted, marginBottom: '8px' }}>
                  当前未处理的影响：{activeConsequences.length + (lastResult?.decree_consequences?.length ?? 0)} 项
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {[...activeConsequences, ...(lastResult?.decree_consequences || [])].slice(0, 5).map((c, idx) => (
                    <span key={idx} style={{
                      fontSize: '11px',
                      padding: '3px 8px',
                      backgroundColor: getSeverityInfo(c.severity).bgColor,
                      color: getSeverityInfo(c.severity).color,
                      borderRadius: '4px',
                    }}>
                      {c.title}
                    </span>
                  ))}
                  {[...activeConsequences, ...(lastResult?.decree_consequences || [])].length > 5 && (
                    <span style={{
                      fontSize: '11px',
                      padding: '3px 8px',
                      backgroundColor: theme.bg.secondary,
                      color: theme.text.muted,
                      borderRadius: '4px',
                    }}>
                      +{[...activeConsequences, ...(lastResult?.decree_consequences || [])].length - 5} 项
                    </span>
                  )}
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setShowEndChapterConfirm(false)}
                disabled={endingChapter}
                style={{
                  flex: 1,
                  padding: '14px',
                  backgroundColor: theme.bg.secondary,
                  color: theme.text.primary,
                  border: `1px solid ${theme.border.medium}`,
                  borderRadius: '8px',
                  fontSize: '14px',
                  cursor: endingChapter ? 'not-allowed' : 'pointer',
                }}
              >
                取消
              </button>
              <button
                onClick={handleEndChapterEarly}
                disabled={endingChapter}
                style={{
                  flex: 1,
                  padding: '14px',
                  background: endingChapter
                    ? theme.border.medium
                    : `linear-gradient(135deg, ${theme.status.warning} 0%, #F59E0B 100%)`,
                  color: endingChapter ? theme.text.muted : '#FFFFFF',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  cursor: endingChapter ? 'not-allowed' : 'pointer',
                }}
              >
                {endingChapter ? '结束中...' : '确认结束'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
