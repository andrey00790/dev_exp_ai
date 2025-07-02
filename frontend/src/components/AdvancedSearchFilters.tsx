import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControl,
  Checkbox,
  FormControlLabel,
  FormGroup,
  TextField,
  Chip,
  Button,
  Grid,
  Slider,
  Switch,
  Autocomplete,
  Alert,
  Badge
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Clear as ClearIcon,
  FilterList as FilterIcon,
  Bookmark as BookmarkIcon,
  Info as InfoIcon
} from '@mui/icons-material';

interface SourceFilter {
  confluence?: string[];
  jira?: string[];
  gitlab?: string[];
  local_files?: string[];
}

interface ContentFilter {
  document_types?: string[];
  categories?: string[];
  file_extensions?: string[];
  languages?: string[];
}

interface AuthorFilter {
  authors?: string[];
  assignees?: string[];
  created_by?: string[];
  updated_by?: string[];
}

interface TimeFilter {
  created_after?: Date;
  created_before?: Date;
  updated_after?: Date;
  updated_before?: Date;
}

interface QualityFilter {
  min_quality_score?: number;
  min_relevance_score?: number;
  min_word_count?: number;
  max_word_count?: number;
}

interface StatusFilter {
  document_status?: string[];
  priorities?: string[];
  jira_statuses?: string[];
}

interface TagsFilter {
  tags?: string[];
  labels?: string[];
  exclude_tags?: string[];
}

interface AdvancedFilters {
  sources?: SourceFilter;
  content?: ContentFilter;
  authors?: AuthorFilter;
  time?: TimeFilter;
  quality?: QualityFilter;
  status?: StatusFilter;
  tags?: TagsFilter;
}

interface FilterSuggestion {
  filter_type: string;
  filter_name: string;
  values: Array<{
    value: string;
    count?: number;
    label: string;
    description?: string;
  }>;
  description: string;
}

interface AdvancedSearchFiltersProps {
  filters: AdvancedFilters;
  onFiltersChange: (filters: AdvancedFilters) => void;
  onSearch: () => void;
  loading?: boolean;
  resultsCount?: number;
}

