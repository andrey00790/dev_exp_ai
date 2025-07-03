import React from 'react';
import { Button as MuiButton } from '@mui/material';

export const Button: React.FC<any> = (props) => (
  <MuiButton variant="contained" {...props} />
);
