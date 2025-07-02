import React from 'react';
import { Container, Paper } from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import AnalyticsDashboard from '../components/Analytics/AnalyticsDashboard';

const Analytics: React.FC = () => {
  const { user } = useAuth();

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Paper elevation={1} sx={{ p: 3 }}>
        <AnalyticsDashboard 
          userId={user?.user_id ? parseInt(user.user_id) : undefined}
          isAdmin={user?.scopes?.includes('admin') || false}
        />
      </Paper>
    </Container>
  );
};

export default Analytics; 