// 游戏状态管理 Hook - 支持关卡系统和新裁决系统

import { useState, useCallback, useEffect } from 'react';
import type { GameState, ChapterScene, DecisionResult, DialogueEntry, ChapterInfo, FinalAudit, ObservationLensChoice, JudgmentMetadata, DecreeConsequence, PendingConsequence } from '../types/game';
import { gameApi } from '../api/gameApi';

// 游戏阶段
type GamePhase = 'setup' | 'lens_selection' | 'chapter_select' | 'playing' | 'ended';

interface UseGameStateReturn {
  // 状态
  sessionId: string | null;
  gameState: GameState | null;
  currentChapter: ChapterScene | null;
  dialogueHistory: DialogueEntry[];
  availableChapters: ChapterInfo[];
  isLoading: boolean;
  error: string | null;
  intro: string;
  lastDecisionResult: DecisionResult | null;
  finalAudit: FinalAudit | null;

  // 新裁决系统状态
  gamePhase: GamePhase;
  initializationScene: string;
  lensChoices: Record<string, ObservationLensChoice>;
  selectedLens: string | null;
  mountainView: string;
  lastJudgment: JudgmentMetadata | null;

  // API Key 配置
  apiKey: string;
  setApiKey: (key: string) => void;
  model: string;
  setModel: (model: string) => void;

  // 累积的未处理影响
  pendingConsequences: PendingConsequence[];

  // 操作
  startNewGame: () => Promise<void>;
  selectObservationLens: (lens: string) => Promise<void>;
  startChapter: (chapterId: string) => Promise<void>;
  submitDecision: (input: string, followedAdvisor?: string) => Promise<DecisionResult | null>;
  privateAudience: (advisor: string, message: string) => Promise<string | null>;
  clearError: () => void;
  backToChapterSelect: () => void;
  exitToSetup: () => void;
  skipConsequences: (consequences: DecreeConsequence[]) => void;
  continueWithConsequences: (consequences: DecreeConsequence[]) => void;
  goToNextChapter: () => void;
}

// 本地存储键名
const STORAGE_KEYS = {
  SESSION_ID: 'game_session_id',
  GAME_STATE: 'game_state',
  CURRENT_CHAPTER: 'game_current_chapter',
  DIALOGUE_HISTORY: 'game_dialogue_history',
  AVAILABLE_CHAPTERS: 'game_available_chapters',
  GAME_PHASE: 'game_phase',
  SELECTED_LENS: 'game_selected_lens',
  PENDING_CONSEQUENCES: 'game_pending_consequences',
  INTRO: 'game_intro',
  MOUNTAIN_VIEW: 'game_mountain_view',
};

