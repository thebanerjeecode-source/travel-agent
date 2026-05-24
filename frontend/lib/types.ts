export interface TraceEntry {
  step: number;
  agent: string;
  provider: string;
  model: string;
  message: string;
}

export interface QuotaUsage {
  rpm_used: number;
  rpm_limit: number;
  rpd_used: number;
  rpd_limit: number;
}

export interface Activity {
  time: string;
  name: string;
  duration_hours: number;
}

export interface DayPlan {
  day: number;
  city: string;
  theme: string;
  activities: Activity[];
}

export interface AccommodationOption {
  name: string;
  price_per_night_usd: number;
  tier: string;
}

export interface AccommodationPlan {
  city: string;
  nights: number;
  recommended_neighborhood: string;
  reason: string;
  options: AccommodationOption[];
}

export interface InterCityLeg {
  from: string;
  to: string;
  mode: string;
  duration_hours: number;
  estimated_cost_usd: number;
  suggested_day: number;
}

export interface TransportPlan {
  inter_city: InterCityLeg[];
  local_transit_notes: string;
}

export interface BudgetBreakdown {
  budget_usd: number;
  estimated_total_usd: number;
  breakdown: Record<string, number>;
  status: string;
  savings_suggestions: string[];
}

export interface TravelRequirements {
  duration_days: number;
  destinations: string[];
  budget_usd: number;
  interests: string[];
  dislikes: string[];
}

export interface TripPlan {
  summary: string;
  requirements?: TravelRequirements;
  day_by_day: DayPlan[];
  neighborhoods_to_stay: AccommodationPlan[];
  logistics?: TransportPlan;
  budget?: BudgetBreakdown;
  assumptions: string[];
  validation_passed: boolean;
  status: string;
  data_provenance?: Record<string, string>;
}

export interface PlanResponse {
  session_id: string;
  status: string;
  raw_request: string;
  trip_plan: TripPlan;
  trace: TraceEntry[];
  quota: { groq: QuotaUsage; gemini: QuotaUsage };
  data_provenance?: Record<string, string>;
  warning?: string;
  error?: string;
}

export interface PlanRequest {
  request: string;
  dry_run?: boolean;
  intent_only?: boolean;
  planning_only?: boolean;
  data_mode?: "auto" | "seed" | "live";
}
