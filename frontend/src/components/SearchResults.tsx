import React from 'react';
import { MagnifyingGlassIcon, DocumentIcon, LinkIcon } from '@heroicons/react/24/outline';

interface SearchResult {
  id: string;
  title: string;
  content: string;
  source: string;
  score: number;
  url?: string;
}

interface SearchResultsProps {
  results: SearchResult[];
  query?: string;
}

export default function SearchResults({ results, query }: SearchResultsProps) {
  if (!results || results.length === 0) {
    return (
      <div className="text-center py-8">
        <MagnifyingGlassIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
        <p className="text-gray-500">
          {query ? `No results found for "${query}"` : 'Try a different search query'}
        </p>
      </div>
    );
  }

  const highlightText = (text: string, query?: string) => {
    if (!query) return text;
    
    const regex = new RegExp(`(${query})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 px-1 rounded">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getSourceIcon = (source: string) => {
    if (source.includes('jira')) return '🎫';
    if (source.includes('confluence')) return '📄';
    if (source.includes('gitlab')) return '🦊';
    if (source.includes('github')) return '🐙';
    return '📄';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">
          Search Results ({results.length})
        </h3>
        {query && (
          <span className="text-sm text-gray-500">
            for "{query}"
          </span>
        )}
      </div>
      
      <div className="space-y-3">
        {results.map((result, index) => (
          <div
            key={result.id}
            className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-lg">{getSourceIcon(result.source)}</span>
                  <h4 className="text-base font-medium text-gray-900 truncate">
                    {highlightText(result.title, query)}
                  </h4>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(result.score)}`}>
                    {(result.score * 100).toFixed(0)}%
                  </span>
                </div>
                
                <p className="text-sm text-gray-600 mb-3 line-clamp-3">
                  {highlightText(result.content.substring(0, 200), query)}
                  {result.content.length > 200 && '...'}
                </p>
                
                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  <div className="flex items-center space-x-1">
                    <DocumentIcon className="h-4 w-4" />
                    <span>Source: {result.source}</span>
                  </div>
                  
                  {result.url && (
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center space-x-1 text-blue-600 hover:text-blue-800"
                    >
                      <LinkIcon className="h-4 w-4" />
                      <span>View original</span>
                    </a>
                  )}
                  
                  <span>Rank #{index + 1}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {results.length > 5 && (
        <div className="text-center pt-4">
          <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
            Show more results
          </button>
        </div>
      )}
    </div>
  );
} 