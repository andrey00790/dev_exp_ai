import React, { useContext } from 'react';
import { Box, Container, Paper } from '@mui/material';
import { AuthContext } from '../contexts/AuthContext';
import AnalyticsDashboard from '../components/Analytics/AnalyticsDashboard';

const Analytics: React.FC = () => {
  const { user } = useContext(AuthContext);

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Paper elevation={1} sx={{ p: 3 }}>
        <AnalyticsDashboard 
          userId={user?.id}
          isAdmin={user?.is_admin || false}
        />
      </Paper>
    </Container>
  );
};

export default Analytics; 