import React from 'react';
import { TextField } from '@mui/material';

export const Textarea: React.FC<any> = (props) => <TextField multiline rows={4} variant="outlined" {...props} />;
