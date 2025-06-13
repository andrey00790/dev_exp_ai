export interface DataSource {
  source_type: string;
  source_name: string;
  is_enabled_semantic_search: boolean;
  is_enabled_architecture_generation: boolean;
  connection_config: Record<string, any>;
  last_sync_at: string | null;
  sync_status: 'pending' | 'running' | 'success' | 'error';
  sync_schedule: string | null;
  auto_sync_on_startup: boolean;
}

export interface UserSettings {
  data_sources: DataSource[];
  preferences: {
    language?: string;
    theme?: string;
    default_doc_type?: string;
  };
} 