import React, { useState } from 'react';
import { ArrowDownTrayIcon, DocumentTextIcon, CodeBracketIcon, DocumentIcon } from '@heroicons/react/24/outline';

interface ExportFormat {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<any>;
  extension: string;
  mimeType: string;
}

interface RFCExportProps {
  rfcContent: string;
  rfcTitle: string;
  onExport?: (format: string) => void;
}

const exportFormats: ExportFormat[] = [
  {
    id: 'markdown',
    name: 'Markdown',
    description: 'Standard Markdown format (.md)',
    icon: DocumentTextIcon,
    extension: 'md',
    mimeType: 'text/markdown'
  },
  {
    id: 'html',
    name: 'HTML',
    description: 'Web-ready HTML format (.html)',
    icon: CodeBracketIcon,
    extension: 'html',
    mimeType: 'text/html'
  },
  {
    id: 'txt',
    name: 'Plain Text',
    description: 'Simple text format (.txt)',
    icon: DocumentIcon,
    extension: 'txt',
    mimeType: 'text/plain'
  },
  {
    id: 'json',
    name: 'JSON',
    description: 'Structured JSON format (.json)',
    icon: CodeBracketIcon,
    extension: 'json',
    mimeType: 'application/json'
  }
];

export default function RFCExport({ rfcContent, rfcTitle, onExport }: RFCExportProps) {
  const [isExporting, setIsExporting] = useState<string | null>(null);

  const convertToHtml = (markdown: string): string => {
    // Simple markdown to HTML conversion
    let html = markdown
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^\* (.*$)/gim, '<li>$1</li>')
      .replace(/^\- (.*$)/gim, '<li>$1</li>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');

    // Wrap lists
    html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');

    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${rfcTitle}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }
        h1 { color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
        h2 { color: #374151; margin-top: 30px; }
        h3 { color: #4b5563; }
        code { background: #f3f4f6; padding: 2px 4px; border-radius: 3px; font-family: 'Monaco', 'Consolas', monospace; }
        ul { padding-left: 20px; }
        li { margin: 5px 0; }
    </style>
</head>
<body>
    ${html}
</body>
</html>`;
  };

  const convertToJson = (markdown: string): string => {
    const sections = markdown.split(/^## /gm).filter(Boolean);
    const rfcData = {
      title: rfcTitle,
      generated_at: new Date().toISOString(),
      format: 'RFC',
      sections: sections.map((section, index) => {
        if (index === 0) {
          // First section might be the title
          const lines = section.split('\n');
          return {
            title: lines[0].replace(/^# /, ''),
            content: lines.slice(1).join('\n').trim()
          };
        } else {
          const lines = section.split('\n');
          return {
            title: lines[0].trim(),
            content: lines.slice(1).join('\n').trim()
          };
        }
      }),
      metadata: {
        word_count: markdown.split(/\s+/).length,
        character_count: markdown.length,
        sections_count: sections.length
      }
    };
    return JSON.stringify(rfcData, null, 2);
  };

  const convertToPlainText = (markdown: string): string => {
    // Remove markdown formatting
    return markdown
      .replace(/^#{1,6} /gm, '')
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/`(.*?)`/g, '$1')
      .replace(/^\* /gm, '• ')
      .replace(/^\- /gm, '• ');
  };

  const downloadFile = async (format: ExportFormat) => {
    setIsExporting(format.id);
    
    try {
      let content = rfcContent;
      let filename = `${rfcTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.${format.extension}`;

      switch (format.id) {
        case 'html':
          content = convertToHtml(rfcContent);
          break;
        case 'json':
          content = convertToJson(rfcContent);
          break;
        case 'txt':
          content = convertToPlainText(rfcContent);
          break;
        case 'markdown':
        default:
          // Keep original markdown content
          break;
      }

      // Create and download file
      const blob = new Blob([content], { type: format.mimeType });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      if (onExport) {
        onExport(format.id);
      }
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(null);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(rfcContent);
      // You might want to show a toast notification here
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center space-x-3 mb-6">
        <ArrowDownTrayIcon className="h-6 w-6 text-blue-600" />
        <h3 className="text-lg font-semibold text-gray-900">Export RFC</h3>
      </div>

      <p className="text-gray-600 mb-6">
        Download your RFC document in various formats for sharing and documentation.
      </p>

      {/* Export Formats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {exportFormats.map(format => {
          const Icon = format.icon;
          const isCurrentlyExporting = isExporting === format.id;
          
          return (
            <button
              key={format.id}
              onClick={() => downloadFile(format)}
              disabled={isCurrentlyExporting}
              className="flex items-center space-x-4 p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <div className="p-2 bg-gray-100 rounded-lg">
                <Icon className="h-6 w-6 text-gray-600" />
              </div>
              <div className="flex-1 text-left">
                <h4 className="font-medium text-gray-900">{format.name}</h4>
                <p className="text-sm text-gray-600">{format.description}</p>
              </div>
              {isCurrentlyExporting ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />
              ) : (
                <ArrowDownTrayIcon className="h-5 w-5 text-gray-400" />
              )}
            </button>
          );
        })}
      </div>

      {/* Additional Actions */}
      <div className="border-t pt-6">
        <h4 className="font-medium text-gray-900 mb-4">Additional Actions</h4>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={copyToClipboard}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <DocumentTextIcon className="h-4 w-4" />
            <span>Copy to Clipboard</span>
          </button>
          
          <button
            onClick={() => window.print()}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <DocumentIcon className="h-4 w-4" />
            <span>Print</span>
          </button>
        </div>
      </div>

      {/* File Info */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <h4 className="font-medium text-gray-900 mb-2">Document Information</h4>
        <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
          <div>
            <span className="font-medium">Title:</span> {rfcTitle}
          </div>
          <div>
            <span className="font-medium">Word Count:</span> {rfcContent.split(/\s+/).length}
          </div>
          <div>
            <span className="font-medium">Characters:</span> {rfcContent.length}
          </div>
          <div>
            <span className="font-medium">Generated:</span> {new Date().toLocaleDateString()}
          </div>
        </div>
      </div>
    </div>
  );
} 