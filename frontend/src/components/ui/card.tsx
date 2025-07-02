import React from 'react';
import { Card as MuiCard, CardContent as MuiCardContent, CardHeader as MuiCardHeader, Typography } from '@mui/material';

export const Card: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
  <MuiCard className={className}>{children}</MuiCard>
);

export const CardContent: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
  <MuiCardContent className={className}>{children}</MuiCardContent>
);

export const CardHeader: React.FC<{ children?: React.ReactNode; className?: string }> = ({ children, className }) => (
  <MuiCardHeader className={className} title={children} />
);

export const CardTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
  <Typography variant="h6" className={className}>{children}</Typography>
);