const AdvancedSearchFilters: React.FC<AdvancedSearchFiltersProps> = ({
  filters,
  onFiltersChange,
  onSearch,
  loading = false,
  resultsCount = 0
}) => {
  const [suggestions, setSuggestions] = useState<FilterSuggestion[]>([]);
  const [presets, setPresets] = useState<Record<string, any>>({});
  const [expanded, setExpanded] = useState<string[]>(['sources']);
  const [activeFiltersCount, setActiveFiltersCount] = useState(0);

  useEffect(() => {
    loadFilterSuggestions();
    loadFilterPresets();
  }, []);

  useEffect(() => {
    // Подсчет активных фильтров
    let count = 0;
    Object.values(filters).forEach(filterGroup => {
      if (filterGroup && typeof filterGroup === 'object') {
        Object.values(filterGroup).forEach(filterValue => {
          if (Array.isArray(filterValue) && filterValue.length > 0) count++;
          else if (filterValue !== undefined && filterValue !== null && filterValue !== '') count++;
        });
      }
    });
    setActiveFiltersCount(count);
  }, [filters]);

  const loadFilterSuggestions = async () => {
    try {
      const response = await fetch('/api/v1/search/advanced/filters/suggestions');
      const data = await response.json();
      setSuggestions(data);
    } catch (error) {
      console.error('Ошибка загрузки предложений фильтров:', error);
    }
  };

  const loadFilterPresets = async () => {
    try {
      const response = await fetch('/api/v1/search/advanced/filters/presets');
      const data = await response.json();
      setPresets(data.presets || {});
    } catch (error) {
      console.error('Ошибка загрузки пресетов фильтров:', error);
    }
  };

  const handleAccordionChange = (panel: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
    setExpanded(prev => 
      isExpanded 
        ? [...prev, panel]
        : prev.filter(p => p !== panel)
    );
  };

  const updateFilter = (category: keyof AdvancedFilters, field: string, value: any) => {
    const newFilters = {
      ...filters,
      [category]: {
        ...filters[category],
        [field]: value
      }
    };
    onFiltersChange(newFilters);
  };

  const clearAllFilters = () => {
    onFiltersChange({});
  };

  const applyPreset = (presetKey: string) => {
    const preset = presets[presetKey];
    if (preset) {
      onFiltersChange(preset.filters);
    }
  };

  const getSuggestionForFilter = (filterType: string, filterName: string) => {
    return suggestions.find(s => s.filter_type === filterType && s.filter_name === filterName);
  };

  const renderSourceFilters = () => {
    const confluenceOptions = getSuggestionForFilter('sources', 'confluence')?.values || [];
    const jiraOptions = getSuggestionForFilter('sources', 'jira')?.values || [];
    const gitlabOptions = getSuggestionForFilter('sources', 'gitlab')?.values || [];

    return (
      <Accordion expanded={expanded.includes('sources')} onChange={handleAccordionChange('sources')}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6">Источники данных</Typography>
            {(filters.sources?.confluence?.length || filters.sources?.jira?.length || filters.sources?.gitlab?.length || filters.sources?.local_files?.length) && (
              <Badge badgeContent={
                (filters.sources?.confluence?.length || 0) +
                (filters.sources?.jira?.length || 0) +
                (filters.sources?.gitlab?.length || 0) +
                (filters.sources?.local_files?.length || 0)
              } color="primary" />
            )}
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <Autocomplete
                  multiple
                  options={confluenceOptions}
                  getOptionLabel={(option) => option.label}
                  value={confluenceOptions.filter(opt => filters.sources?.confluence?.includes(opt.value)) || []}
                  onChange={(_, newValue) => updateFilter('sources', 'confluence', newValue.map(v => v.value))}
                  renderInput={(params) => (
                    <TextField {...params} label="Confluence Spaces" placeholder="Выберите пространства" />
                  )}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip
                        variant="outlined"
                        label={`${option.label} (${option.count || 0})`}
                        {...getTagProps({ index })}
                        key={option.value}
                      />
                    ))
                  }
                />
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <Autocomplete
                  multiple
                  options={jiraOptions}
                  getOptionLabel={(option) => option.label}
                  value={jiraOptions.filter(opt => filters.sources?.jira?.includes(opt.value)) || []}
                  onChange={(_, newValue) => updateFilter('sources', 'jira', newValue.map(v => v.value))}
                  renderInput={(params) => (
                    <TextField {...params} label="Jira Projects" placeholder="Выберите проекты" />
                  )}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip
                        variant="outlined"
                        label={`${option.label} (${option.count || 0})`}
                        {...getTagProps({ index })}
                        key={option.value}
                      />
                    ))
                  }
                />
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <Autocomplete
                  multiple
                  options={gitlabOptions}
                  getOptionLabel={(option) => option.label}
                  value={gitlabOptions.filter(opt => filters.sources?.gitlab?.includes(opt.value)) || []}
                  onChange={(_, newValue) => updateFilter('sources', 'gitlab', newValue.map(v => v.value))}
                  renderInput={(params) => (
                    <TextField {...params} label="GitLab Repositories" placeholder="Выберите репозитории" />
                  )}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip
                        variant="outlined"
                        label={`${option.label} (${option.count || 0})`}
                        {...getTagProps({ index })}
                        key={option.value}
                      />
                    ))
                  }
                />
              </FormControl>
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={filters.sources?.local_files?.includes('bootstrap') || false}
                    onChange={(e) => updateFilter('sources', 'local_files', e.target.checked ? ['bootstrap'] : [])}
                  />
                }
                label="Локальные файлы для обучения"
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>
    );
  };

  const renderContentFilters = () => {
    const documentTypes = [
      { value: 'page', label: 'Страницы' },
      { value: 'issue', label: 'Задачи' },
      { value: 'file', label: 'Файлы' },
      { value: 'comment', label: 'Комментарии' }
    ];

    const categories = [
      { value: 'documentation', label: 'Документация' },
      { value: 'code', label: 'Код' },
      { value: 'requirements', label: 'Требования' },
      { value: 'architecture', label: 'Архитектура' },
      { value: 'training_data', label: 'Обучающие данные' }
    ];

    const fileExtensions = [
      { value: 'md', label: 'Markdown (.md)' },
      { value: 'py', label: 'Python (.py)' },
      { value: 'js', label: 'JavaScript (.js)' },
      { value: 'yaml', label: 'YAML (.yaml)' },
      { value: 'json', label: 'JSON (.json)' },
      { value: 'txt', label: 'Text (.txt)' },
      { value: 'pdf', label: 'PDF (.pdf)' }
    ];

    return (
      <Accordion expanded={expanded.includes('content')} onChange={handleAccordionChange('content')}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6">Тип контента</Typography>
            {(filters.content?.document_types?.length || filters.content?.categories?.length || filters.content?.file_extensions?.length) && (
              <Badge badgeContent={
                (filters.content?.document_types?.length || 0) +
                (filters.content?.categories?.length || 0) +
                (filters.content?.file_extensions?.length || 0)
              } color="primary" />
            )}
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Типы документов</Typography>
              <FormGroup>
                {documentTypes.map(type => (
                  <FormControlLabel
                    key={type.value}
                    control={
                      <Checkbox
                        checked={filters.content?.document_types?.includes(type.value) || false}
                        onChange={(e) => {
                          const current = filters.content?.document_types || [];
                          const updated = e.target.checked
                            ? [...current, type.value]
                            : current.filter(t => t !== type.value);
                          updateFilter('content', 'document_types', updated);
                        }}
                      />
                    }
                    label={type.label}
                  />
                ))}
              </FormGroup>
            </Grid>

            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Категории</Typography>
              <FormGroup>
                {categories.map(category => (
                  <FormControlLabel
                    key={category.value}
                    control={
                      <Checkbox
                        checked={filters.content?.categories?.includes(category.value) || false}
                        onChange={(e) => {
                          const current = filters.content?.categories || [];
                          const updated = e.target.checked
                            ? [...current, category.value]
                            : current.filter(c => c !== category.value);
                          updateFilter('content', 'categories', updated);
                        }}
                      />
                    }
                    label={category.label}
                  />
                ))}
              </FormGroup>
            </Grid>

            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Расширения файлов</Typography>
              <FormGroup>
                {fileExtensions.map(ext => (
                  <FormControlLabel
                    key={ext.value}
                    control={
                      <Checkbox
                        checked={filters.content?.file_extensions?.includes(ext.value) || false}
                        onChange={(e) => {
                          const current = filters.content?.file_extensions || [];
                          const updated = e.target.checked
                            ? [...current, ext.value]
                            : current.filter(f => f !== ext.value);
                          updateFilter('content', 'file_extensions', updated);
                        }}
                      />
                    }
                    label={ext.label}
                  />
                ))}
              </FormGroup>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>
    );
  };

  const renderTimeFilters = () => {
    return (
      <Accordion expanded={expanded.includes('time')} onChange={handleAccordionChange('time')}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6">Временной период</Typography>
            {(filters.time?.created_after || filters.time?.created_before || filters.time?.updated_after || filters.time?.updated_before) && (
              <Badge badgeContent="•" color="primary" />
            )}
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mb: 2 }}>Быстрые фильтры</Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                {[
                  { label: 'Сегодня', days: 1 },
                  { label: 'Неделя', days: 7 },
                  { label: 'Месяц', days: 30 },
                  { label: 'Квартал', days: 90 }
                ].map(period => (
                  <Button
                    key={period.label}
                    size="small"
                    variant="outlined"
                    onClick={() => {
                      const now = new Date();
                      const pastDate = new Date(now.getTime() - period.days * 24 * 60 * 60 * 1000);
                      updateFilter('time', 'updated_after', pastDate);
                      updateFilter('time', 'updated_before', now);
                    }}
                  >
                    {period.label}
                  </Button>
                ))}
              </Box>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Дата создания</Typography>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <TextField
                  label="С"
                  type="date"
                  value={filters.time?.created_after ? filters.time.created_after.toISOString().split('T')[0] : ''}
                  onChange={(e) => updateFilter('time', 'created_after', e.target.value ? new Date(e.target.value) : undefined)}
                />
                <TextField
                  label="По"
                  type="date"
                  value={filters.time?.created_before ? filters.time.created_before.toISOString().split('T')[0] : ''}
                  onChange={(e) => updateFilter('time', 'created_before', e.target.value ? new Date(e.target.value) : undefined)}
                />
              </Box>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Дата обновления</Typography>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <TextField
                  label="С"
                  type="date"
                  value={filters.time?.updated_after ? filters.time.updated_after.toISOString().split('T')[0] : ''}
                  onChange={(e) => updateFilter('time', 'updated_after', e.target.value ? new Date(e.target.value) : undefined)}
                />
                <TextField
                  label="По"
                  type="date"
                  value={filters.time?.updated_before ? filters.time.updated_before.toISOString().split('T')[0] : ''}
                  onChange={(e) => updateFilter('time', 'updated_before', e.target.value ? new Date(e.target.value) : undefined)}
                />
              </Box>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>
    );
  };

  const renderQualityFilters = () => {
    return (
      <Accordion expanded={expanded.includes('quality')} onChange={handleAccordionChange('quality')}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6">Качество контента</Typography>
            {(filters.quality?.min_quality_score || filters.quality?.min_word_count || filters.quality?.max_word_count) && (
              <Badge badgeContent="•" color="primary" />
            )}
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Минимальная оценка качества: {filters.quality?.min_quality_score || 0}
              </Typography>
              <Slider
                value={filters.quality?.min_quality_score || 0}
                onChange={(_, value) => updateFilter('quality', 'min_quality_score', value)}
                min={0}
                max={1}
                step={0.1}
                marks={[
                  { value: 0, label: '0' },
                  { value: 0.5, label: '0.5' },
                  { value: 1, label: '1' }
                ]}
                valueLabelDisplay="auto"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Количество слов</Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  label="Мин"
                  type="number"
                  size="small"
                  value={filters.quality?.min_word_count || ''}
                  onChange={(e) => updateFilter('quality', 'min_word_count', parseInt(e.target.value) || undefined)}
                />
                <TextField
                  label="Макс"
                  type="number"
                  size="small"
                  value={filters.quality?.max_word_count || ''}
                  onChange={(e) => updateFilter('quality', 'max_word_count', parseInt(e.target.value) || undefined)}
                />
              </Box>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>
    );
  };

  const renderPresets = () => {
    return (
      <Card sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            <BookmarkIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Быстрые фильтры
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {Object.entries(presets).map(([key, preset]) => (
              <Button
                key={key}
                variant="outlined"
                size="small"
                onClick={() => applyPreset(key)}
                startIcon={<FilterIcon />}
              >
                {preset.name}
              </Button>
            ))}
          </Box>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box>
      {/* Заголовок с кнопками действий */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h5">
            Расширенный поиск
          </Typography>
          {activeFiltersCount > 0 && (
            <Badge badgeContent={activeFiltersCount} color="primary">
              <FilterIcon />
            </Badge>
          )}
          {resultsCount > 0 && (
            <Typography variant="body2" color="text.secondary">
              Найдено: {resultsCount.toLocaleString()} документов
            </Typography>
          )}
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<ClearIcon />}
            onClick={clearAllFilters}
            disabled={activeFiltersCount === 0}
          >
            Очистить
          </Button>
          <Button
            variant="contained"
            onClick={onSearch}
            disabled={loading}
          >
            {loading ? 'Поиск...' : 'Найти'}
          </Button>
        </Box>
      </Box>

      {/* Информационное сообщение */}
      <Alert severity="info" sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <InfoIcon />
          <Typography variant="body2">
            Настройте фильтры для точного поиска по метаданным документов. 
            Поиск работает по выбранным источникам, генерация документов использует все доступные источники.
          </Typography>
        </Box>
      </Alert>

      {/* Основные фильтры */}
      <Card>
        <CardContent>
          {renderSourceFilters()}
          {renderContentFilters()}
          {renderTimeFilters()}
          {renderQualityFilters()}
        </CardContent>
      </Card>

      {/* Пресеты */}
      {renderPresets()}
    </Box>
  );
};

export default AdvancedSearchFilters; 