/**
 * Tests for Dashboard component
 */

import { render, screen, waitFor } from '../utils/test-utils';
import Dashboard from '../../src/pages/Dashboard';
import { mockFetch, mockApiResponses } from '../utils/test-utils';

// Mock Chart.js components
jest.mock('react-chartjs-2', () => ({
  Line: ({ data }: any) => <div data-testid="line-chart">{JSON.stringify(data)}</div>,
  Bar: ({ data }: any) => <div data-testid="bar-chart">{JSON.stringify(data)}</div>,
  Doughnut: ({ data }: any) => <div data-testid="doughnut-chart">{JSON.stringify(data)}</div>,
}));

describe('Dashboard Component', () => {
  beforeEach(() => {
    global.fetch = mockFetch({
      summary: {
        total_requests: 1000,
        active_models: 4,
        active_users: 50,
        data_points_collected: 10000
      },
      recent_activity: [
        { id: 1, type: 'search', description: 'Semantic search performed', timestamp: '2023-01-01T10:00:00Z' },
        { id: 2, type: 'generation', description: 'RFC generated', timestamp: '2023-01-01T09:30:00Z' }
      ],
      usage_stats: {
        api_calls_today: 150,
        successful_requests: 148,
        error_rate: 1.3
      }
    });
  });

  test('renders dashboard with summary cards', async () => {
    render(<Dashboard />);
    
    expect(screen.getByText('AI Assistant Dashboard')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('1,000')).toBeInTheDocument(); // total_requests
      expect(screen.getByText('4')).toBeInTheDocument(); // active_models
      expect(screen.getByText('50')).toBeInTheDocument(); // active_users
    });
  });

  test('displays recent activity section', async () => {
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Recent Activity')).toBeInTheDocument();
      expect(screen.getByText('Semantic search performed')).toBeInTheDocument();
      expect(screen.getByText('RFC generated')).toBeInTheDocument();
    });
  });

  test('shows usage statistics', async () => {
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('API Calls Today')).toBeInTheDocument();
      expect(screen.getByText('150')).toBeInTheDocument();
      expect(screen.getByText('98.7%')).toBeInTheDocument(); // success rate
    });
  });

  test('renders charts for data visualization', async () => {
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument();
    });
  });

  test('handles loading state', () => {
    global.fetch = jest.fn().mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    render(<Dashboard />);
    
    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
  });

  test('handles error state', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('API Error'));

    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/Error loading dashboard/)).toBeInTheDocument();
    });
  });

  test('refresh button updates data', async () => {
    render(<Dashboard />);
    
    const refreshButton = screen.getByText('Refresh');
    expect(refreshButton).toBeInTheDocument();
    
    // Initial load
    await waitFor(() => {
      expect(screen.getByText('1,000')).toBeInTheDocument();
    });
    
    // Mock new data
    global.fetch = mockFetch({
      summary: {
        total_requests: 1100,
        active_models: 5,
        active_users: 55,
        data_points_collected: 11000
      }
    });
    
    // Click refresh
    refreshButton.click();
    
    await waitFor(() => {
      expect(screen.getByText('1,100')).toBeInTheDocument();
    });
  });

  test('displays correct timestamps for recent activity', async () => {
    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText(/10:00/)).toBeInTheDocument();
      expect(screen.getByText(/09:30/)).toBeInTheDocument();
    });
  });

  test('shows empty state when no recent activity', async () => {
    global.fetch = mockFetch({
      summary: { total_requests: 0, active_models: 0, active_users: 0, data_points_collected: 0 },
      recent_activity: [],
      usage_stats: { api_calls_today: 0, successful_requests: 0, error_rate: 0 }
    });

    render(<Dashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('No recent activity')).toBeInTheDocument();
    });
  });
}); 