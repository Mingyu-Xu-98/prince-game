// 游戏状态管理 Hook

import { useState, useCallback } from 'react';
import type { GameState, TurnResult, GameEvent, DialogueEntry } from '../types/game';
import { gameApi } from '../api/gameApi';

interface UseGameStateReturn {
  // 状态
  sessionId: string | null;
  gameState: GameState | null;
  dialogueHistory: DialogueEntry[];
  currentEvent: GameEvent | null;
  isLoading: boolean;
  error: string | null;
  intro: string;
  lastTurnResult: TurnResult | null;

  // API Key 配置
  apiKey: string;
  setApiKey: (key: string) => void;
  model: string;
  setModel: (model: string) => void;

  // 操作
  startNewGame: () => Promise<void>;
  submitTurn: (input: string) => Promise<TurnResult | null>;
  handleEventChoice: (choiceId: string) => Promise<void>;
  clearError: () => void;
}

export function useGameState(): UseGameStateReturn {
  // 配置
  const [apiKey, setApiKey] = useState<string>(() => localStorage.getItem('openrouter_api_key') || '');
  const [model, setModel] = useState<string>(() => localStorage.getItem('openrouter_model') || '');

  // 游戏状态
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [dialogueHistory, setDialogueHistory] = useState<DialogueEntry[]>([]);
  const [currentEvent, setCurrentEvent] = useState<GameEvent | null>(null);
  const [intro, setIntro] = useState<string>('');
  const [lastTurnResult, setLastTurnResult] = useState<TurnResult | null>(null);

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
      const response = await gameApi.newGame(apiKey, model || undefined);
      setSessionId(response.session_id);
      setGameState(response.state);
      setIntro(response.intro);
      setDialogueHistory([]);
      setCurrentEvent(null);
      setLastTurnResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '创建游戏失败');
    } finally {
      setIsLoading(false);
    }
  }, [apiKey, model]);

  // 提交回合
  const submitTurn = useCallback(async (input: string): Promise<TurnResult | null> => {
    if (!sessionId || !apiKey) {
      setError('游戏未开始或 API Key 未设置');
      return null;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await gameApi.processTurn(sessionId, input, apiKey, model || undefined);

      // 更新对话历史
      setDialogueHistory(prev => [
        ...prev,
        { turn: result.turn, speaker: 'player', content: input },
        { turn: result.turn, speaker: 'lion', content: result.robot_responses.lion },
        { turn: result.turn, speaker: 'fox', content: result.robot_responses.fox },
        { turn: result.turn, speaker: 'balance', content: result.robot_responses.balance },
      ]);

      // 更新游戏状态
      setGameState(result.state);
      setLastTurnResult(result);

      // 检查是否有事件
      if (result.event) {
        setCurrentEvent(result.event);
      }

      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : '处理回合失败');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, apiKey, model]);

  // 处理事件选择
  const handleEventChoice = useCallback(async (choiceId: string) => {
    if (!sessionId || !apiKey || !currentEvent) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await gameApi.handleEvent(
        sessionId,
        currentEvent.id,
        choiceId,
        apiKey,
        model || undefined
      );

      setGameState(result.state);
      setCurrentEvent(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '处理事件失败');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, apiKey, model, currentEvent]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    sessionId,
    gameState,
    dialogueHistory,
    currentEvent,
    isLoading,
    error,
    intro,
    lastTurnResult,
    apiKey,
    setApiKey: handleSetApiKey,
    model,
    setModel: handleSetModel,
    startNewGame,
    submitTurn,
    handleEventChoice,
    clearError,
  };
}
