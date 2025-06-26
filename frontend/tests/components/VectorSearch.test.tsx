/**
 * Tests for VectorSearch component
 */

import { render, screen, fireEvent, waitFor } from '../utils/test-utils';
import VectorSearch from '../../src/pages/VectorSearch';
import { mockFetch } from '../utils/test-utils';

describe('VectorSearch Component', () => {
  const mockSearchResults = {
    results: [
      {
        id: '1',
        title: 'React Hooks Documentation',
        content: 'Hooks are a new addition in React 16.8...',
        score: 0.95,
        metadata: { source: 'confluence', type: 'documentation' }
      },
      {
        id: '2', 
        title: 'API Gateway Design',
        content: 'API Gateway patterns for microservices...',
        score: 0.87,
        metadata: { source: 'gitlab', type: 'code' }
      }
    ],
    total: 2,
    query_time: 0.234
  };

  beforeEach(() => {
    global.fetch = mockFetch(mockSearchResults);
  });

  test('renders search interface', () => {
    render(<VectorSearch />);
    
    expect(screen.getByText('Vector Search')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your search query...')).toBeInTheDocument();
    expect(screen.getByText('Search')).toBeInTheDocument();
  });

  test('performs search when form is submitted', async () => {
    render(<VectorSearch />);
    
    const searchInput = screen.getByPlaceholderText('Enter your search query...');
    const searchButton = screen.getByText('Search');
    
    fireEvent.change(searchInput, { target: { value: 'React hooks' } });
    fireEvent.click(searchButton);
    
    await waitFor(() => {
      expect(screen.getByText('React Hooks Documentation')).toBeInTheDocument();
      expect(screen.getByText('API Gateway Design')).toBeInTheDocument();
    });
  });

  test('displays search results with correct information', async () => {
    render(<VectorSearch />);
    
    const searchInput = screen.getByPlaceholderText('Enter your search query...');
    fireEvent.change(searchInput, { target: { value: 'React' } });
    fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter', charCode: 13 });
    
    await waitFor(() => {
      // Check titles
      expect(screen.getByText('React Hooks Documentation')).toBeInTheDocument();
      expect(screen.getByText('API Gateway Design')).toBeInTheDocument();
      
      // Check scores
      expect(screen.getByText('95%')).toBeInTheDocument();
      expect(screen.getByText('87%')).toBeInTheDocument();
      
      // Check sources
      expect(screen.getByText('confluence')).toBeInTheDocument();
      expect(screen.getByText('gitlab')).toBeInTheDocument();
    });
  });

  test('shows loading state during search', async () => {
    global.fetch = jest.fn().mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: () => Promise.resolve(mockSearchResults)
      }), 100))
    );

    render(<VectorSearch />);
    
    const searchInput = screen.getByPlaceholderText('Enter your search query...');
    const searchButton = screen.getByText('Search');
    
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    fireEvent.click(searchButton);
    
    expect(screen.getByText('Searching...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.queryByText('Searching...')).not.toBeInTheDocument();
    });
  });

  test('handles search errors gracefully', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Search failed'));

    render(<VectorSearch />);
    
    const searchInput = screen.getByPlaceholderText('Enter your search query...');
    const searchButton = screen.getByText('Search');
    
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    fireEvent.click(searchButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Error performing search/)).toBeInTheDocument();
    });
  });

  test('disables search button when input is empty', () => {
    render(<VectorSearch />);
    
    const searchButton = screen.getByText('Search');
    expect(searchButton).toBeDisabled();
  });

  test('enables search button when input has text', () => {
    render(<VectorSearch />);
    
    const searchInput = screen.getByPlaceholderText('Enter your search query...');
    const searchButton = screen.getByText('Search');
    
    fireEvent.change(searchInput, { target: { value: 'test' } });
    expect(searchButton).not.toBeDisabled();
  });

  test('displays query time and result count', async () => {
    render(<VectorSearch />);
    
    const searchInput = screen.getByPlaceholderText('Enter your search query...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter', charCode: 13 });
    
    await waitFor(() => {
      expect(screen.getByText('2 results')).toBeInTheDocument();
      expect(screen.getByText('0.234s')).toBeInTheDocument();
    });
  });

  test('shows empty state when no results found', async () => {
    global.fetch = mockFetch({ results: [], total: 0, query_time: 0.123 });

    render(<VectorSearch />);
    
    const searchInput = screen.getByPlaceholderText('Enter your search query...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
    fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter', charCode: 13 });
    
    await waitFor(() => {
      expect(screen.getByText('No results found')).toBeInTheDocument();
      expect(screen.getByText('Try different search terms')).toBeInTheDocument();
    });
  });

  test('advanced search toggle works', () => {
    render(<VectorSearch />);
    
    const advancedToggle = screen.getByText('Advanced Search');
    fireEvent.click(advancedToggle);
    
    expect(screen.getByText('Search Mode')).toBeInTheDocument();
    expect(screen.getByText('Source Filter')).toBeInTheDocument();
    expect(screen.getByText('Minimum Score')).toBeInTheDocument();
  });

  test('filters can be applied', async () => {
    render(<VectorSearch />);
    
    // Open advanced search
    fireEvent.click(screen.getByText('Advanced Search'));
    
    // Set filters
    const sourceFilter = screen.getByLabelText('Source Filter');
    const minScoreFilter = screen.getByLabelText('Minimum Score');
    
    fireEvent.change(sourceFilter, { target: { value: 'confluence' } });
    fireEvent.change(minScoreFilter, { target: { value: '0.8' } });
    
    // Perform search
    const searchInput = screen.getByPlaceholderText('Enter your search query...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter', charCode: 13 });
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/vector-search/search'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('"source_filter":"confluence"')
        })
      );
    });
  });

  test('result items are clickable', async () => {
    render(<VectorSearch />);
    
    const searchInput = screen.getByPlaceholderText('Enter your search query...');
    fireEvent.change(searchInput, { target: { value: 'test' } });
    fireEvent.keyPress(searchInput, { key: 'Enter', code: 'Enter', charCode: 13 });
    
    await waitFor(() => {
      const firstResult = screen.getByText('React Hooks Documentation');
      fireEvent.click(firstResult);
      
      // Should show detailed view or navigate
      expect(screen.getByText('Hooks are a new addition in React 16.8...')).toBeInTheDocument();
    });
  });
}); 