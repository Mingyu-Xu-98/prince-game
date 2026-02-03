// 游戏 API 客户端 - 支持关卡系统和新裁决系统

import type { GameState, ChapterScene, DecisionResult, ChapterInfo, FinalAudit, CouncilDebate, InitializationScene, ObservationLensChoice } from '../types/game';

const API_BASE = '/api';

interface NewGameResponse {
  session_id: string;
  intro: string;
  initialization_scene: string;
  lens_choices: Record<string, ObservationLensChoice>;
  state: GameState;
  available_chapters: ChapterInfo[];
  requires_lens_selection: boolean;
}

interface SetLensResponse {
  success: boolean;
  selected_lens: {
    key: string;
    name: string;
    description: string;
    effect: string;
  };
  message: string;
  mountain_view: string;
  next_step: string;
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
   * 获取初始化场景
   */
  async getInitializationScene(): Promise<InitializationScene> {
    const response = await fetch(`${API_BASE}/game/initialization`);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '获取初始化场景失败');
    }

    return response.json();
  },

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
   * 设置观测透镜
   */
  async setObservationLens(sessionId: string, lens: string): Promise<SetLensResponse> {
    const response = await fetch(`${API_BASE}/game/lens`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        lens,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '设置观测透镜失败');
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

  /**
   * 密谈 - 单独召见顾问
   */
  async privateAudience(
    sessionId: string,
    advisor: string,
    message: string,
    apiKey: string,
    model?: string
  ): Promise<{
    advisor: string;
    response: string;
    trust_change: number;
    new_trust: number;
  }> {
    const response = await fetch(`${API_BASE}/game/private-audience`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        advisor,
        message,
        api_key: apiKey,
        model,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '密谈失败');
    }

    return response.json();
  },

  /**
   * 处理政令后续影响 - 继续处理某个后果
   */
  async handleConsequence(
    sessionId: string,
    consequenceId: string,
    playerResponse: string,
    apiKey: string,
    model?: string
  ): Promise<{
    success: boolean;
    scene_update: string;
    advisor_comments: {
      lion?: string;
      fox?: string;
      balance?: string;
    };
    consequence_resolved: boolean;
    new_developments: string[];
    state: GameState;
  }> {
    const response = await fetch(`${API_BASE}/game/consequence`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        consequence_id: consequenceId,
        player_response: playerResponse,
        api_key: apiKey,
        model,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '处理政令后果失败');
    }

    return response.json();
  },

  /**
   * 继续当前回合 - 生成新场景和顾问评论
   */
  async continueRound(
    sessionId: string,
    previousDecision: string,
    consequences: any[],
    apiKey: string,
    model?: string
  ): Promise<{
    success: boolean;
    scene_update: string;
    new_dilemma: string;
    advisor_comments: {
      lion?: { stance: string; comment: string; suggestion?: string };
      fox?: { stance: string; comment: string; suggestion?: string };
      balance?: { stance: string; comment: string; suggestion?: string };
    };
    state: GameState;
  }> {
    const response = await fetch(`${API_BASE}/game/continue-round`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        previous_decision: previousDecision,
        consequences,
        api_key: apiKey,
        model,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '继续回合失败');
    }

    return response.json();
  },

  /**
   * 廷议对话 - 分析玩家意图并生成顾问回应
   */
  async councilChat(
    sessionId: string,
    message: string,
    conversationHistory: any[],
    apiKey: string,
    model?: string
  ): Promise<{
    success: boolean;
    intent: {
      intent: string;
      target: string;
      tone: string;
      summary: string;
      triggers_conflict: boolean;
    };
    responses: {
      lion?: string;
      fox?: string;
      balance?: string;
    };
    conflict_triggered: boolean;
    conflict_description: string;
    trust_changes: { lion: number; fox: number; balance: number };
    atmosphere: string;
    state: GameState;
  }> {
    const response = await fetch(`${API_BASE}/game/council-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message,
        conversation_history: conversationHistory,
        api_key: apiKey,
        model,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '廷议对话失败');
    }

    return response.json();
  },

  /**
   * 提前结束关卡
   */
  async endChapterEarly(
    sessionId: string,
    pendingConsequences: any[],
    apiKey: string,
    model?: string
  ): Promise<{
    success: boolean;
    chapter_ended: boolean;
    victory: boolean;
    reason: string;
    pending_consequences_count: number;
    next_chapter_available: { id: string; name: string } | null;
    state: GameState;
  }> {
    const response = await fetch(`${API_BASE}/game/end-chapter`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        pending_consequences: pendingConsequences,
        api_key: apiKey,
        model,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || '结束关卡失败');
    }

    return response.json();
  },
};
