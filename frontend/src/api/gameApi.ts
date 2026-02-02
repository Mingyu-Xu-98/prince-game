// 游戏 API 客户端 - 支持关卡系统

import type { GameState, ChapterScene, DecisionResult, ChapterInfo, FinalAudit, CouncilDebate } from '../types/game';

const API_BASE = '/api';

interface NewGameResponse {
  session_id: string;
  intro: string;
  state: GameState;
  available_chapters: ChapterInfo[];
}

// API 返回的原始关卡响应
interface StartChapterApiResponse {
  chapter: {
    id: string;
    name: string;
    subtitle: string;
    complexity: number;
    max_turns: number;
  };
  background: string;
  scene_snapshot: string;
  dilemma: string;
  opening_narration: string;
  council_debate: CouncilDebate;
  state: GameState;
}

// 转换后的响应
interface StartChapterResponse {
  chapter: ChapterScene;
  state: GameState;
}

export const gameApi = {
  /**
   * 创建新游戏
   */
  async newGame(apiKey: string, model?: string, skipIntro: boolean = false): Promise<NewGameResponse> {
    const response = await fetch(`${API_BASE}/game/new`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: apiKey,
        model,
        skip_intro: skipIntro
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '创建游戏失败');
    }

    return response.json();
  },

  /**
   * 开始指定关卡
   */
  async startChapter(
    sessionId: string,
    chapterId: string,
    apiKey: string,
    model?: string
  ): Promise<StartChapterResponse> {
    const response = await fetch(`${API_BASE}/game/chapter/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        chapter_id: chapterId,
        api_key: apiKey,
        model,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '开始关卡失败');
    }

    const data: StartChapterApiResponse = await response.json();

    // 转换为前端使用的格式
    const chapter: ChapterScene = {
      id: data.chapter.id,
      name: data.chapter.name,
      subtitle: data.chapter.subtitle,
      complexity: data.chapter.complexity,
      max_turns: data.chapter.max_turns,
      current_turn: data.state.chapter_turn,
      background: data.background,
      scene_snapshot: data.scene_snapshot,
      dilemma: data.dilemma,
      opening_narration: data.opening_narration,
      council_debate: data.council_debate,
      hide_values: false, // 从 state 获取或默认
    };

    return {
      chapter,
      state: data.state,
    };
  },

  /**
   * 提交玩家决策
   */
  async submitDecision(
    sessionId: string,
    decision: string,
    apiKey: string,
    model?: string,
    followedAdvisor?: string
  ): Promise<DecisionResult> {
    const response = await fetch(`${API_BASE}/game/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        decision,
        followed_advisor: followedAdvisor,
        api_key: apiKey,
        model,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '处理决策失败');
    }

    return response.json();
  },

  /**
   * 获取游戏状态
   */
  async getGameState(sessionId: string): Promise<{
    state: GameState;
    current_chapter: {
      id: string;
      name: string;
      turn: number;
      max_turns: number;
    };
    history: any[];
    stats: any;
    leverages_count: number;
    active_promises: number;
  }> {
    const response = await fetch(`${API_BASE}/game/${sessionId}`);

    if (!response.ok) {
      throw new Error('获取游戏状态失败');
    }

    return response.json();
  },

  /**
   * 获取审计报告
   */
  async getAudit(sessionId: string): Promise<{
    audit: FinalAudit;
    all_decisions: any[];
    leverages: any[];
  }> {
    const response = await fetch(`${API_BASE}/game/${sessionId}/audit`);

    if (!response.ok) {
      throw new Error('获取审计报告失败');
    }

    return response.json();
  },

  /**
   * 删除游戏会话
   */
  async deleteGame(sessionId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/game/${sessionId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('删除游戏失败');
    }
  },
};
