import React, { useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Search, 
  Upload, 
  Code, 
  FileText, 
  Image as ImageIcon,
  Play,
  Download,
  Star,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';

interface MultimodalSearchResult {
  id: string;
  content: string;
  score: number;
  source: string;
  search_type: string;
}

interface CodeReviewResult {
  overall_score: number;
  issues: Array<{
    severity: string;
    type: string;
    description: string;
    suggestion: string;
  }>;
  suggestions: Array<{
    type: string;
    description: string;
    benefit: string;
  }>;
  summary: string;
  review_time: number;
}

interface AdvancedRFCResult {
  rfc_id: string;
  content: string;
  template_used: string;
  sections: Array<{ title: string; description: string }>;
  quality_score: number;
}

const AdvancedAI: React.FC = () => {
  // Multimodal Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<MultimodalSearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Code Review State
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [reviewType, setReviewType] = useState('comprehensive');
  const [reviewResult, setReviewResult] = useState<CodeReviewResult | null>(null);
  const [reviewLoading, setReviewLoading] = useState(false);

  // RFC Generation State
  const [rfcTitle, setRfcTitle] = useState('');
  const [rfcDescription, setRfcDescription] = useState('');
  const [rfcTemplate, setRfcTemplate] = useState('standard');
  const [rfcResult, setRfcResult] = useState<AdvancedRFCResult | null>(null);
  const [rfcLoading, setRfcLoading] = useState(false);

  // Image Upload Handler
  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/v1/ai-advanced/upload-image', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setUploadedImage(result.image_data);
      }
    } catch (error) {
      console.error('Image upload failed:', error);
    }
  };

  // Multimodal Search Handler
  const handleMultimodalSearch = async () => {
    if (!searchQuery.trim()) return;

    setSearchLoading(true);
    try {
      const response = await fetch('/api/v1/ai-advanced/multimodal-search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          query: searchQuery,
          image_data: uploadedImage,
          search_types: uploadedImage ? ['semantic', 'visual'] : ['semantic'],
          limit: 10
        })
      });

      if (response.ok) {
        const results = await response.json();
        setSearchResults(results);
      }
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setSearchLoading(false);
    }
  };

  // Code Review Handler
  const handleCodeReview = async () => {
    if (!code.trim()) return;

    setReviewLoading(true);
    try {
      const response = await fetch('/api/v1/ai-advanced/code-review', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          code,
          language,
          review_type: reviewType
        })
      });

      if (response.ok) {
        const result = await response.json();
        setReviewResult(result);
      }
    } catch (error) {
      console.error('Code review failed:', error);
    } finally {
      setReviewLoading(false);
    }
  };

  // RFC Generation Handler
  const handleRFCGeneration = async () => {
    if (!rfcTitle.trim() || !rfcDescription.trim()) return;

    setRfcLoading(true);
    try {
      const response = await fetch('/api/v1/ai-advanced/rfc-advanced', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          title: rfcTitle,
          description: rfcDescription,
          template_type: rfcTemplate,
          stakeholders: [],
          technical_requirements: {},
          business_context: ''
        })
      });

      if (response.ok) {
        const result = await response.json();
        setRfcResult(result);
      }
    } catch (error) {
      console.error('RFC generation failed:', error);
    } finally {
      setRfcLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="p-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Advanced AI Features</h1>
        <p className="text-gray-600">Multi-modal search, AI code review, and advanced RFC generation</p>
      </div>

      <Tabs defaultValue="search" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="search" className="flex items-center gap-2">
            <Search className="w-4 h-4" />
            Multi-modal Search
          </TabsTrigger>
          <TabsTrigger value="review" className="flex items-center gap-2">
            <Code className="w-4 h-4" />
            Code Review
          </TabsTrigger>
          <TabsTrigger value="rfc" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Advanced RFC
          </TabsTrigger>
        </TabsList>

        {/* Multi-modal Search Tab */}
        <TabsContent value="search" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="w-5 h-5" />
                Multi-modal Search
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4">
                <div className="flex-1">
                  <Input
                    placeholder="Enter your search query..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleMultimodalSearch()}
                  />
                </div>
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <Upload className="w-4 h-4" />
                  Upload Image
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
                <Button 
                  onClick={handleMultimodalSearch}
                  disabled={searchLoading || !searchQuery.trim()}
                  className="flex items-center gap-2"
                >
                  {searchLoading ? (
                    <Clock className="w-4 h-4 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                  Search
                </Button>
              </div>

              {uploadedImage && (
                <Alert>
                  <ImageIcon className="w-4 h-4" />
                  <AlertDescription>
                    Image uploaded successfully. Visual search will be included in results.
                  </AlertDescription>
                </Alert>
              )}

              {searchResults.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Search Results</h3>
                  {searchResults.map((result) => (
                    <Card key={result.id} className="border-l-4 border-l-blue-500">
                      <CardContent className="pt-4">
                        <div className="flex justify-between items-start mb-2">
                          <Badge variant="outline">{result.search_type}</Badge>
                          <span className="text-sm font-medium text-blue-600">
                            Score: {(result.score * 100).toFixed(1)}%
                          </span>
                        </div>
                        <p className="text-gray-700 mb-2">{result.content}</p>
                        <p className="text-sm text-gray-500">Source: {result.source}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Code Review Tab */}
        <TabsContent value="review" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="w-5 h-5" />
                AI Code Review
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Language</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full p-2 border rounded-md"
                  >
                    <option value="python">Python</option>
                    <option value="javascript">JavaScript</option>
                    <option value="typescript">TypeScript</option>
                    <option value="java">Java</option>
                    <option value="cpp">C++</option>
                    <option value="go">Go</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Review Type</label>
                  <select
                    value={reviewType}
                    onChange={(e) => setReviewType(e.target.value)}
                    className="w-full p-2 border rounded-md"
                  >
                    <option value="quick">Quick Review</option>
                    <option value="comprehensive">Comprehensive</option>
                    <option value="security">Security Focused</option>
                    <option value="performance">Performance</option>
                    <option value="style">Style & Best Practices</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Code</label>
                <Textarea
                  placeholder="Paste your code here..."
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className="min-h-40 font-mono text-sm"
                />
              </div>

              <Button 
                onClick={handleCodeReview}
                disabled={reviewLoading || !code.trim()}
                className="w-full flex items-center justify-center gap-2"
              >
                {reviewLoading ? (
                  <Clock className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                Review Code
              </Button>

              {reviewResult && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">Review Results</h3>
                    <div className="flex items-center gap-2">
                      <Star className="w-5 h-5 text-yellow-500" />
                      <span className={`text-xl font-bold ${getScoreColor(reviewResult.overall_score)}`}>
                        {reviewResult.overall_score.toFixed(1)}/10
                      </span>
                    </div>
                  </div>

                  <Alert>
                    <AlertCircle className="w-4 h-4" />
                    <AlertDescription>{reviewResult.summary}</AlertDescription>
                  </Alert>

                  {reviewResult.issues.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-red-600">Issues Found</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {reviewResult.issues.map((issue, index) => (
                          <div key={index} className="border-l-4 border-l-red-500 pl-4">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge className={getSeverityColor(issue.severity)}>
                                {issue.severity}
                              </Badge>
                              <span className="text-sm text-gray-600">{issue.type}</span>
                            </div>
                            <p className="text-sm font-medium">{issue.description}</p>
                            <p className="text-sm text-gray-600 mt-1">{issue.suggestion}</p>
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  )}

                  {reviewResult.suggestions.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-blue-600">Suggestions</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {reviewResult.suggestions.map((suggestion, index) => (
                          <div key={index} className="border-l-4 border-l-blue-500 pl-4">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant="outline">{suggestion.type}</Badge>
                            </div>
                            <p className="text-sm font-medium">{suggestion.description}</p>
                            <p className="text-sm text-green-600 mt-1">✓ {suggestion.benefit}</p>
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* RFC Generation Tab */}
        <TabsContent value="rfc" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Advanced RFC Generation
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">RFC Title</label>
                <Input
                  placeholder="Enter RFC title..."
                  value={rfcTitle}
                  onChange={(e) => setRfcTitle(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Template Type</label>
                <select
                  value={rfcTemplate}
                  onChange={(e) => setRfcTemplate(e.target.value)}
                  className="w-full p-2 border rounded-md"
                >
                  <option value="standard">Standard RFC</option>
                  <option value="technical">Technical RFC</option>
                  <option value="business">Business RFC</option>
                  <option value="security">Security RFC</option>
                  <option value="architecture">Architecture RFC</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <Textarea
                  placeholder="Describe your RFC proposal..."
                  value={rfcDescription}
                  onChange={(e) => setRfcDescription(e.target.value)}
                  className="min-h-32"
                />
              </div>

              <Button 
                onClick={handleRFCGeneration}
                disabled={rfcLoading || !rfcTitle.trim() || !rfcDescription.trim()}
                className="w-full flex items-center justify-center gap-2"
              >
                {rfcLoading ? (
                  <Clock className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                Generate RFC
              </Button>

              {rfcResult && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">Generated RFC</h3>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm">
                        <Download className="w-4 h-4" />
                        Download
                      </Button>
                      <div className="flex items-center gap-1">
                        <CheckCircle className="w-5 h-5 text-green-500" />
                        <span className="text-sm font-medium">
                          Quality: {rfcResult.quality_score.toFixed(1)}/10
                        </span>
                      </div>
                    </div>
                  </div>

                  <Card>
                    <CardContent className="pt-4">
                      <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-4 rounded-md overflow-auto max-h-96">
                        {rfcResult.content}
                      </pre>
                    </CardContent>
                  </Card>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdvancedAI; 