// 从 localStorage 安全获取 JSON 数据
function getStoredJson<T>(key: string, defaultValue: T): T {
  try {
    const stored = localStorage.getItem(key);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (e) {
    console.warn(`Failed to parse stored ${key}:`, e);
  }
  return defaultValue;
}

export function useGameState(): UseGameStateReturn {
  // 配置 - 默认 API Key
  const DEFAULT_API_KEY = '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';
  const [apiKey, setApiKey] = useState<string>(() => localStorage.getItem('openrouter_api_key') || DEFAULT_API_KEY);
  const [model, setModel] = useState<string>(() => localStorage.getItem('openrouter_model') || '');

  // 游戏状态 - 从 localStorage 恢复
  const [sessionId, setSessionId] = useState<string | null>(() => localStorage.getItem(STORAGE_KEYS.SESSION_ID));
  const [gameState, setGameState] = useState<GameState | null>(() => getStoredJson(STORAGE_KEYS.GAME_STATE, null));
  const [currentChapter, setCurrentChapter] = useState<ChapterScene | null>(() => getStoredJson(STORAGE_KEYS.CURRENT_CHAPTER, null));
  const [dialogueHistory, setDialogueHistory] = useState<DialogueEntry[]>(() => getStoredJson(STORAGE_KEYS.DIALOGUE_HISTORY, []));
  const [availableChapters, setAvailableChapters] = useState<ChapterInfo[]>(() => getStoredJson(STORAGE_KEYS.AVAILABLE_CHAPTERS, []));
  const [intro, setIntro] = useState<string>(() => localStorage.getItem(STORAGE_KEYS.INTRO) || '');
  const [lastDecisionResult, setLastDecisionResult] = useState<DecisionResult | null>(null);
  const [finalAudit, setFinalAudit] = useState<FinalAudit | null>(null);

  // 新裁决系统状态 - 从 localStorage 恢复
  const [gamePhase, setGamePhase] = useState<GamePhase>(() => {
    const stored = localStorage.getItem(STORAGE_KEYS.GAME_PHASE);
    return (stored as GamePhase) || 'setup';
  });
  const [initializationScene, setInitializationScene] = useState<string>('');
  const [lensChoices, setLensChoices] = useState<Record<string, ObservationLensChoice>>({});
  const [selectedLens, setSelectedLens] = useState<string | null>(() => localStorage.getItem(STORAGE_KEYS.SELECTED_LENS));
  const [mountainView, setMountainView] = useState<string>(() => localStorage.getItem(STORAGE_KEYS.MOUNTAIN_VIEW) || '');
  const [lastJudgment, setLastJudgment] = useState<JudgmentMetadata | null>(null);

  // 累积的未处理影响 - 从 localStorage 恢复
  const [pendingConsequences, setPendingConsequences] = useState<PendingConsequence[]>(() => getStoredJson(STORAGE_KEYS.PENDING_CONSEQUENCES, []));

  // UI 状态
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 自动保存游戏状态到 localStorage
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem(STORAGE_KEYS.SESSION_ID, sessionId);
    } else {
      localStorage.removeItem(STORAGE_KEYS.SESSION_ID);
    }
  }, [sessionId]);

  useEffect(() => {
    if (gameState) {
      localStorage.setItem(STORAGE_KEYS.GAME_STATE, JSON.stringify(gameState));
    } else {
      localStorage.removeItem(STORAGE_KEYS.GAME_STATE);
    }
  }, [gameState]);

  useEffect(() => {
    if (currentChapter) {
      localStorage.setItem(STORAGE_KEYS.CURRENT_CHAPTER, JSON.stringify(currentChapter));
    } else {
      localStorage.removeItem(STORAGE_KEYS.CURRENT_CHAPTER);
    }
  }, [currentChapter]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.DIALOGUE_HISTORY, JSON.stringify(dialogueHistory));
  }, [dialogueHistory]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.AVAILABLE_CHAPTERS, JSON.stringify(availableChapters));
  }, [availableChapters]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.GAME_PHASE, gamePhase);
  }, [gamePhase]);

  useEffect(() => {
    if (selectedLens) {
      localStorage.setItem(STORAGE_KEYS.SELECTED_LENS, selectedLens);
    } else {
      localStorage.removeItem(STORAGE_KEYS.SELECTED_LENS);
    }
  }, [selectedLens]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.PENDING_CONSEQUENCES, JSON.stringify(pendingConsequences));
  }, [pendingConsequences]);

  useEffect(() => {
    if (intro) {
      localStorage.setItem(STORAGE_KEYS.INTRO, intro);
    }
  }, [intro]);

  useEffect(() => {
    if (mountainView) {
      localStorage.setItem(STORAGE_KEYS.MOUNTAIN_VIEW, mountainView);
    }
  }, [mountainView]);

  // 保存配置到 localStorage
  const handleSetApiKey = useCallback((key: string) => {
    setApiKey(key);
    localStorage.setItem('openrouter_api_key', key);
  }, []);

  const handleSetModel = useCallback((m: string) => {
    setModel(m);
    localStorage.setItem('openrouter_model', m);
  }, []);

  // 开始新游戏
  const startNewGame = useCallback(async () => {
    if (!apiKey) {
      setError('请先设置 OpenRouter API Key');
      return;
    }

    setIsLoading(true);
    setError(null);

    // 清除旧的游戏数据
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
    setPendingConsequences([]);

    try {
      const response = await gameApi.newGame(apiKey, model || undefined, false);
      setSessionId(response.session_id);
      setGameState(response.state);
      setIntro(response.intro);
      setAvailableChapters(response.available_chapters);
      setDialogueHistory([]);
      setCurrentChapter(null);
      setLastDecisionResult(null);
      setFinalAudit(null);

      // 新裁决系统初始化
      setInitializationScene(response.initialization_scene || '');
      setLensChoices(response.lens_choices || {});
      setSelectedLens(null);
      setLastJudgment(null);

      // 判断是否需要选择观测透镜
      if (response.requires_lens_selection) {
        setGamePhase('lens_selection');
      } else {
        setGamePhase('chapter_select');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建游戏失败');
    } finally {
      setIsLoading(false);
    }
  }, [apiKey, model]);

  // 选择观测透镜
  const selectObservationLens = useCallback(async (lens: string) => {
    if (!sessionId || !apiKey) {
      setError('游戏未开始');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await gameApi.setObservationLens(sessionId, lens);
      setSelectedLens(lens);
      setMountainView(response.mountain_view);

      // 添加选择记录到对话历史
      setDialogueHistory(prev => [
        ...prev,
        {
          turn: 0,
          speaker: 'system',
          content: `🔮 ${response.message}\n\n效果: ${response.selected_lens.effect}`
        }
      ]);

      // 进入关卡选择阶段
      setGamePhase('chapter_select');
    } catch (err) {
      setError(err instanceof Error ? err.message : '设置观测透镜失败');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, apiKey]);

  // 开始关卡
  const startChapter = useCallback(async (chapterId: string) => {
    if (!sessionId || !apiKey) {
      setError('游戏未开始或 API Key 未设置');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await gameApi.startChapter(sessionId, chapterId, apiKey, model || undefined);
      setCurrentChapter(response.chapter);
      setGameState(response.state);
      setGamePhase('playing');

      // 添加开场叙事到对话历史
      setDialogueHistory(prev => [
        ...prev,
        {
          turn: 0,
          speaker: 'system',
          content: `📜 【${response.chapter.name}】开始\n\n${response.chapter.opening_narration || response.chapter.scene_snapshot}`
        }
      ]);

      // 格式化议会辩论
      if (response.chapter.council_debate) {
        const debate = response.chapter.council_debate;
        let debateText = '';

        if (debate.lion) {
          debateText += `🦁 狮子: "${debate.lion.suggestion}"\n   (${debate.lion.reasoning})\n\n`;
        }
        if (debate.fox) {
          debateText += `🦊 狐狸: "${debate.fox.suggestion}"\n   (${debate.fox.reasoning})\n\n`;
        }
        if (debate.balance) {
          debateText += `⚖️ 天平: "${debate.balance.suggestion}"\n   (${debate.balance.reasoning})`;
        }

        if (debateText) {
          setDialogueHistory(prev => [
            ...prev,
            {
              turn: 0,
              speaker: 'system',
              content: `⚔️ 【顾问辩论】\n\n${debateText}`
            }
          ]);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '开始关卡失败');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, apiKey, model]);

  // 提交决策
  const submitDecision = useCallback(async (input: string, followedAdvisor?: string): Promise<DecisionResult | null> => {
    if (!sessionId || !apiKey) {
      setError('游戏未开始或 API Key 未设置');
      return null;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await gameApi.submitDecision(sessionId, input, apiKey, model || undefined, followedAdvisor);

      // 更新对话历史
      const newEntries: DialogueEntry[] = [
        {
          turn: result.turn,
          speaker: 'player',
          content: input,
          is_promise: result.decision_analysis?.contains_promise,
          is_lie: result.decision_analysis?.is_secret_action
        },
      ];

      // 添加顾问回应（仅显示顾问的对话，不显示分析）
      if (result.advisor_responses) {
        if (result.advisor_responses.lion) {
          newEntries.push({ turn: result.turn, speaker: 'lion', content: result.advisor_responses.lion });
        }
        if (result.advisor_responses.fox) {
          newEntries.push({ turn: result.turn, speaker: 'fox', content: result.advisor_responses.fox });
        }
        if (result.advisor_responses.balance) {
          newEntries.push({ turn: result.turn, speaker: 'balance', content: result.advisor_responses.balance });
        }
      }

      // 保存裁决元数据供回合结束时使用，但不实时显示
      if (result.judgment_metadata) {
        setLastJudgment(result.judgment_metadata);
      }

      // 因果回响触发（重要事件，仍需显示）
      if (result.echo_triggered) {
        newEntries.push({
          turn: result.turn,
          speaker: 'system',
          content: `⚡ 命运的回响触动了你过去的抉择...`
        });
      }

      // 如果泄露了秘密（重要事件）
      if (result.secret_leaked) {
        newEntries.push({
          turn: result.turn,
          speaker: 'system',
          content: '🔓 有人发现了你的秘密...'
        });
      }

      // 如果被抓把柄（重要事件）
      if (result.leverage_gained) {
        newEntries.push({
          turn: result.turn,
          speaker: 'system',
          content: `📎 有人抓住了你的把柄...`
        });
      }

      setDialogueHistory(prev => [...prev, ...newEntries]);

      // 更新游戏状态（只有当返回了有效状态时才更新）
      if (result.new_state) {
        setGameState(result.new_state);
      }
      setLastDecisionResult(result);

      // 更新当前关卡的回合数
      if (currentChapter && result.turn !== undefined) {
        setCurrentChapter(prev => prev ? {
          ...prev,
          current_turn: result.turn
        } : null);
      }

      // 如果关卡结束
      if (result.chapter_result?.chapter_ended) {
        const endMessage = result.chapter_result.victory
          ? `🎉 【关卡通过】${result.chapter_result.reason || '恭喜你完成了这个关卡！'}`
          : `💀 【关卡失败】${result.chapter_result.reason || '你在这个关卡失败了。'}`;

        // 构建关卡结束时的君主论分析
        const chapterAnalysisEntries: DialogueEntry[] = [{
          turn: result.turn,
          speaker: 'system',
          content: endMessage
        }];

        // 在关卡结束时添加基于君主论的整体分析
        if (result.judgment_metadata) {
          const analysis = result.judgment_metadata;
          chapterAnalysisEntries.push({
            turn: result.turn,
            speaker: 'system',
            content: `📜 【君主论审视】\n\n` +
              `「${analysis.machiavelli_critique}」\n\n` +
              `▸ 策略风格: ${analysis.player_strategy}\n` +
              `▸ 展现特质: ${analysis.machiavelli_traits.join('、')}\n` +
              `▸ 结局评级: ${analysis.outcome_level}`
          });
        }

        // 如果有因果种子或回响，在关卡结束时一并展示
        if (result.causal_seed) {
          chapterAnalysisEntries.push({
            turn: result.turn,
            speaker: 'system',
            content: `🌱 【因果种子】\n你的决策埋下了伏笔: ${result.causal_seed.description}`
          });
        }

        setDialogueHistory(prev => [...prev, ...chapterAnalysisEntries]);

        // 如果有下一关，先解锁它（但不自动跳转，等用户点击进入下一关按钮）
        if (result.next_chapter_available) {
          setAvailableChapters(prev => {
            // 检查是否已经有这个关卡
            const existingIndex = prev.findIndex(c => c.id === result.next_chapter_available!.id);
            if (existingIndex >= 0) {
              // 已存在，更新当前关卡为完成状态
              return prev.map(c =>
                c.id === currentChapter?.id ? { ...c, status: 'completed' as const } : c
              );
            }
            // 不存在，添加新关卡
            return [
              ...prev.map(c => c.id === currentChapter?.id ? { ...c, status: 'completed' as const } : c),
              {
                id: result.next_chapter_available!.id,
                name: result.next_chapter_available!.name,
                subtitle: '',
                complexity: 0,
                status: 'available' as const
              }
            ];
          });
          // 不再自动跳转，让用户通过 GameBoard 的按钮来进入下一关
        }

        // 如果有最终审计（游戏通关）
        if (result.final_audit) {
          setFinalAudit(result.final_audit);
          setGamePhase('ended');
        }

        // 如果关卡失败但没有下一关
        if (!result.chapter_result.victory && !result.next_chapter_available) {
          // 保持在当前界面显示失败信息，不跳转
        }
      }

      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : '处理决策失败');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, apiKey, model, currentChapter]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // 返回关卡选择界面
  const backToChapterSelect = useCallback(() => {
    setCurrentChapter(null);
    setGamePhase('chapter_select');
    setDialogueHistory([]);
  }, []);

  // 退出到设置页面（清除本地存储）
  const exitToSetup = useCallback(() => {
    // 清除状态
    setSessionId(null);
    setGameState(null);
    setCurrentChapter(null);
    setDialogueHistory([]);
    setAvailableChapters([]);
    setGamePhase('setup');
    setFinalAudit(null);
    setLastDecisionResult(null);
    setSelectedLens(null);
    setPendingConsequences([]);
    setIntro('');
    setMountainView('');

    // 清除本地存储（保留 API Key 和 Model）
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
  }, []);

  // 跳过政令后续影响（累积到后续关卡）
  const skipConsequences = useCallback((consequences: DecreeConsequence[]) => {
    if (!currentChapter || consequences.length === 0) return;

    const newPendingConsequences: PendingConsequence[] = consequences.map(c => ({
      source_chapter: currentChapter.id,
      source_turn: currentChapter.current_turn,
      consequence: c,
      turns_remaining: c.deadline_turns,
    }));

    setPendingConsequences(prev => [...prev, ...newPendingConsequences]);

    console.log('累积的未处理影响:', newPendingConsequences);
  }, [currentChapter]);

  // 继续处理政令后续影响（添加到对话历史，让顾问评论）
  const continueWithConsequences = useCallback((consequences: DecreeConsequence[]) => {
    if (consequences.length === 0) return;

    // 添加系统消息表明正在处理后果
    const consequenceMessages: DialogueEntry[] = [
      {
        turn: currentChapter?.current_turn || 0,
        speaker: 'system',
        content: `🌊 【政令影响处理中】\n\n你的政令产生了 ${consequences.length} 项需要关注的后续影响：\n${consequences.map(c => `• ${c.title}：${c.description.slice(0, 50)}...`).join('\n')}`
      }
    ];

    setDialogueHistory(prev => [...prev, ...consequenceMessages]);
  }, [currentChapter]);

  // 进入下一关
  const goToNextChapter = useCallback(() => {
    setCurrentChapter(null);
    setGamePhase('chapter_select');
    setDialogueHistory([]);
  }, []);

  // 密谈 - 单独召见顾问
  const privateAudience = useCallback(async (advisor: string, message: string): Promise<string | null> => {
    if (!sessionId || !apiKey) {
      setError('游戏未开始或 API Key 未设置');
      return null;
    }

    try {
      const result = await gameApi.privateAudience(
        sessionId,
        advisor,
        message,
        apiKey,
        model || undefined
      );

      // 更新顾问关系（如果有变化）
      if (result.trust_change !== 0 && gameState) {
        setGameState(prev => {
          if (!prev) return prev;
          const updatedRelations = { ...prev.relations };
          const advisorKey = advisor as keyof typeof updatedRelations;
          if (updatedRelations[advisorKey]) {
            updatedRelations[advisorKey] = {
              ...updatedRelations[advisorKey],
              trust: result.new_trust,
            };
          }
          return {
            ...prev,
            relations: updatedRelations,
          };
        });
      }

      return result.response;
    } catch (err) {
      setError(err instanceof Error ? err.message : '密谈失败');
      return null;
    }
  }, [sessionId, apiKey, model, gameState]);

  return {
    sessionId,
    gameState,
    currentChapter,
    dialogueHistory,
    availableChapters,
    isLoading,
    error,
    intro,
    lastDecisionResult,
    finalAudit,
    // 新裁决系统状态
    gamePhase,
    initializationScene,
    lensChoices,
    selectedLens,
    mountainView,
    lastJudgment,
    // API Key 配置
    apiKey,
    setApiKey: handleSetApiKey,
    model,
    setModel: handleSetModel,
    // 累积的未处理影响
    pendingConsequences,

    // 操作
    startNewGame,
    selectObservationLens,
    startChapter,
    submitDecision,
    privateAudience,
    clearError,
    backToChapterSelect,
    exitToSetup,
    skipConsequences,
    continueWithConsequences,
    goToNextChapter,
  };
}
