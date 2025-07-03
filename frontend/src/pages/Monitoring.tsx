import React, { useState, useEffect, useRef } from 'react';
import { ArrowPathIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface SyncTask {
  id: string;
  source: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number;
  total_items?: number;
  processed_items?: number;
  estimated_time_remaining?: number;
  completed_at?: string;
  error_message?: string;
}

interface SyncStatus {
  tasks: SyncTask[];
  overall_status: string;
}

export default function Monitoring() {
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket подключение
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const wsUrl = `ws://localhost:8000/ws?user_id=monitoring_user`;
        wsRef.current = new WebSocket(wsUrl);

        wsRef.current.onopen = () => {
          console.log('WebSocket connected');
          setIsConnected(true);
          setConnectionError(null);

          wsRef.current?.send(JSON.stringify({
            type: 'get_sync_status'
          }));
        };

        wsRef.current.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            handleWebSocketMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        wsRef.current.onclose = () => {
          console.log('WebSocket disconnected');
          setIsConnected(false);
          setTimeout(connectWebSocket, 5000);
        };

        wsRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
          setConnectionError('Connection failed');
          setIsConnected(false);
        };

      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        setConnectionError('Failed to connect');
      }
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'sync_status':
        setSyncStatus(message.data);
        break;
      case 'sync_update':
        setSyncStatus(prev => {
          if (!prev) return prev;
          const updatedTasks = prev.tasks.map(task => 
            task.id === message.data.task_id 
              ? { ...task, ...message.data }
              : task
          );
          return { ...prev, tasks: updatedTasks };
        });
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  };

  const sendPing = () => {
    if (wsRef.current && isConnected) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }));
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅';
      case 'in_progress': return '🔄';
      case 'failed': return '❌';
      case 'pending': return '⏳';
      default: return '❓';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600';
      case 'in_progress': return 'text-blue-600';
      case 'failed': return 'text-red-600';
      case 'pending': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Мониторинг синхронизации</h1>
          <p className="text-gray-600 mt-2">Real-time статус синхронизации</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
            isConnected 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
          
          <button
            onClick={sendPing}
            disabled={!isConnected}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
          >
            Ping
          </button>
        </div>
      </div>

      {connectionError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
            <span className="text-red-700">Connection Error: {connectionError}</span>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Статус синхронизации</h2>
        </div>

        {syncStatus ? (
          <div className="space-y-4">
            {syncStatus.tasks.map((task) => (
              <div key={task.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{getStatusIcon(task.status)}</span>
                    <div>
                      <h3 className="font-semibold text-gray-900 capitalize">
                        {task.source} Sync
                      </h3>
                      <p className={`text-sm ${getStatusColor(task.status)}`}>
                        {task.status.replace('_', ' ')}
                      </p>
                    </div>
                  </div>
                  
                  {task.status === 'in_progress' && (
                    <div className="text-right">
                      <div className="text-sm text-gray-600">
                        {task.processed_items || 0} / {task.total_items || 0} items
                      </div>
                    </div>
                  )}
                </div>

                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      task.status === 'completed' 
                        ? 'bg-green-500' 
                        : task.status === 'failed'
                        ? 'bg-red-500'
                        : 'bg-blue-500'
                    }`}
                    style={{ width: `${task.progress}%` }}
                  ></div>
                </div>

                <div className="flex justify-between items-center mt-2">
                  <span className="text-sm text-gray-600">{task.progress}%</span>
                  {task.completed_at && (
                    <span className="text-sm text-gray-500">
                      Completed: {new Date(task.completed_at).toLocaleTimeString()}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="text-gray-500">Загрузка статуса синхронизации...</div>
          </div>
        )}
      </div>
    </div>
  );
}
