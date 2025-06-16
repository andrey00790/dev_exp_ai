import { render, screen, fireEvent } from '@testing-library/react';
import Chat from '../Chat';

const mockMessages = [
  {
    id: '1',
    type: 'user' as const,
    content: 'Hello, AI!',
    timestamp: new Date('2024-01-15T10:00:00'),
  },
  {
    id: '2',
    type: 'assistant' as const,
    content: 'Hello! How can I help you today?',
    timestamp: new Date('2024-01-15T10:00:30'),
  },
];

describe('Chat', () => {
  const mockOnSendMessage = jest.fn();

  beforeEach(() => {
    mockOnSendMessage.mockClear();
  });

  it('renders welcome message when no messages', () => {
    render(
      <Chat
        messages={[]}
        onSendMessage={mockOnSendMessage}
      />
    );
    
    expect(screen.getByText('Welcome to AI Assistant')).toBeInTheDocument();
  });

  it('renders messages correctly', () => {
    render(
      <Chat
        messages={mockMessages}
        onSendMessage={mockOnSendMessage}
      />
    );
    
    expect(screen.getByText('Hello, AI!')).toBeInTheDocument();
    expect(screen.getByText('Hello! How can I help you today?')).toBeInTheDocument();
  });

  it('sends message when form is submitted', () => {
    render(
      <Chat
        messages={[]}
        onSendMessage={mockOnSendMessage}
      />
    );
    
    const input = screen.getByPlaceholderText('Type your message...');
    const submitButton = screen.getByRole('button', { name: /send/i });
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(submitButton);
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message');
  });

  it('sends message when Enter is pressed', () => {
    render(
      <Chat
        messages={[]}
        onSendMessage={mockOnSendMessage}
      />
    );
    
    const input = screen.getByPlaceholderText('Type your message...');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    
    expect(mockOnSendMessage).toHaveBeenCalledWith('Test message');
  });

  it('does not send empty messages', () => {
    render(
      <Chat
        messages={[]}
        onSendMessage={mockOnSendMessage}
      />
    );
    
    const submitButton = screen.getByRole('button', { name: /send/i });
    fireEvent.click(submitButton);
    
    expect(mockOnSendMessage).not.toHaveBeenCalled();
  });

  it('disables input when loading', () => {
    render(
      <Chat
        messages={[]}
        onSendMessage={mockOnSendMessage}
        isLoading={true}
      />
    );
    
    const input = screen.getByPlaceholderText('Type your message...');
    const submitButton = screen.getByRole('button', { name: /send/i });
    
    expect(input).toBeDisabled();
    expect(submitButton).toBeDisabled();
  });
}); 