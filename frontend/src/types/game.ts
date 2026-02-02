// 游戏类型定义 - 支持关卡系统

export interface PowerValue {
  value: number;
  label: string;
}

export interface PowerVector {
  authority: PowerValue;
  fear: PowerValue;
  love: PowerValue;
  total: number;
}

export interface RobotRelation {
  trust: number;
  loyalty: number;
  is_hostile: boolean;
  will_betray: boolean;
}

export interface GameState {
  session_id: string;
  current_chapter: string;
  chapter_turn: number;
  total_turn: number;
  power: PowerVector;
  relations: {
    lion: RobotRelation;
    fox: RobotRelation;
    balance: RobotRelation;
  };
  credit_score: number;
  active_promises: number;
  leverages_against_you: number;
  warnings: string[];
  game_over: boolean;
  game_over_reason: string | null;
}

// 关卡相关
export interface ChapterInfo {
  id: string;
  name: string;
  subtitle: string;
  complexity: number;
  status: 'locked' | 'available' | 'active' | 'completed' | 'failed';
}

// 顾问辩论条目
export interface AdvisorDebateEntry {
  suggestion: string;
  reasoning: string;
  tone: string;
  trust_level: number;
  has_leverage?: boolean;
}

// 议会辩论
export interface CouncilDebate {
  lion: AdvisorDebateEntry;
  fox: AdvisorDebateEntry;
  balance?: AdvisorDebateEntry;
  dynamic_dialogue?: Array<{
    speaker: string;
    content: string;
  }>;
}

// 前端使用的关卡场景
export interface ChapterScene {
  id: string;
  name: string;
  subtitle: string;
  complexity: number;
  max_turns: number;
  current_turn: number;
  background: string;
  scene_snapshot: string;
  dilemma: string;
  opening_narration: string;
  council_debate: CouncilDebate;
  hide_values: boolean;
}

export interface DecisionAnalysis {
  contains_promise: boolean;
  promise_target?: string;
  is_violent: boolean;
  is_deceptive: boolean;
  is_fair: boolean;
  is_secret_action: boolean;
  followed_advisor?: string;
}

export interface ChapterResult {
  chapter_ended: boolean;
  victory: boolean;
  reason?: string;
  chapter_summary?: string;
}

export interface DecisionResult {
  turn: number;
  decision_analysis: DecisionAnalysis;
  power_changes: {
    authority: number;
    fear: number;
    love: number;
  };
  new_state: GameState;
  chapter_result: ChapterResult;
  advisor_responses: {
    lion: string;
    fox: string;
    balance: string;
  };
  warnings: string[];
  leverage_gained?: {
    holder: string;
    type: string;
    description: string;
  };
  secret_leaked?: boolean;
  next_chapter_available?: {
    id: string;
    name: string;
  };
  final_audit?: FinalAudit;
}

export interface FinalAudit {
  total_decisions: number;
  violent_decisions: number;
  deceptive_decisions: number;
  fair_decisions: number;
  promises_made: number;
  promises_broken: number;
  secrets_leaked: number;
  leverages_held: number;
  violence_ratio: number;
  deception_ratio: number;
  fairness_ratio: number;
  promise_reliability: number;
  reputation: string;
  final_score: number;
}

// 事件相关 (保留旧的兼容)
export interface EventChoice {
  id: string;
  text: string;
  impact: {
    authority: number;
    fear: number;
    love: number;
  };
}

export interface GameEvent {
  id: string;
  type: string;
  title: string;
  narration: string;
  choices: EventChoice[];
}

export interface DialogueEntry {
  turn: number;
  speaker: 'player' | 'lion' | 'fox' | 'balance' | 'system';
  content: string;
  is_promise?: boolean;
  is_lie?: boolean;
}
