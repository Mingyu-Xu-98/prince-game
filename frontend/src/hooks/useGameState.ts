// 游戏状态管理 Hook - 支持关卡系统和新裁决系统

import { useState, useCallback } from 'react';
import type { GameState, ChapterScene, DecisionResult, DialogueEntry, ChapterInfo, FinalAudit, ObservationLensChoice, JudgmentMetadata } from '../types/game';
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

  // 操作
  startNewGame: () => Promise<void>;
  selectObservationLens: (lens: string) => Promise<void>;
  startChapter: (chapterId: string) => Promise<void>;
  submitDecision: (input: string, followedAdvisor?: string) => Promise<DecisionResult | null>;
  clearError: () => void;
}

export function useGameState(): UseGameStateReturn {
  // 配置
  const [apiKey, setApiKey] = useState<string>(() => localStorage.getItem('openrouter_api_key') || '');
  const [model, setModel] = useState<string>(() => localStorage.getItem('openrouter_model') || '');

  // 游戏状态
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [currentChapter, setCurrentChapter] = useState<ChapterScene | null>(null);
  const [dialogueHistory, setDialogueHistory] = useState<DialogueEntry[]>([]);
  const [availableChapters, setAvailableChapters] = useState<ChapterInfo[]>([]);
  const [intro, setIntro] = useState<string>('');
  const [lastDecisionResult, setLastDecisionResult] = useState<DecisionResult | null>(null);
  const [finalAudit, setFinalAudit] = useState<FinalAudit | null>(null);

  // 新裁决系统状态
  const [gamePhase, setGamePhase] = useState<GamePhase>('setup');
  const [initializationScene, setInitializationScene] = useState<string>('');
  const [lensChoices, setLensChoices] = useState<Record<string, ObservationLensChoice>>({});
  const [selectedLens, setSelectedLens] = useState<string | null>(null);
  const [mountainView, setMountainView] = useState<string>('');
  const [lastJudgment, setLastJudgment] = useState<JudgmentMetadata | null>(null);

  // UI 状态
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

      // 添加顾问回应
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

      // 如果有警告
      if (result.warnings && result.warnings.length > 0) {
        newEntries.push({
          turn: result.turn,
          speaker: 'system',
          content: `⚠️ ${result.warnings.join('\n')}`
        });
      }

      // 新裁决系统：裁决元数据
      if (result.judgment_metadata) {
        setLastJudgment(result.judgment_metadata);
        newEntries.push({
          turn: result.turn,
          speaker: 'system',
          content: `📊 【裁决】\n策略: ${result.judgment_metadata.player_strategy}\n特质: ${result.judgment_metadata.machiavelli_traits.join(', ')}\n结局等级: ${result.judgment_metadata.outcome_level}\n\n📜 马基雅维利曰: "${result.judgment_metadata.machiavelli_critique}"`
        });
      }

      // 因果种子警告
      if (result.causal_seed) {
        newEntries.push({
          turn: result.turn,
          speaker: 'system',
          content: `🌱 【因果种子】\n${result.causal_seed.description}\n\n${result.causal_seed.warning}`
        });
      }

      // 因果回响触发
      if (result.echo_triggered) {
        newEntries.push({
          turn: result.turn,
          speaker: 'system',
          content: `⚡ 【因果回响】\n${result.echo_triggered.echo_message}\n\n来源: 第${result.echo_triggered.source_chapter}关 第${result.echo_triggered.source_turn}回合\n\n💀 ${result.echo_triggered.crisis}`
        });
      }

      // 顾问状态变化
      if (result.advisor_changes) {
        Object.entries(result.advisor_changes).forEach(([advisor, change]) => {
          newEntries.push({
            turn: result.turn,
            speaker: 'system',
            content: `🔄 【顾问异化】\n${advisor} ${change.status}\n⚠️ ${change.warning}`
          });
        });
      }

      // 如果泄露了秘密
      if (result.secret_leaked) {
        newEntries.push({
          turn: result.turn,
          speaker: 'system',
          content: '🔓 你的秘密行动被发现了！'
        });
      }

      // 如果被抓把柄
      if (result.leverage_gained) {
        newEntries.push({
          turn: result.turn,
          speaker: 'system',
          content: `📎 ${result.leverage_gained.holder} 抓住了你的把柄: ${result.leverage_gained.description}`
        });
      }

      setDialogueHistory(prev => [...prev, ...newEntries]);

      // 更新游戏状态
      setGameState(result.new_state);
      setLastDecisionResult(result);

      // 如果关卡结束
      if (result.chapter_result?.chapter_ended) {
        const endMessage = result.chapter_result.victory
          ? `🎉 【关卡通过】${result.chapter_result.reason || '恭喜你完成了这个关卡！'}`
          : `💀 【关卡失败】${result.chapter_result.reason || '你在这个关卡失败了。'}`;

        setDialogueHistory(prev => [...prev, {
          turn: result.turn,
          speaker: 'system',
          content: endMessage
        }]);

        // 如果有下一关
        if (result.next_chapter_available) {
          setAvailableChapters(prev => [
            ...prev.map(c => c.id === currentChapter?.id ? { ...c, status: 'completed' as const } : c),
            {
              id: result.next_chapter_available!.id,
              name: result.next_chapter_available!.name,
              subtitle: '',
              complexity: 0,
              status: 'available' as const
            }
          ]);
          setCurrentChapter(null);
        }

        // 如果有最终审计（游戏通关）
        if (result.final_audit) {
          setFinalAudit(result.final_audit);
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
    // 操作
    startNewGame,
    selectObservationLens,
    startChapter,
    submitDecision,
    clearError,
  };
}
