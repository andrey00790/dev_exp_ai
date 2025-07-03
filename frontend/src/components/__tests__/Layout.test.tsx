import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Layout from '../Layout';

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Layout', () => {
  it('renders AI Assistant title', () => {
    renderWithRouter(
      <Layout>
        <div>Test content</div>
      </Layout>
    );
    
    expect(screen.getByText('AI Assistant')).toBeInTheDocument();
  });

  it('renders navigation items', () => {
    renderWithRouter(
      <Layout>
        <div>Test content</div>
      </Layout>
    );
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Search')).toBeInTheDocument();
    expect(screen.getByText('Generate RFC')).toBeInTheDocument();
    expect(screen.getByText('Code Docs')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders children content', () => {
    renderWithRouter(
      <Layout>
        <div>Test content</div>
      </Layout>
    );
    
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('renders New Chat button', () => {
    renderWithRouter(
      <Layout>
        <div>Test content</div>
      </Layout>
    );
    
    expect(screen.getByText('New Chat')).toBeInTheDocument();
  });

  it('renders Recent Chats section', () => {
    renderWithRouter(
      <Layout>
        <div>Test content</div>
      </Layout>
    );
    
    expect(screen.getByText('Recent Chats')).toBeInTheDocument();
  });
}); 