// User types
export interface User {
  id: string;
  name: string;
  email: string;
  avatar_url: string | null;
  role: 'manager' | 'member';
  team_id: string;
  auth_provider: string;
  created_at: string;
}

// Team types
export interface Team {
  id: string;
  name: string;
  created_at: string;
}

// Shift type types
export interface ShiftType {
  id: string;
  team_id: string;
  name: string;
  start_time: string;
  end_time: string;
  color: string;
  is_active: boolean;
  created_at: string;
}

// Schedule period types
export type PeriodStatus = 'draft' | 'collecting_wishes' | 'solving' | 'proposed' | 'published';

export interface SchedulePeriod {
  id: string;
  team_id: string;
  start_date: string;
  end_date: string;
  status: PeriodStatus;
  created_at: string;
}

// Day shift slot types
export interface DayShiftSlot {
  id: string;
  period_id: string;
  date: string;
  shift_type_id: string;
  min_staff: number;
  max_staff: number;
}

// Constraint types
export type ConstraintKind = 'vacation' | 'unavailable' | 'preference_avoid' | 'preference_want';

export interface MemberConstraint {
  id: string;
  period_id: string;
  user_id: string;
  kind: ConstraintKind;
  start_date: string;
  end_date: string;
  shift_type_id: string | null;
  note: string | null;
  created_at: string;
}

// Proposal types
export type ProposalStatus = 'candidate' | 'selected';

export interface RosterProposal {
  id: string;
  period_id: string;
  created_at: string;
  soft_penalty_total: number;
  hard_violation_count: number;
  status: ProposalStatus;
}

// Assignment types
export interface Assignment {
  id: string;
  proposal_id: string;
  date: string;
  shift_type_id: string;
  user_id: string;
}

// Violation types
export interface Violation {
  id: string;
  proposal_id: string;
  constraint_kind: string;
  hard: boolean;
  user_id: string | null;
  date: string | null;
  message: string;
  penalty: number;
}

// Auth types
export interface Token {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    name: string;
    email: string;
    role: string;
    team_id: string;
  };
}

// API response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// Calendar types
export interface CalendarDay {
  date: Date;
  dayOfWeek: number;
  isCurrentMonth: boolean;
  isToday: boolean;
  isSelected: boolean;
  shiftSlots: DayShiftSlot[];
  assignments: Assignment[];
}

// Form types
export interface CreateShiftTypeForm {
  name: string;
  start_time: string;
  end_time: string;
  color: string;
  is_active: boolean;
}

export interface CreatePeriodForm {
  start_date: string;
  end_date: string;
}

export interface CreateConstraintForm {
  period_id: string;
  kind: ConstraintKind;
  start_date: string;
  end_date: string;
  shift_type_id?: string;
  note?: string;
}
