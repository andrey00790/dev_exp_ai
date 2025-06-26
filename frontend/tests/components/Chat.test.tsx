/**
 * Tests for Chat component
 */

import { render, screen, fireEvent, waitFor } from '../utils/test-utils';
import Chat from '../../src/components/Chat';
import { mockFetch, mockApiResponses } from '../utils/test-utils';

// Mock fetch for API calls
global.fetch = mockFetch(mockApiResponses.search);

describe('Chat Component', () => {
  test('renders chat interface', () => {
    render(<Chat />);
    
    expect(screen.getByText('Chat with AI Assistant')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Type your message...')).toBeInTheDocument();
    expect(screen.getByText('Send')).toBeInTheDocument();
  });

  test('allows typing in message input', () => {
    render(<Chat />);
    
    const input = screen.getByPlaceholderText('Type your message...') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'Hello AI' } });
    
    expect(input.value).toBe('Hello AI');
  });

  test('sends message when send button is clicked', async () => {
    render(<Chat />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText('Test message')).toBeInTheDocument();
    });
  });

  test('sends message when Enter key is pressed', async () => {
    render(<Chat />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });
    
    await waitFor(() => {
      expect(screen.getByText('Test message')).toBeInTheDocument();
    });
  });

  test('clears input after sending message', async () => {
    render(<Chat />);
    
    const input = screen.getByPlaceholderText('Type your message...') as HTMLInputElement;
    const sendButton = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(input.value).toBe('');
    });
  });

  test('disables send button when input is empty', () => {
    render(<Chat />);
    
    const sendButton = screen.getByText('Send');
    expect(sendButton).toBeDisabled();
  });

  test('enables send button when input has text', () => {
    render(<Chat />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'Test' } });
    expect(sendButton).not.toBeDisabled();
  });

  test('shows loading state while sending message', async () => {
    // Mock delayed response
    global.fetch = jest.fn().mockImplementation(
      () => new Promise(resolve => 
        setTimeout(() => resolve({
          ok: true,
          json: () => Promise.resolve(mockApiResponses.search)
        }), 100)
      )
    );

    render(<Chat />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);
    
    // Should show loading state
    expect(screen.getByText('Sending...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.queryByText('Sending...')).not.toBeInTheDocument();
    });
  });

  test('displays error message on API failure', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('API Error'));

    render(<Chat />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText(/Error sending message/)).toBeInTheDocument();
    });
  });

  test('displays chat history', async () => {
    render(<Chat />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');
    
    // Send first message
    fireEvent.change(input, { target: { value: 'First message' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText('First message')).toBeInTheDocument();
    });
    
    // Send second message
    fireEvent.change(input, { target: { value: 'Second message' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(screen.getByText('First message')).toBeInTheDocument();
      expect(screen.getByText('Second message')).toBeInTheDocument();
    });
  });

  test('shows message timestamps', async () => {
    render(<Chat />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      // Should show timestamp (format may vary)
      expect(screen.getByText(/\d{1,2}:\d{2}/)).toBeInTheDocument();
    });
  });

  test('scrolls to bottom when new message is added', async () => {
    const scrollIntoViewMock = jest.fn();
    Element.prototype.scrollIntoView = scrollIntoViewMock;

    render(<Chat />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(scrollIntoViewMock).toHaveBeenCalled();
    });
  });
}); 