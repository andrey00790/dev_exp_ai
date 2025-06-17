import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  HomeIcon, 
  MagnifyingGlassIcon, 
  DocumentTextIcon, 
  CodeBracketIcon, 
  Cog6ToothIcon,
  Bars3Icon,
  XMarkIcon,
  PlusIcon,
  ChatBubbleLeftIcon,
  BeakerIcon,
  ChatBubbleLeftRightIcon,
  SparklesIcon, 
  ChartBarIcon,
  ArrowRightOnRectangleIcon
} from '@heroicons/react/24/outline';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon },
    { name: 'Chat', href: '/chat', icon: ChatBubbleLeftIcon },
    { name: 'Search', href: '/search', icon: MagnifyingGlassIcon },
    { name: 'Generate RFC', href: '/generate', icon: DocumentTextIcon },
    { name: 'Code Docs', href: '/code-docs', icon: CodeBracketIcon },
    { name: 'API Test', href: '/api-test', icon: BeakerIcon },
    { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
    { name: 'Monitoring', href: '/monitoring', icon: ChartBarIcon },
    { name: 'Enhanced RFC', href: '/enhanced-rfc', icon: SparklesIcon },
  ];

  // Mock chat history for sidebar
  const chatHistory = [
    { id: 1, title: 'Search for API documentation', type: 'search', timestamp: '2 hours ago' },
    { id: 2, title: 'Generate RFC for user auth', type: 'generate', timestamp: '1 day ago' },
    { id: 3, title: 'Document React components', type: 'docs', timestamp: '2 days ago' },
  ];

  const handleLogout = () => {
    logout();
  };

  const getUserInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getBudgetStatusColor = (usage: number, limit: number) => {
    const percentage = (usage / limit) * 100;
    if (percentage >= 95) return 'text-red-400';
    if (percentage >= 80) return 'text-yellow-400';
    return 'text-green-400';
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        </div>
      )}

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between h-16 px-4 bg-gray-800">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-xl font-bold text-white">AI Assistant</h1>
              </div>
            </div>
            <button
              className="lg:hidden text-gray-400 hover:text-white"
              onClick={() => setSidebarOpen(false)}
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* New Chat Button */}
          <div className="p-4">
            <Link 
              to="/chat"
              className="w-full flex items-center justify-center px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              New Chat
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  <Icon className="h-5 w-5 mr-3" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Chat History */}
          <div className="flex-1 px-4 mt-8">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
              Recent Chats
            </h3>
            <div className="space-y-1">
              {chatHistory.map((chat) => (
                <Link
                  key={chat.id}
                  to="/chat"
                  className="flex items-start p-2 text-sm text-gray-300 hover:bg-gray-700 rounded-lg cursor-pointer transition-colors"
                >
                  <ChatBubbleLeftIcon className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="truncate">{chat.title}</p>
                    <p className="text-xs text-gray-500 mt-1">{chat.timestamp}</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* User Profile */}
          <div className="p-4 border-t border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center flex-1 min-w-0">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 bg-indigo-600 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-white">
                      {user ? getUserInitials(user.name) : 'U'}
                    </span>
                  </div>
                </div>
                <div className="ml-3 flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">
                    {user ? user.name : 'User'}
                  </p>
                  <p className="text-xs text-gray-400 truncate">
                    {user ? user.email : 'user@example.com'}
                  </p>
                  {user && (
                    <p className={`text-xs ${getBudgetStatusColor(user.current_usage, user.budget_limit)}`}>
                      ${user.current_usage.toFixed(2)} / ${user.budget_limit.toFixed(2)}
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={handleLogout}
                className="ml-2 p-1 text-gray-400 hover:text-white transition-colors"
                title="Logout"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <div className="bg-white shadow-sm border-b border-gray-200 lg:hidden">
          <div className="flex items-center justify-between h-16 px-4">
            <button
              className="text-gray-500 hover:text-gray-700"
              onClick={() => setSidebarOpen(true)}
            >
              <Bars3Icon className="h-6 w-6" />
            </button>
            <h1 className="text-lg font-semibold text-gray-900">AI Assistant</h1>
            <div className="w-6" /> {/* Spacer */}
          </div>
        </div>

        {/* Main content area */}
        <main className="flex-1 overflow-hidden bg-white">
          {children}
        </main>
      </div>
    </div>
  );
}
