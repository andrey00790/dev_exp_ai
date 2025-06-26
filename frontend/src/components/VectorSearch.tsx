import React, { useState, useEffect } from 'react';
import { Search, FileText, Database, Zap, Filter, Download } from 'lucide-react';

interface SearchResult {
  id: string;
  score: number;
  doc_id: string;
  title: string;
  text: string;
  collection_type: string;
  metadata: {
    author?: string;
    source?: string;
    tags?: string[];
    content_type?: string;
    chunk_index?: number;
    total_chunks?: number;
  };
}

interface SearchResponse {
  results: SearchResult[];
  total_results: number;
  query: string;
  search_time_ms: number;
  collections_searched: string[];
}

interface CollectionStats {
  [key: string]: {
    exists: boolean;
    type: string;
    status: string;
  };
}

const VectorSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchStats, setSearchStats] = useState<Partial<SearchResponse>>({});
  const [selectedCollections, setSelectedCollections] = useState<string[]>([]);
  const [availableCollections, setAvailableCollections] = useState<string[]>([]);
  const [collectionStats, setCollectionStats] = useState<CollectionStats>({});
  const [maxResults, setMaxResults] = useState(10);
  const [hybridSearch, setHybridSearch] = useState(true);
  const [includeSnippets, setIncludeSnippets] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCollectionStats();
  }, []);

  const loadCollectionStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/vector-search/collections', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setCollectionStats(data.collections || {});
        const collections = Object.keys(data.collections || {})
          .filter(key => data.collections[key].exists)
          .map(key => data.collections[key].type);
        setAvailableCollections(collections);
      }
    } catch (err) {
      console.error('Failed to load collection stats:', err);
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const searchRequest = {
        query: query.trim(),
        collections: selectedCollections.length > 0 ? selectedCollections : undefined,
        limit: maxResults,
        include_snippets: includeSnippets,
        hybrid_search: hybridSearch,
      };

      const response = await fetch('/api/v1/vector-search/search', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(searchRequest),
      });

      if (response.ok) {
        const data: SearchResponse = await response.json();
        setResults(data.results);
        setSearchStats({
          total_results: data.total_results,
          search_time_ms: data.search_time_ms,
          collections_searched: data.collections_searched,
        });
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Search failed');
      }
    } catch (err) {
      setError('Network error occurred');
      console.error('Search error:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  const toggleCollection = (collection: string) => {
    setSelectedCollections(prev => 
      prev.includes(collection)
        ? prev.filter(c => c !== collection)
        : [...prev, collection]
    );
  };

  const exportResults = () => {
    const exportData = {
      query: query,
      search_stats: searchStats,
      results: results.map(r => ({
        title: r.title,
        score: r.score,
        content: r.text,
        source: r.metadata.source,
        collection: r.collection_type,
      })),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `vector_search_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 0.8) return 'High';
    if (score >= 0.6) return 'Medium';
    return 'Low';
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          <Database className="inline-block w-8 h-8 mr-2 text-blue-600" />
          Vector Search
        </h1>
        <p className="text-gray-600">
          Semantic search across your document collections using AI embeddings
        </p>
      </div>

      {/* Collection Stats */}
      <div className="bg-white rounded-lg shadow-md p-4 border">
        <h3 className="text-lg font-semibold mb-3 flex items-center">
          <Database className="w-5 h-5 mr-2" />
          Collection Status
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {Object.entries(collectionStats).map(([key, stats]) => (
            <div key={key} className="text-center">
              <div className={`w-3 h-3 rounded-full mx-auto mb-1 ${
                stats.exists ? 'bg-green-500' : 'bg-gray-300'
              }`} />
              <div className="text-xs font-medium">{stats.type}</div>
              <div className="text-xs text-gray-500">
                {stats.exists ? 'Active' : 'Empty'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Search Interface */}
      <div className="bg-white rounded-lg shadow-md p-6 border">
        <div className="space-y-4">
          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter your search query... (e.g., 'machine learning algorithms for semantic search')"
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={3}
            />
          </div>

          {/* Search Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Collection Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Filter className="inline w-4 h-4 mr-1" />
                Collections
              </label>
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {availableCollections.map(collection => (
                  <label key={collection} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedCollections.includes(collection)}
                      onChange={() => toggleCollection(collection)}
                      className="mr-2"
                    />
                    <span className="text-sm">{collection}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Max Results */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Results
              </label>
              <select
                value={maxResults}
                onChange={(e) => setMaxResults(Number(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </div>

            {/* Search Options */}
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={hybridSearch}
                  onChange={(e) => setHybridSearch(e.target.checked)}
                  className="mr-2"
                />
                <span className="text-sm">Hybrid Search</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeSnippets}
                  onChange={(e) => setIncludeSnippets(e.target.checked)}
                  className="mr-2"
                />
                <span className="text-sm">Include Snippets</span>
              </label>
            </div>

            {/* Search Button */}
            <div className="flex items-end">
              <button
                onClick={handleSearch}
                disabled={isSearching || !query.trim()}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium flex items-center justify-center"
              >
                {isSearching ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                ) : (
                  <>
                    <Zap className="w-4 h-4 mr-2" />
                    Search
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-red-800">{error}</div>
        </div>
      )}

      {/* Search Stats */}
      {searchStats.total_results !== undefined && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-6 text-sm text-blue-800">
              <span>
                <strong>{searchStats.total_results}</strong> results found
              </span>
              <span>
                Search time: <strong>{searchStats.search_time_ms?.toFixed(1)}ms</strong>
              </span>
              <span>
                Collections: <strong>{searchStats.collections_searched?.join(', ')}</strong>
              </span>
            </div>
            {results.length > 0 && (
              <button
                onClick={exportResults}
                className="flex items-center gap-2 text-blue-600 hover:text-blue-800"
              >
                <Download className="w-4 h-4" />
                Export Results
              </button>
            )}
          </div>
        </div>
      )}

      {/* Search Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-900">Search Results</h2>
          {results.map((result, index) => (
            <div key={result.id} className="bg-white rounded-lg shadow-md border p-6">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {result.title}
                  </h3>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span className="flex items-center">
                      <FileText className="w-4 h-4 mr-1" />
                      {result.collection_type}
                    </span>
                    {result.metadata.author && (
                      <span>by {result.metadata.author}</span>
                    )}
                    {result.metadata.chunk_index !== undefined && (
                      <span>
                        Chunk {result.metadata.chunk_index + 1} of {result.metadata.total_chunks}
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-lg font-bold ${getScoreColor(result.score)}`}>
                    {(result.score * 100).toFixed(1)}%
                  </div>
                  <div className={`text-xs ${getScoreColor(result.score)}`}>
                    {getScoreLabel(result.score)} Match
                  </div>
                </div>
              </div>

              <div className="text-gray-700 mb-3 leading-relaxed">
                {result.text.length > 300 
                  ? `${result.text.substring(0, 300)}...`
                  : result.text
                }
              </div>

              {result.metadata.tags && result.metadata.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-3">
                  {result.metadata.tags.map(tag => (
                    <span
                      key={tag}
                      className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>Document ID: {result.doc_id}</span>
                {result.metadata.source && (
                  <span>Source: {result.metadata.source}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* No Results */}
      {searchStats.total_results === 0 && query && !isSearching && (
        <div className="text-center py-12">
          <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
          <p className="text-gray-600 mb-4">
            Try adjusting your search query or selecting different collections.
          </p>
          <button
            onClick={() => setQuery('')}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            Clear search
          </button>
        </div>
      )}
    </div>
  );
};

export default VectorSearch; 