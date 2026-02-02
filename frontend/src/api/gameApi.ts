// 游戏 API 客户端

import type { GameState, TurnResult, GameEvent } from '../types/game';

const API_BASE = '/api';

interface NewGameResponse {
  session_id: string;
  intro: string;
  state: GameState;
}

interface EventResponse {
  event_id: string;
  result: {
    choice_made: string;
    impact: { authority: number; fear: number; love: number };
    new_power: { authority: { value: number }; fear: { value: number }; love: { value: number }; total: number };
    warnings: string[];
    game_over?: boolean;
    game_over_narration?: string;
  };
  state: GameState;
}

export const gameApi = {
  /**
   * 创建新游戏
   */
  async newGame(apiKey: string, model?: string): Promise<NewGameResponse> {
    const response = await fetch(`${API_BASE}/game/new`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: apiKey, model }),
    });

    if (!response.ok) {
      throw new Error(`创建游戏失败: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * 处理一个回合
   */
  async processTurn(
    sessionId: string,
    input: string,
    apiKey: string,
    model?: string
  ): Promise<TurnResult> {
    const response = await fetch(`${API_BASE}/game/turn`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        input,
        api_key: apiKey,
        model,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '处理回合失败');
    }

    return response.json();
  },

  /**
   * 处理事件选择
   */
  async handleEvent(
    sessionId: string,
    eventId: string,
    choiceId: string,
    apiKey: string,
    model?: string
  ): Promise<EventResponse> {
    const response = await fetch(`${API_BASE}/game/event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        event_id: eventId,
        choice_id: choiceId,
        api_key: apiKey,
        model,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '处理事件失败');
    }

    return response.json();
  },

  /**
   * 获取游戏状态
   */
  async getGameState(sessionId: string): Promise<{ state: GameState; history: any[]; pending_events: string[] }> {
    const response = await fetch(`${API_BASE}/game/${sessionId}`);

    if (!response.ok) {
      throw new Error('获取游戏状态失败');
    }

    return response.json();
  },
};
