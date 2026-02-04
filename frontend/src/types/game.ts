// 游戏类型定义 - 支持关卡系统和新裁决系统

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

// 观测透镜选项
export interface ObservationLensChoice {
  name: string;
  description: string;
  effect: string;
  warning: string;
}

// 初始化场景响应
export interface InitializationScene {
  scene: string;
  lens_choices: Record<string, ObservationLensChoice>;
  mountain_view: string;
}

// 裁决元数据
export interface JudgmentMetadata {
  player_strategy: string;
  machiavelli_traits: string[];
  machiavelli_critique: string;
  outcome_level: string;
  consequence: string;
}

// ============ 因果系统 (Causal System) ============

// 伏笔种子 (Shadow Seed) - 埋下的雷，将在未来触发
export interface ShadowSeed {
  id: string;                          // 唯一标识
  origin_chapter: string;              // 来源关卡 ID
  origin_turn: number;                 // 来源回合
  trigger_chapter?: string;            // 触发关卡 (具体关卡ID)
  trigger_delay?: number;              // 延迟触发回合数
  trigger_condition?: string;          // 条件触发 (如 "ANY_RIOT", "LOW_LOVE", "WAR")
  tag: 'DECEPTION' | 'VIOLENCE' | 'BROKEN_PROMISE' | 'MERCY' | 'DEBT' | 'CORRUPTION' | 'BETRAYAL' | 'OTHER';
  description: string;                 // 语义描述 (给 AI 看)
  player_visible_hint?: string;        // 给玩家的隐晦提示
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  created_at: number;                  // 创建时间戳
  is_triggered: boolean;               // 是否已触发
  triggered_at?: number;               // 触发时间戳
}

// 即时状态标记 (Immediate Flag) - 当前回合生效的 Buff/Debuff
export interface ImmediateFlag {
  id: string;
  type: 'BUFF' | 'DEBUFF' | 'MODIFIER';
  name: string;
  description: string;
  effect_on_scene: string;             // 对场景的影响描述
  duration_turns?: number;             // 持续回合数 (undefined = 永久)
  source_seed_id?: string;             // 来源种子ID (如果是种子触发的)
  modifiers?: {                        // 数值修正
    authority?: number;
    fear?: number;
    love?: number;
    trust_lion?: number;
    trust_fox?: number;
    trust_balance?: number;
  };
}

// 因果状态 (Causal State) - 完整的因果池
export interface CausalState {
  shadow_seeds: ShadowSeed[];          // 伏笔种子库
  immediate_flags: ImmediateFlag[];    // 即时状态列表
  triggered_echoes: TriggeredEcho[];   // 已触发的回响记录
}

// 触发的回响 (用于记录和展示)
export interface TriggeredEcho {
  seed_id: string;
  seed_description: string;
  trigger_chapter: string;
  trigger_turn: number;
  echo_narrative: string;              // AI 生成的叙事文本
  crisis_modifier: string;             // 对当前危机的影响
  advisor_reactions: {                 // 顾问的反应
    lion?: string;
    fox?: string;
    balance?: string;
  };
}

// API 返回的新种子 (政令结算时)
export interface NewSeedFromDecision {
  add_seeds?: ShadowSeed[];            // 新增的种子
  remove_seed_ids?: string[];          // 移除的种子 (被化解)
  add_flags?: ImmediateFlag[];         // 新增的即时状态
  remove_flag_ids?: string[];          // 移除的即时状态
}

// 关卡初始化时的因果检查结果
export interface CausalCheckResult {
  active_shadows: ShadowSeed[];        // 本关卡需要触发的种子
  echoes_to_inject: TriggeredEcho[];   // 需要注入场景的回响
  modified_scene?: string;             // 被因果修改后的场景描述
  advisor_warnings?: {                 // 顾问的警告
    lion?: string;
    fox?: string;
    balance?: string;
  };
}

// 旧的类型保持兼容
export interface CausalSeedInfo {
  action_type: string;
  description: string;
  severity: number;
  warning: string;
}

// 因果回响 (旧版兼容)
export interface EchoTriggered {
  source_chapter: number;
  source_turn: number;
  action_type: string;
  description: string;
  echo_message: string;
  crisis: string;
}

// 顾问状态变化
export interface AdvisorChangeInfo {
  status: string;
  warning: string;
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
  observation_lens?: string;  // 观测透镜

  // 因果系统
  causal_state?: CausalState;
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

// 政令后续影响
export interface DecreeConsequence {
  id: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  type: 'political' | 'economic' | 'military' | 'social' | 'diplomatic';
  potential_outcomes: string[];
  requires_action: boolean;           // 是否必须处理
  deadline_turns?: number;            // 剩余回合数，超时自动触发
  auto_trigger_effect?: string;       // 超时自动触发的效果描述
  unresolved_penalty?: {              // 不处理时每回合的惩罚
    authority?: number;
    fear?: number;
    love?: number;
    credit?: number;
  };
  resolved?: boolean;                 // 是否已被处理
  resolution_turn?: number;           // 在哪个回合被处理
}

// 累积的未处理影响（会影响后续关卡）
export interface PendingConsequence {
  source_chapter: string;
  source_turn: number;
  consequence: DecreeConsequence;
  turns_remaining?: number;
}

// 把柄使用结果
export interface LeverageUsedResult {
  advisor: string;
  advisor_name: string;
  leverage_type: string;
  description: string;
  impact: {
    authority?: number;
    fear?: number;
    love?: number;
  };
  narrative: string;
}

// 关卡结果扩展
export interface ChapterResultExtended extends ChapterResult {
  triggered_by?: string;  // 触发原因: authority_zero, love_zero, assassination, credit_bankruptcy, betrayal, balance_failure
  betrayer?: string;      // 如果是背叛触发，记录背叛者
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
  chapter_result: ChapterResultExtended;
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

  // 新裁决系统字段
  judgment_metadata?: JudgmentMetadata;
  causal_seed?: CausalSeedInfo;
  echo_triggered?: EchoTriggered;
  advisor_changes?: Record<string, AdvisorChangeInfo>;

  // 政令后续影响
  decree_consequences?: DecreeConsequence[];
  pending_consequences?: PendingConsequence[];

  // 因果系统更新
  causal_update?: NewSeedFromDecision;
  triggered_echoes?: TriggeredEcho[];

  // 把柄系统
  leverage_used?: LeverageUsedResult;

  // 信用系统
  credit_warning?: string;

  // 危机系统
  resolved_crises?: string[];           // 本回合解决的危机
  triggered_crises?: string[];          // 自动触发的危机
  active_crises?: ActiveCrisis[];       // 当前活动危机
  overdue_warning?: string[];           // 即将超时的危机
}

// 活动危机
export interface ActiveCrisis {
  id: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  type: string;
  requires_action: boolean;
  deadline_turns: number;
  auto_trigger_effect?: string;
  created_turn: number;
  created_chapter: string;
  resolved: boolean;
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
