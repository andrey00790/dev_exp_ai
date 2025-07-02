import React from 'react';
import { Alert as MuiAlert, AlertTitle } from '@mui/material';

export const Alert: React.FC<any> = (props) => <MuiAlert {...props} />;
export const AlertDescription: React.FC<{ children: React.ReactNode }> = ({ children }) => <div>{children}</div>;
