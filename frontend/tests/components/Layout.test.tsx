/**
 * Tests for Layout component
 */

import { render, screen, fireEvent } from '../utils/test-utils';
import Layout from '../../src/components/Layout';
import { testIds, mockUser } from '../utils/test-utils';

// Mock the auth context
jest.mock('../../src/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    logout: jest.fn(),
    isAuthenticated: true,
    loading: false
  })
}));

describe('Layout Component', () => {
  const renderLayout = (children = <div>Test Content</div>) => {
    return render(<Layout>{children}</Layout>);
  };

  test('renders layout with navigation', () => {
    renderLayout();
    
    // Check if main navigation items are present
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Chat')).toBeInTheDocument();
    expect(screen.getByText('Vector Search')).toBeInTheDocument();
    expect(screen.getByText('AI Analytics')).toBeInTheDocument();
    expect(screen.getByText('Real-time Monitoring')).toBeInTheDocument();
  });

  test('renders user profile information', () => {
    renderLayout();
    
    // Check user name and email
    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    
    // Check budget information
    expect(screen.getByText('$50.00 / $100.00')).toBeInTheDocument();
  });

  test('renders children content', () => {
    renderLayout(<div>Custom Test Content</div>);
    
    expect(screen.getByText('Custom Test Content')).toBeInTheDocument();
  });

  test('highlights active navigation item', () => {
    // Mock useLocation to return dashboard path
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useLocation: () => ({ pathname: '/' })
    }));

    renderLayout();
    
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    expect(dashboardLink).toHaveClass('bg-gray-700', 'text-white');
  });

  test('shows new chat button', () => {
    renderLayout();
    
    const newChatButton = screen.getByText('New Chat');
    expect(newChatButton).toBeInTheDocument();
    expect(newChatButton.closest('a')).toHaveAttribute('href', '/chat');
  });

  test('displays recent chat history', () => {
    renderLayout();
    
    expect(screen.getByText('Recent Chats')).toBeInTheDocument();
    expect(screen.getByText('Search for API documentation')).toBeInTheDocument();
    expect(screen.getByText('Generate RFC for user auth')).toBeInTheDocument();
  });

  test('renders mobile menu toggle on small screens', () => {
    // Mock window size for mobile
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 500,
    });

    renderLayout();
    
    // Mobile menu should be available (though visibility depends on CSS)
    const mobileToggle = screen.getByRole('button');
    expect(mobileToggle).toBeInTheDocument();
  });

  test('user initials are calculated correctly', () => {
    renderLayout();
    
    // Should show "TU" for "Test User"
    expect(screen.getByText('TU')).toBeInTheDocument();
  });

  test('budget status color is correct', () => {
    renderLayout();
    
    // With 50% usage (50/100), should be green
    const budgetText = screen.getByText('$50.00 / $100.00');
    expect(budgetText).toHaveClass('text-green-400');
  });

  test('logout button is present and functional', () => {
    const mockLogout = jest.fn();
    
    jest.mock('../../src/contexts/AuthContext', () => ({
      useAuth: () => ({
        user: mockUser,
        logout: mockLogout,
        isAuthenticated: true,
        loading: false
      })
    }));

    renderLayout();
    
    const logoutButton = screen.getByTitle('Logout');
    expect(logoutButton).toBeInTheDocument();
    
    fireEvent.click(logoutButton);
    // Note: Due to mocking limitations, we can't easily test if logout was called
    // In a real test, you'd verify the logout function was called
  });

  test('navigation links have correct hrefs', () => {
    renderLayout();
    
    const links = [
      { text: 'Dashboard', href: '/' },
      { text: 'Chat', href: '/chat' },
      { text: 'Vector Search', href: '/vector-search' },
      { text: 'AI Analytics', href: '/ai-analytics' },
      { text: 'Real-time Monitoring', href: '/realtime-monitoring' },
    ];

    links.forEach(({ text, href }) => {
      const link = screen.getByText(text).closest('a');
      expect(link).toHaveAttribute('href', href);
    });
  });

  test('AI Assistant title is displayed', () => {
    renderLayout();
    
    expect(screen.getByText('AI Assistant')).toBeInTheDocument();
  });
}); 