import React, { useState } from 'react';
import { DocumentTextIcon, CpuChipIcon, ShieldCheckIcon, CloudIcon, CogIcon, UserGroupIcon } from '@heroicons/react/24/outline';

interface RFCTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: React.ComponentType<any>;
  sections: string[];
  estimatedTime: string;
  complexity: 'Low' | 'Medium' | 'High';
  template: string;
}

interface RFCTemplatesProps {
  onTemplateSelect: (template: RFCTemplate) => void;
  selectedTemplateId?: string;
}

const rfcTemplates: RFCTemplate[] = [
  {
    id: 'new-feature',
    name: 'New Feature',
    description: 'Template for proposing new product features',
    category: 'Product',
    icon: CpuChipIcon,
    sections: ['Summary', 'Motivation', 'Detailed Design', 'Implementation Plan', 'Testing Strategy'],
    estimatedTime: '30-45 min',
    complexity: 'Medium',
    template: `# RFC: [Feature Name]

## Summary
Brief description of the proposed feature.

## Motivation
Why is this feature needed? What problem does it solve?

## Detailed Design
Technical specification of the feature.

## Implementation Plan
Step-by-step implementation approach.

## Testing Strategy
How will this feature be tested?

## Considerations
- Performance implications
- Security considerations
- Backward compatibility
- Maintenance overhead

## Alternatives Considered
What other approaches were considered and why were they rejected?

## Timeline
Estimated development timeline.`
  },
  {
    id: 'security-enhancement',
    name: 'Security Enhancement',
    description: 'Template for security improvements and hardening',
    category: 'Security',
    icon: ShieldCheckIcon,
    sections: ['Threat Model', 'Security Requirements', 'Implementation', 'Validation', 'Monitoring'],
    estimatedTime: '45-60 min',
    complexity: 'High',
    template: `# RFC: [Security Enhancement Title]

## Summary
Overview of the security enhancement.

## Threat Model
What threats does this enhancement address?

## Security Requirements
Specific security requirements and compliance needs.

## Implementation Details
Technical implementation of security measures.

## Validation & Testing
Security testing and validation procedures.

## Monitoring & Alerting
How will security be monitored post-implementation?

## Risk Assessment
- Risk level: [High/Medium/Low]
- Impact if not implemented
- Implementation risks

## Compliance
Relevant compliance requirements (GDPR, SOC2, etc.).`
  },
  {
    id: 'infrastructure',
    name: 'Infrastructure Change',
    description: 'Template for infrastructure modifications and deployments',
    category: 'Infrastructure',
    icon: CloudIcon,
    sections: ['Architecture', 'Scalability', 'Deployment', 'Monitoring', 'Rollback Plan'],
    estimatedTime: '40-55 min',
    complexity: 'High',
    template: `# RFC: [Infrastructure Change Title]

## Summary
Description of the infrastructure change.

## Current State
Current infrastructure setup and limitations.

## Proposed Architecture
New infrastructure design and components.

## Scalability Considerations
How will this scale with growth?

## Deployment Strategy
Step-by-step deployment plan.

## Monitoring & Observability
Monitoring, logging, and alerting setup.

## Rollback Plan
How to rollback if issues occur.

## Cost Analysis
Infrastructure costs and budget impact.

## Timeline
Implementation phases and timeline.`
  },
  {
    id: 'api-design',
    name: 'API Design',
    description: 'Template for designing new APIs or API changes',
    category: 'API',
    icon: CogIcon,
    sections: ['API Specification', 'Authentication', 'Rate Limiting', 'Documentation', 'Versioning'],
    estimatedTime: '35-50 min',
    complexity: 'Medium',
    template: `# RFC: [API Name] API Design

## Summary
Overview of the API and its purpose.

## API Specification
Detailed API endpoints, methods, and data structures.

## Authentication & Authorization
How will the API handle auth?

## Rate Limiting
Rate limiting strategy and implementation.

## Error Handling
Error response format and status codes.

## Versioning Strategy
How will API versions be managed?

## Documentation
API documentation approach.

## Testing
API testing strategy and tools.

## Performance Considerations
Expected load and performance requirements.`
  },
  {
    id: 'process-improvement',
    name: 'Process Improvement',
    description: 'Template for proposing workflow and process changes',
    category: 'Process',
    icon: UserGroupIcon,
    sections: ['Current Process', 'Proposed Changes', 'Benefits', 'Implementation', 'Success Metrics'],
    estimatedTime: '25-35 min',
    complexity: 'Low',
    template: `# RFC: [Process Improvement Title]

## Summary
Overview of the process improvement proposal.

## Current Process
Description of the current process and its limitations.

## Proposed Changes
Detailed description of proposed improvements.

## Benefits
Expected benefits and improvements.

## Implementation Plan
How will the new process be implemented?

## Training & Communication
How will team members be trained on the new process?

## Success Metrics
How will success be measured?

## Timeline
Implementation timeline and milestones.

## Risks & Mitigation
Potential risks and mitigation strategies.`
  },
  {
    id: 'architecture-decision',
    name: 'Architecture Decision',
    description: 'Template for significant architectural decisions',
    category: 'Architecture',
    icon: DocumentTextIcon,
    sections: ['Context', 'Decision', 'Consequences', 'Alternatives', 'Implementation'],
    estimatedTime: '50-70 min',
    complexity: 'High',
    template: `# RFC: [Architecture Decision Title]

## Summary
Brief summary of the architectural decision.

## Context
What is the current situation and why is this decision needed?

## Decision
What is the architectural decision being made?

## Consequences
What are the positive and negative consequences?

## Alternatives Considered
What other options were considered and why were they rejected?

## Implementation Strategy
How will this decision be implemented?

## Migration Plan
If applicable, how will existing systems be migrated?

## Impact Assessment
- Performance impact
- Security implications
- Maintenance overhead
- Team training needs

## Success Criteria
How will we know if this decision was successful?`
  }
];

