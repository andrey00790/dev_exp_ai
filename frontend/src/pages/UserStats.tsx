import React, { useState, useEffect } from 'react';
import {
  ChartBarIcon,
  TrophyIcon,
  ClockIcon,
  FireIcon,
  StarIcon,
  CodeBracketIcon,
  DocumentTextIcon,
  MagnifyingGlassIcon,
  CpuChipIcon,
  CalendarDaysIcon,
  UsersIcon,
  BoltIcon,
  CheckCircleIcon,
  ArrowTrendingUpIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline';
import { Line, Bar, Doughnut, Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  RadialLinearScale
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  RadialLinearScale
);

interface UserStats {
  user_id: string;
  username: string;
  created_at: string;
  user_level: string;
  total_score: number;
  messages_sent: number;
  commands_used: number;
  total_time: number;
  search_count: number;
  generation_count: number;
  analysis_count: number;
  review_count: number;
  optimization_count: number;
  documentation_count: number;
  templates_used: number;
  user_rank: number;
  total_users: number;
  streak_days: number;
  achievements: Achievement[];
  activity_chart: ActivityData[];
  skill_scores: SkillScores;
}

interface Achievement {
  id: string;
  name: string;
  description: string;
  emoji: string;
  category: string;
  unlocked_at: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
  progress?: number;
  max_progress?: number;
}

interface ActivityData {
  date: string;
  messages: number;
  commands: number;
  time_spent: number;
}

interface SkillScores {
  search_proficiency: number;
  coding_skills: number;
  documentation: number;
  architecture: number;
  ai_usage: number;
  collaboration: number;
}

export default function UserStats() {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [timeRange, setTimeRange] = useState('30d');
  const [achievementFilter, setAchievementFilter] = useState('all');

  const tabs = [
    { id: 'overview', label: 'Overview', icon: ChartBarIcon },
    { id: 'activity', label: 'Activity', icon: ClockIcon },
    { id: 'achievements', label: 'Achievements', icon: TrophyIcon },
    { id: 'skills', label: 'Skills', icon: StarIcon },
    { id: 'leaderboard', label: 'Leaderboard', icon: UsersIcon }
  ];

  const timeRanges = [
    { value: '7d', label: 'Last 7 days' },
    { value: '30d', label: 'Last 30 days' },
    { value: '90d', label: 'Last 3 months' },
    { value: '1y', label: 'Last year' },
    { value: 'all', label: 'All time' }
  ];

  const achievementCategories = [
    { value: 'all', label: 'All Achievements' },
    { value: 'usage', label: 'Usage Milestones' },
    { value: 'skill', label: 'Skill Development' },
    { value: 'social', label: 'Social' },
    { value: 'special', label: 'Special Events' }
  ];

  useEffect(() => {
    loadStats();
  }, [timeRange]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/users/stats?range=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to load user stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const exportStats = async (format: 'pdf' | 'csv' | 'json') => {
    try {
      const response = await fetch(`/api/v1/users/stats/export?format=${format}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `user-stats.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Failed to export stats:', error);
    }
  };

  const getLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'novice':
        return 'bg-gray-100 text-gray-800';
      case 'beginner':
        return 'bg-green-100 text-green-800';
      case 'intermediate':
        return 'bg-blue-100 text-blue-800';
      case 'advanced':
        return 'bg-purple-100 text-purple-800';
      case 'expert':
        return 'bg-yellow-100 text-yellow-800';
      case 'master':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case 'common':
        return 'border-gray-300 bg-gray-50';
      case 'rare':
        return 'border-blue-300 bg-blue-50';
      case 'epic':
        return 'border-purple-300 bg-purple-50';
      case 'legendary':
        return 'border-yellow-300 bg-yellow-50';
      default:
        return 'border-gray-300 bg-gray-50';
    }
  };

  const activityChartData = stats?.activity_chart ? {
    labels: stats.activity_chart.map(d => new Date(d.date).toLocaleDateString()),
    datasets: [
      {
        label: 'Messages',
        data: stats.activity_chart.map(d => d.messages),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4
      },
      {
        label: 'Commands',
        data: stats.activity_chart.map(d => d.commands),
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4
      }
    ]
  } : null;

  const usageChartData = stats ? {
    labels: ['Search', 'Generation', 'Analysis', 'Review', 'Optimization', 'Documentation'],
    datasets: [{
      data: [
        stats.search_count,
        stats.generation_count,
        stats.analysis_count,
        stats.review_count,
        stats.optimization_count,
        stats.documentation_count
      ],
      backgroundColor: [
        '#3B82F6',
        '#10B981',
        '#F59E0B',
        '#EF4444',
        '#8B5CF6',
        '#06B6D4'
      ]
    }]
  } : null;

  const skillRadarData = stats?.skill_scores ? {
    labels: [
      'Search Proficiency',
      'Coding Skills',
      'Documentation',
      'Architecture',
      'AI Usage',
      'Collaboration'
    ],
    datasets: [{
      label: 'Your Skills',
      data: [
        stats.skill_scores.search_proficiency,
        stats.skill_scores.coding_skills,
        stats.skill_scores.documentation,
        stats.skill_scores.architecture,
        stats.skill_scores.ai_usage,
        stats.skill_scores.collaboration
      ],
      backgroundColor: 'rgba(59, 130, 246, 0.2)',
      borderColor: 'rgb(59, 130, 246)',
      pointBackgroundColor: 'rgb(59, 130, 246)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgb(59, 130, 246)'
    }]
  } : null;

  const filteredAchievements = stats?.achievements.filter(achievement => 
    achievementFilter === 'all' || achievement.category === achievementFilter
  ) || [];

  if (loading) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="text-center py-12">
          <div className="animate-spin h-8 w-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-500">Loading your statistics...</p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <div className="text-center py-12">
          <ChartBarIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Statistics Available</h3>
          <p className="text-gray-500">Start using the AI Assistant to see your statistics here.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">📊 Your Statistics</h1>
            <p className="text-gray-600">
              Track your progress and achievements with the AI Assistant
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {timeRanges.map((range) => (
                <option key={range.value} value={range.value}>
                  {range.label}
                </option>
              ))}
            </select>
            <button
              onClick={() => exportStats('pdf')}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <ArrowDownTrayIcon className="h-4 w-4" />
              <span>Export</span>
            </button>
          </div>
        </div>
      </div>

      {/* Quick Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg">
              <TrophyIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">{stats.total_score}</div>
              <div className="text-sm text-gray-500">Total Score</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-lg">
              <UsersIcon className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">#{stats.user_rank}</div>
              <div className="text-sm text-gray-500">Rank of {stats.total_users}</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <FireIcon className="h-6 w-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <div className="text-2xl font-bold text-gray-900">{stats.streak_days}</div>
              <div className="text-sm text-gray-500">Day Streak</div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center">
            <div className="p-3 bg-purple-100 rounded-lg">
              <StarIcon className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <div className={`inline-flex px-2 py-1 rounded-full text-sm font-medium ${getLevelColor(stats.user_level)}`}>
                {stats.user_level}
              </div>
              <div className="text-sm text-gray-500 mt-1">Current Level</div>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-5 w-5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Usage Overview */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Feature Usage</h3>
            {usageChartData && (
              <div className="h-64">
                <Doughnut 
                  data={usageChartData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'bottom'
                      }
                    }
                  }}
                />
              </div>
            )}
          </div>

          {/* Activity Summary */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Activity Summary</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <DocumentTextIcon className="h-5 w-5 text-blue-500" />
                  <span className="text-gray-700">Messages Sent</span>
                </div>
                <span className="font-semibold text-gray-900">{stats.messages_sent}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CodeBracketIcon className="h-5 w-5 text-green-500" />
                  <span className="text-gray-700">Commands Used</span>
                </div>
                <span className="font-semibold text-gray-900">{stats.commands_used}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <ClockIcon className="h-5 w-5 text-yellow-500" />
                  <span className="text-gray-700">Time Spent</span>
                </div>
                <span className="font-semibold text-gray-900">{Math.round(stats.total_time / 60)} hours</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <MagnifyingGlassIcon className="h-5 w-5 text-purple-500" />
                  <span className="text-gray-700">Searches</span>
                </div>
                <span className="font-semibold text-gray-900">{stats.search_count}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CpuChipIcon className="h-5 w-5 text-red-500" />
                  <span className="text-gray-700">AI Analyses</span>
                </div>
                <span className="font-semibold text-gray-900">{stats.analysis_count}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'activity' && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Activity Over Time</h3>
          {activityChartData && (
            <div className="h-80">
              <Line 
                data={activityChartData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    y: {
                      beginAtZero: true
                    }
                  },
                  plugins: {
                    legend: {
                      position: 'top'
                    }
                  }
                }}
              />
            </div>
          )}
        </div>
      )}

      {activeTab === 'achievements' && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">
              Achievements ({filteredAchievements.length})
            </h3>
            <select
              value={achievementFilter}
              onChange={(e) => setAchievementFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {achievementCategories.map((category) => (
                <option key={category.value} value={category.value}>
                  {category.label}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAchievements.map((achievement) => (
              <div 
                key={achievement.id} 
                className={`rounded-lg border-2 p-6 ${getRarityColor(achievement.rarity)}`}
              >
                <div className="flex items-start space-x-3">
                  <span className="text-3xl">{achievement.emoji}</span>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="font-semibold text-gray-900">{achievement.name}</h4>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${
                        achievement.rarity === 'legendary' ? 'bg-yellow-100 text-yellow-800' :
                        achievement.rarity === 'epic' ? 'bg-purple-100 text-purple-800' :
                        achievement.rarity === 'rare' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {achievement.rarity}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{achievement.description}</p>
                    <div className="text-xs text-gray-500">
                      Unlocked {new Date(achievement.unlocked_at).toLocaleDateString()}
                    </div>
                    {achievement.progress !== undefined && achievement.max_progress && (
                      <div className="mt-3">
                        <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                          <span>Progress</span>
                          <span>{achievement.progress}/{achievement.max_progress}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${(achievement.progress / achievement.max_progress) * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'skills' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Skill Radar</h3>
            {skillRadarData && (
              <div className="h-80">
                <Radar 
                  data={skillRadarData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                      r: {
                        angleLines: {
                          display: false
                        },
                        suggestedMin: 0,
                        suggestedMax: 10
                      }
                    }
                  }}
                />
              </div>
            )}
          </div>

          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Skill Breakdown</h3>
            <div className="space-y-4">
              {Object.entries(stats.skill_scores).map(([skill, score]) => (
                <div key={skill}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700 capitalize">
                      {skill.replace('_', ' ')}
                    </span>
                    <span className="text-sm font-semibold text-gray-900">{score.toFixed(1)}/10</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        score >= 8 ? 'bg-green-500' : 
                        score >= 6 ? 'bg-yellow-500' : 
                        score >= 4 ? 'bg-blue-500' : 
                        'bg-red-500'
                      }`}
                      style={{ width: `${score * 10}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'leaderboard' && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Leaderboard Position</h3>
          <div className="text-center py-8">
            <div className="text-6xl font-bold text-blue-600 mb-2">#{stats.user_rank}</div>
            <div className="text-lg text-gray-600 mb-4">out of {stats.total_users} users</div>
            <div className="text-sm text-gray-500">
              You're in the top {Math.round((stats.user_rank / stats.total_users) * 100)}% of users!
            </div>
            <div className="mt-6 w-64 mx-auto bg-gray-200 rounded-full h-4">
              <div 
                className="bg-gradient-to-r from-blue-500 to-purple-600 h-4 rounded-full"
                style={{ width: `${100 - (stats.user_rank / stats.total_users) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 