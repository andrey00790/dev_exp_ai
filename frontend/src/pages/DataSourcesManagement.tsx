import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  Button,
  Chip,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  LinearProgress,
  IconButton,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';
import {
  Sync as SyncIcon,
  Settings as SettingsIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { apiClient } from '../api/apiClient';

interface DataSource {
  source_type: string;
  source_name: string;
  enabled: boolean;
  last_sync: string | null;
  next_sync: string | null;
  running: boolean;
  documents_count: number;
  sync_schedule: string;
  incremental: boolean;
}

interface SearchSourcesConfig {
  user_id: string;
  enabled_sources: string[];
  search_preferences: Record<string, any>;
}

const DataSourcesManagement: React.FC = () => {
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [searchConfig, setSearchConfig] = useState<SearchSourcesConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<Record<string, boolean>>({});
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Диалоги
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [searchConfigDialogOpen, setSearchConfigDialogOpen] = useState(false);
  const [selectedSource, setSelectedSource] = useState<DataSource | null>(null);

  // Форма для нового источника
  const [newSource, setNewSource] = useState({
    source_type: 'confluence',
    source_name: '',
    enabled: true,
    sync_schedule: '0 2 * * *',
    incremental: true,
    config: {}
  });

  useEffect(() => {
    loadDataSources();
    loadSearchConfig();
  }, []);

  const loadDataSources = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/v1/data-sources/');
      setDataSources(response.data);
    } catch (err: any) {
      setError(`Ошибка загрузки источников: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadSearchConfig = async () => {
    try {
      // Получаем ID текущего пользователя (здесь должна быть логика получения из контекста)
      const userId = 'current_user'; // Заменить на реальный ID
      const response = await apiClient.get(`/api/v1/data-sources/search-sources/${userId}`);
      setSearchConfig(response.data);
    } catch (err: any) {
      console.warn('Не удалось загрузить конфигурацию поиска:', err.message);
    }
  };

  const handleSyncSource = async (sourceType: string, sourceName: string) => {
    const sourceKey = `${sourceType}_${sourceName}`;
    
    try {
      setSyncing(prev => ({ ...prev, [sourceKey]: true }));
      
      await apiClient.post(`/api/v1/data-sources/${sourceType}/${sourceName}/sync`);
      
      setSuccess(`Синхронизация ${sourceName} запущена`);
      
      // Обновляем статус через несколько секунд
      setTimeout(() => {
        loadDataSources();
      }, 2000);
      
    } catch (err: any) {
      setError(`Ошибка синхронизации: ${err.message}`);
    } finally {
      setSyncing(prev => ({ ...prev, [sourceKey]: false }));
    }
  };

  const handleToggleSource = async (source: DataSource) => {
    try {
      const updatedSource = {
        ...source,
        enabled: !source.enabled
      };

      await apiClient.put(
        `/api/v1/data-sources/${source.source_type}/${source.source_name}`,
        updatedSource
      );

      setSuccess(`Источник ${source.source_name} ${updatedSource.enabled ? 'включен' : 'отключен'}`);
      loadDataSources();
      
    } catch (err: any) {
      setError(`Ошибка обновления источника: ${err.message}`);
    }
  };

  const handleAddSource = async () => {
    try {
      await apiClient.post('/api/v1/data-sources/', newSource);
      
      setSuccess(`Источник ${newSource.source_name} создан`);
      setAddDialogOpen(false);
      setNewSource({
        source_type: 'confluence',
        source_name: '',
        enabled: true,
        sync_schedule: '0 2 * * *',
        incremental: true,
        config: {}
      });
      loadDataSources();
      
    } catch (err: any) {
      setError(`Ошибка создания источника: ${err.message}`);
    }
  };

  const handleUpdateSearchSources = async (enabledSources: string[]) => {
    try {
      const userId = 'current_user'; // Заменить на реальный ID
      
      await apiClient.put(`/api/v1/data-sources/search-sources/${userId}`, {
        user_id: userId,
        enabled_sources: enabledSources,
        search_preferences: searchConfig?.search_preferences || {}
      });

      setSuccess('Настройки поиска обновлены');
      setSearchConfigDialogOpen(false);
      loadSearchConfig();
      
    } catch (err: any) {
      setError(`Ошибка обновления настроек поиска: ${err.message}`);
    }
  };

  const formatLastSync = (lastSync: string | null) => {
    if (!lastSync) return 'Никогда';
    return new Date(lastSync).toLocaleString('ru-RU');
  };

  const formatNextSync = (nextSync: string | null) => {
    if (!nextSync) return 'Не запланирована';
    return new Date(nextSync).toLocaleString('ru-RU');
  };

  const getSourceTypeIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'confluence': return '📚';
      case 'gitlab': return '🦊';
      case 'jira': return '🎯';
      case 'local_files': return '📁';
      default: return '📄';
    }
  };

  const getStatusColor = (source: DataSource) => {
    if (source.running) return 'info';
    if (!source.enabled) return 'default';
    if (source.last_sync) return 'success';
    return 'warning';
  };

  const getStatusText = (source: DataSource) => {
    if (source.running) return 'Синхронизация';
    if (!source.enabled) return 'Отключен';
    if (source.last_sync) return 'Активен';
    return 'Ожидает';
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" sx={{ mb: 3 }}>
          Управление источниками данных
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Управление источниками данных
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<SettingsIcon />}
            onClick={() => setSearchConfigDialogOpen(true)}
          >
            Настройки поиска
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setAddDialogOpen(true)}
          >
            Добавить источник
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        {dataSources.map((source) => {
          const sourceKey = `${source.source_type}_${source.source_name}`;
          const isSyncing = syncing[sourceKey] || source.running;
          
          return (
            <Grid item xs={12} md={6} lg={4} key={sourceKey}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="h6">
                        {getSourceTypeIcon(source.source_type)} {source.source_name}
                      </Typography>
                      <Chip
                        label={getStatusText(source)}
                        color={getStatusColor(source)}
                        size="small"
                      />
                    </Box>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={source.enabled}
                          onChange={() => handleToggleSource(source)}
                          size="small"
                        />
                      }
                      label=""
                    />
                  </Box>

                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Тип: {source.source_type}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Документов: {source.documents_count.toLocaleString()}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Последняя синхронизация: {formatLastSync(source.last_sync)}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Следующая синхронизация: {formatNextSync(source.next_sync)}
                  </Typography>

                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={isSyncing ? <PauseIcon /> : <SyncIcon />}
                      onClick={() => handleSyncSource(source.source_type, source.source_name)}
                      disabled={isSyncing || !source.enabled}
                    >
                      {isSyncing ? 'Синхронизация...' : 'Синхронизировать'}
                    </Button>
                    
                    <IconButton
                      size="small"
                      onClick={() => {
                        setSelectedSource(source);
                        setEditDialogOpen(true);
                      }}
                    >
                      <EditIcon />
                    </IconButton>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Диалог настроек поиска */}
      <Dialog
        open={searchConfigDialogOpen}
        onClose={() => setSearchConfigDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Настройки источников для поиска</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Выберите источники данных, которые будут использоваться при поиске.
            Генерация документов всегда использует все доступные источники.
          </Typography>
          
          <Box sx={{ mt: 2 }}>
            {dataSources.map((source) => {
              const sourceId = `${source.source_type}_${source.source_name}`;
              const isEnabled = searchConfig?.enabled_sources.includes(sourceId) || false;
              
              return (
                <FormControlLabel
                  key={sourceId}
                  control={
                    <Switch
                      checked={isEnabled}
                      onChange={(e) => {
                        if (!searchConfig) return;
                        
                        const newEnabledSources = e.target.checked
                          ? [...searchConfig.enabled_sources, sourceId]
                          : searchConfig.enabled_sources.filter(s => s !== sourceId);
                        
                        setSearchConfig({
                          ...searchConfig,
                          enabled_sources: newEnabledSources
                        });
                      }}
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography>
                        {getSourceTypeIcon(source.source_type)} {source.source_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ({source.documents_count} документов)
                      </Typography>
                    </Box>
                  }
                />
              );
            })}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSearchConfigDialogOpen(false)}>
            Отмена
          </Button>
          <Button
            onClick={() => handleUpdateSearchSources(searchConfig?.enabled_sources || [])}
            variant="contained"
          >
            Сохранить
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог добавления источника */}
      <Dialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Добавить источник данных</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <FormControl fullWidth>
              <InputLabel>Тип источника</InputLabel>
              <Select
                value={newSource.source_type}
                label="Тип источника"
                onChange={(e) => setNewSource({ ...newSource, source_type: e.target.value })}
              >
                <MenuItem value="confluence">Confluence</MenuItem>
                <MenuItem value="gitlab">GitLab</MenuItem>
                <MenuItem value="jira">Jira</MenuItem>
                <MenuItem value="local_files">Локальные файлы</MenuItem>
              </Select>
            </FormControl>

            <TextField
              fullWidth
              label="Название источника"
              value={newSource.source_name}
              onChange={(e) => setNewSource({ ...newSource, source_name: e.target.value })}
              placeholder="Например: main_confluence"
            />

            <TextField
              fullWidth
              label="Расписание синхронизации (cron)"
              value={newSource.sync_schedule}
              onChange={(e) => setNewSource({ ...newSource, sync_schedule: e.target.value })}
              placeholder="0 2 * * *"
              helperText="Формат cron: минуты часы дни месяцы дни_недели"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={newSource.incremental}
                  onChange={(e) => setNewSource({ ...newSource, incremental: e.target.checked })}
                />
              }
              label="Инкрементальная синхронизация"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={newSource.enabled}
                  onChange={(e) => setNewSource({ ...newSource, enabled: e.target.checked })}
                />
              }
              label="Включить источник"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>
            Отмена
          </Button>
          <Button
            onClick={handleAddSource}
            variant="contained"
            disabled={!newSource.source_name}
          >
            Добавить
          </Button>
        </DialogActions>
      </Dialog>

      {/* Статистика использования источников */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Использование источников
          </Typography>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            <InfoIcon sx={{ fontSize: 16, mr: 1, verticalAlign: 'middle' }} />
            Семантический поиск использует выбранные вами источники.
            Генерация документации, RFC и архитектуры использует все доступные источники для максимальной полноты контекста.
          </Typography>

          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Источник</TableCell>
                  <TableCell align="right">Документов</TableCell>
                  <TableCell align="center">Поиск</TableCell>
                  <TableCell align="center">Генерация</TableCell>
                  <TableCell align="center">Статус</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {dataSources.map((source) => {
                  const sourceId = `${source.source_type}_${source.source_name}`;
                  const searchEnabled = searchConfig?.enabled_sources.includes(sourceId);
                  
                  return (
                    <TableRow key={sourceId}>
                      <TableCell>
                        {getSourceTypeIcon(source.source_type)} {source.source_name}
                      </TableCell>
                      <TableCell align="right">
                        {source.documents_count.toLocaleString()}
                      </TableCell>
                      <TableCell align="center">
                        {searchEnabled ? '✅' : '❌'}
                      </TableCell>
                      <TableCell align="center">
                        {source.enabled ? '✅' : '❌'}
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={getStatusText(source)}
                          color={getStatusColor(source)}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

export default DataSourcesManagement; 