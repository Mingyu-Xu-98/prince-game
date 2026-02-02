// 游戏类型定义

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
  hatred: number;
  is_hostile: boolean;
}

export interface GameState {
  session_id: string;
  turn: number;
  power: PowerVector;
  relations: {
    lion: RobotRelation;
    fox: RobotRelation;
    balance: RobotRelation;
  };
  warnings: string[];
  game_over: boolean;
  game_over_reason: string | null;
}

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

export interface ParsedIntent {
  intent: string;
  target: string;
  method: string;
  goal: string;
  cost: string;
  tone: string;
  keywords: string[];
  raw_input: string;
}

export interface SkillReport {
  score: number;
  assessment: string;
  tone: string;
  keywords: string[];
}

export interface AuditSummary {
  total_delta: {
    authority: number;
    fear: number;
    love: number;
  };
  combined_assessment: string;
  all_warnings: string[];
  trigger_events: string[];
  skill_reports: {
    lion: SkillReport;
    fox: SkillReport;
    balance: SkillReport;
  };
}

export interface Settlement {
  old_power: PowerVector;
  new_power: PowerVector;
  power_changes: {
    authority: number;
    fear: number;
    love: number;
  };
  triggered_event: GameEvent | null;
  game_over: boolean;
  game_over_reason: string | null;
  warnings: string[];
}

export interface TurnResult {
  turn: number;
  player_input: string;
  parsed_intent: ParsedIntent;
  robot_responses: {
    lion: string;
    fox: string;
    balance: string;
  };
  audit_summary: AuditSummary;
  settlement: Settlement;
  state: GameState;
  event: GameEvent | null;
}

export interface DialogueEntry {
  turn: number;
  speaker: 'player' | 'lion' | 'fox' | 'balance';
  content: string;
}
