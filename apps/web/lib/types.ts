export type TrackingState = {
  user_key: string;
  is_applied: boolean;
  applied_at: string | null;
  notes: string | null;
  documents_ready: string[];
};

export type Opportunity = {
  id: number;
  source_name: string;
  source_url: string;
  official_url: string | null;
  verification_status: string;
  status: string;
  title: string;
  project_title: string | null;
  institution: string | null;
  department: string | null;
  lab: string | null;
  country: string | null;
  city: string | null;
  domain_primary: string | null;
  domain_tags: string[];
  supervisor_name: string | null;
  supervisor_profile_url: string | null;
  funding: string | null;
  salary_stipend: string | null;
  duration_text: string | null;
  start_date_text: string | null;
  deadline_text: string | null;
  qualification_requirements?: string | null;
  required_documents?: string[];
  application_process?: string | null;
  description?: string | null;
  contact_info?: string | null;
  last_seen_at: string | null;
  tracking: TrackingState | null;
};

export type SourceDescriptor = {
  source_name: string;
  display_name: string;
  trust_level: string;
  category: string;
  source_type: string;
  live_ready: boolean;
  notes: string | null;
};