export default function RFCTemplates({ onTemplateSelect, selectedTemplateId }: RFCTemplatesProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [searchTerm, setSearchTerm] = useState('');

  const categories = ['All', ...Array.from(new Set(rfcTemplates.map(t => t.category)))];

  const filteredTemplates = rfcTemplates.filter(template => {
    const matchesCategory = selectedCategory === 'All' || template.category === selectedCategory;
    const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'Low': return 'bg-green-100 text-green-800';
      case 'Medium': return 'bg-yellow-100 text-yellow-800';
      case 'High': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">RFC Templates</h2>
        <p className="text-gray-600">
          Choose from pre-built templates to quickly create professional RFC documents.
        </p>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {categories.map(category => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedCategory === category
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTemplates.map(template => {
          const Icon = template.icon;
          const isSelected = selectedTemplateId === template.id;
          
          return (
            <div
              key={template.id}
              className={`border rounded-lg p-6 cursor-pointer transition-all hover:shadow-md ${
                isSelected
                  ? 'border-blue-500 bg-blue-50 shadow-md'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => onTemplateSelect(template)}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${isSelected ? 'bg-blue-100' : 'bg-gray-100'}`}>
                    <Icon className={`h-6 w-6 ${isSelected ? 'text-blue-600' : 'text-gray-600'}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{template.name}</h3>
                    <span className="text-xs text-gray-500">{template.category}</span>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getComplexityColor(template.complexity)}`}>
                  {template.complexity}
                </span>
              </div>

              {/* Description */}
              <p className="text-sm text-gray-600 mb-4">
                {template.description}
              </p>

              {/* Sections */}
              <div className="mb-4">
                <h4 className="text-xs font-medium text-gray-700 mb-2">Includes:</h4>
                <div className="flex flex-wrap gap-1">
                  {template.sections.slice(0, 3).map(section => (
                    <span
                      key={section}
                      className="px-2 py-1 bg-gray-100 text-xs text-gray-600 rounded"
                    >
                      {section}
                    </span>
                  ))}
                  {template.sections.length > 3 && (
                    <span className="px-2 py-1 bg-gray-100 text-xs text-gray-600 rounded">
                      +{template.sections.length - 3} more
                    </span>
                  )}
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>⏱️ {template.estimatedTime}</span>
                <span>{template.sections.length} sections</span>
              </div>

              {/* Selected Indicator */}
              {isSelected && (
                <div className="mt-4 p-2 bg-blue-100 border border-blue-200 rounded text-center">
                  <span className="text-sm font-medium text-blue-700">✓ Selected</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* No Results */}
      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No templates found</h3>
          <p className="text-gray-600">
            Try adjusting your search or filter criteria.
          </p>
        </div>
      )}
    </div>
  );
} 