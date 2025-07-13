import React, { useState, useEffect } from 'react';
import {
  DocumentTextIcon,
  CodeBracketIcon,
  ServerIcon,
  CloudIcon,
  CogIcon,
  UserGroupIcon,
  PlusIcon,
  EyeIcon,
  ClipboardDocumentIcon,
  ArrowDownTrayIcon,
  PencilIcon,
  TrashIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  StarIcon as StarOutlineIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarSolidIcon } from '@heroicons/react/24/solid';

interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  subcategory: string;
  language: string;
  complexity: 'beginner' | 'intermediate' | 'advanced';
  tags: string[];
  content: string;
  author: string;
  created_at: string;
  updated_at: string;
  downloads: number;
  rating: number;
  is_favorite: boolean;
  is_public: boolean;
  file_count: number;
  estimated_time: string;
}

interface TemplateCategory {
  id: string;
  name: string;
  icon: React.ComponentType<any>;
  description: string;
  count: number;
  subcategories: string[];
}

export default function TemplateLibrary() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [categories, setCategories] = useState<TemplateCategory[]>([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedSubcategory, setSelectedSubcategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterComplexity, setFilterComplexity] = useState('all');
  const [filterLanguage, setFilterLanguage] = useState('all');
  const [sortBy, setSortBy] = useState('popular');
  const [isCreating, setIsCreating] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [loading, setLoading] = useState(true);

  const templateCategories: TemplateCategory[] = [
    {
      id: 'all',
      name: 'All Templates',
      icon: DocumentTextIcon,
      description: 'Browse all available templates',
      count: 0,
      subcategories: []
    },
    {
      id: 'architecture',
      name: 'Architecture',
      icon: ServerIcon,
      description: 'System architecture and design templates',
      count: 0,
      subcategories: ['RFC Documents', 'System Design', 'API Specifications', 'Database Schema']
    },
    {
      id: 'code',
      name: 'Code Templates',
      icon: CodeBracketIcon,
      description: 'Ready-to-use code patterns and structures',
      count: 0,
      subcategories: ['Classes', 'Functions', 'Components', 'Modules', 'Tests']
    },
    {
      id: 'devops',
      name: 'DevOps',
      icon: CloudIcon,
      description: 'Infrastructure and deployment templates',
      count: 0,
      subcategories: ['Docker', 'Kubernetes', 'CI/CD', 'Terraform', 'Ansible']
    },
    {
      id: 'documentation',
      name: 'Documentation',
      icon: DocumentTextIcon,
      description: 'Documentation templates and guides',
      count: 0,
      subcategories: ['README', 'User Guides', 'API Docs', 'Tutorials', 'Changelogs']
    },
    {
      id: 'configuration',
      name: 'Configuration',
      icon: CogIcon,
      description: 'Configuration files and settings',
      count: 0,
      subcategories: ['Environment', 'Build Tools', 'Linting', 'IDE Settings']
    },
    {
      id: 'team',
      name: 'Team Templates',
      icon: UserGroupIcon,
      description: 'Team collaboration and process templates',
      count: 0,
      subcategories: ['Meeting Notes', 'Code Review', 'Project Plans', 'Reports']
    }
  ];

  const complexityLevels = [
    { value: 'all', label: 'All Levels' },
    { value: 'beginner', label: 'Beginner' },
    { value: 'intermediate', label: 'Intermediate' },
    { value: 'advanced', label: 'Advanced' }
  ];

  const languages = [
    { value: 'all', label: 'All Languages' },
    { value: 'python', label: 'Python' },
    { value: 'javascript', label: 'JavaScript' },
    { value: 'typescript', label: 'TypeScript' },
    { value: 'java', label: 'Java' },
    { value: 'cpp', label: 'C++' },
    { value: 'csharp', label: 'C#' },
    { value: 'go', label: 'Go' },
    { value: 'rust', label: 'Rust' },
    { value: 'php', label: 'PHP' },
    { value: 'markdown', label: 'Markdown' },
    { value: 'yaml', label: 'YAML' },
    { value: 'json', label: 'JSON' }
  ];

  const sortOptions = [
    { value: 'popular', label: 'Most Popular' },
    { value: 'recent', label: 'Recently Added' },
    { value: 'updated', label: 'Recently Updated' },
    { value: 'rating', label: 'Highest Rated' },
    { value: 'name', label: 'Name (A-Z)' }
  ];

  useEffect(() => {
    loadTemplates();
    setCategories(templateCategories);
  }, []);

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/templates', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates || []);
      }
    } catch (error) {
      console.error('Failed to load templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredTemplates = templates.filter(template => {
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    const matchesSubcategory = selectedSubcategory === 'all' || template.subcategory === selectedSubcategory;
    const matchesSearch = searchQuery === '' || 
      template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      template.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesComplexity = filterComplexity === 'all' || template.complexity === filterComplexity;
    const matchesLanguage = filterLanguage === 'all' || template.language === filterLanguage;

    return matchesCategory && matchesSubcategory && matchesSearch && matchesComplexity && matchesLanguage;
  }).sort((a, b) => {
    switch (sortBy) {
      case 'popular':
        return b.downloads - a.downloads;
      case 'recent':
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      case 'updated':
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
      case 'rating':
        return b.rating - a.rating;
      case 'name':
        return a.name.localeCompare(b.name);
      default:
        return 0;
    }
  });

  const handleUseTemplate = async (template: Template) => {
    try {
      const response = await fetch(`/api/v1/templates/${template.id}/use`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        
        // Copy to clipboard
        navigator.clipboard.writeText(data.content);
        
        // Update downloads count
        setTemplates(prev => prev.map(t => 
          t.id === template.id ? { ...t, downloads: t.downloads + 1 } : t
        ));

        alert('Template copied to clipboard!');
      }
    } catch (error) {
      console.error('Failed to use template:', error);
    }
  };

  const handleToggleFavorite = async (template: Template) => {
    try {
      const response = await fetch(`/api/v1/templates/${template.id}/favorite`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        setTemplates(prev => prev.map(t => 
          t.id === template.id ? { ...t, is_favorite: !t.is_favorite } : t
        ));
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    }
  };

  const handleDownload = async (template: Template) => {
    try {
      const response = await fetch(`/api/v1/templates/${template.id}/download`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${template.name.replace(/\s+/g, '_')}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        // Update downloads count
        setTemplates(prev => prev.map(t => 
          t.id === template.id ? { ...t, downloads: t.downloads + 1 } : t
        ));
      }
    } catch (error) {
      console.error('Failed to download template:', error);
    }
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'beginner':
        return 'bg-green-100 text-green-800';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800';
      case 'advanced':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const selectedCategoryData = categories.find(cat => cat.id === selectedCategory);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">📋 Template Library</h1>
            <p className="text-gray-600">
              Ready-to-use templates for rapid development and documentation
            </p>
          </div>
          <button
            onClick={() => setIsCreating(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <PlusIcon className="h-5 w-5" />
            <span>Create Template</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          {/* Categories */}
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <h3 className="font-semibold text-gray-900 mb-3">Categories</h3>
            <div className="space-y-2">
              {categories.map((category) => {
                const Icon = category.icon;
                return (
                  <button
                    key={category.id}
                    onClick={() => {
                      setSelectedCategory(category.id);
                      setSelectedSubcategory('all');
                    }}
                    className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                      selectedCategory === category.id
                        ? 'bg-blue-50 text-blue-700 border border-blue-200'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    <div className="flex-1">
                      <div className="font-medium">{category.name}</div>
                      <div className="text-xs text-gray-500">{category.count} templates</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Subcategories */}
          {selectedCategoryData && selectedCategoryData.subcategories.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Subcategories</h3>
              <div className="space-y-1">
                <button
                  onClick={() => setSelectedSubcategory('all')}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                    selectedSubcategory === 'all'
                      ? 'bg-blue-50 text-blue-700'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  All {selectedCategoryData.name}
                </button>
                {selectedCategoryData.subcategories.map((subcategory) => (
                  <button
                    key={subcategory}
                    onClick={() => setSelectedSubcategory(subcategory)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      selectedSubcategory === subcategory
                        ? 'bg-blue-50 text-blue-700'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    {subcategory}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Filters */}
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <h3 className="font-semibold text-gray-900 mb-3">Filters</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Complexity
                </label>
                <select
                  value={filterComplexity}
                  onChange={(e) => setFilterComplexity(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {complexityLevels.map((level) => (
                    <option key={level.value} value={level.value}>
                      {level.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Language
                </label>
                <select
                  value={filterLanguage}
                  onChange={(e) => setFilterLanguage(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {languages.map((lang) => (
                    <option key={lang.value} value={lang.value}>
                      {lang.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {/* Search and Sort */}
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1 relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search templates..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div className="flex items-center space-x-3">
                <FunnelIcon className="h-5 w-5 text-gray-400" />
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {sortOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Templates Grid */}
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin h-8 w-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
              <p className="text-gray-500">Loading templates...</p>
            </div>
          ) : filteredTemplates.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {filteredTemplates.map((template) => (
                <div key={template.id} className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
                  <div className="p-6">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900 mb-1">{template.name}</h3>
                        <p className="text-sm text-gray-600 line-clamp-2">{template.description}</p>
                      </div>
                      <button
                        onClick={() => handleToggleFavorite(template)}
                        className="ml-2 p-1 text-gray-400 hover:text-yellow-500"
                      >
                        {template.is_favorite ? (
                          <StarSolidIcon className="h-5 w-5 text-yellow-500" />
                        ) : (
                          <StarOutlineIcon className="h-5 w-5" />
                        )}
                      </button>
                    </div>

                    {/* Meta Info */}
                    <div className="flex items-center space-x-4 mb-4 text-sm text-gray-500">
                      <span className={`px-2 py-1 rounded-full text-xs ${getComplexityColor(template.complexity)}`}>
                        {template.complexity}
                      </span>
                      <span>{template.language}</span>
                      <span>{template.estimated_time}</span>
                    </div>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-2 mb-4">
                      {template.tags.slice(0, 3).map((tag, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                      {template.tags.length > 3 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-500 rounded text-xs">
                          +{template.tags.length - 3} more
                        </span>
                      )}
                    </div>

                    {/* Stats */}
                    <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                      <div className="flex items-center space-x-4">
                        <span>⭐ {template.rating.toFixed(1)}</span>
                        <span>📥 {template.downloads}</span>
                        <span>📁 {template.file_count} files</span>
                      </div>
                      <span>by {template.author}</span>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleUseTemplate(template)}
                        className="flex-1 flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        <ClipboardDocumentIcon className="h-4 w-4" />
                        <span>Use Template</span>
                      </button>
                      
                      <button
                        onClick={() => {
                          setSelectedTemplate(template);
                          setShowPreview(true);
                        }}
                        className="p-2 text-gray-500 hover:text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                        title="Preview"
                      >
                        <EyeIcon className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => handleDownload(template)}
                        className="p-2 text-gray-500 hover:text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                        title="Download"
                      >
                        <ArrowDownTrayIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <DocumentTextIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No templates found</h3>
              <p className="text-gray-500 mb-4">
                Try adjusting your search criteria or browse different categories.
              </p>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedCategory('all');
                  setSelectedSubcategory('all');
                  setFilterComplexity('all');
                  setFilterLanguage('all');
                }}
                className="px-4 py-2 text-blue-600 hover:text-blue-700"
              >
                Clear all filters
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Template Preview Modal */}
      {showPreview && selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">{selectedTemplate.name}</h2>
                <p className="text-gray-600">{selectedTemplate.description}</p>
              </div>
              <button
                onClick={() => setShowPreview(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto" style={{ maxHeight: 'calc(80vh - 120px)' }}>
              <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm">
                <code>{selectedTemplate.content}</code>
              </pre>
            </div>
            
            <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200">
              <button
                onClick={() => setShowPreview(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Close
              </button>
              <button
                onClick={() => {
                  handleUseTemplate(selectedTemplate);
                  setShowPreview(false);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Use Template
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 