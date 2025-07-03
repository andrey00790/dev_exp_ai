import React from 'react';
import { Tabs as MuiTabs, Tab, Box } from '@mui/material';

export const Tabs: React.FC<any> = (props) => <MuiTabs {...props} />;
export const TabsList: React.FC<any> = (props) => <Box {...props} />;
export const TabsTrigger: React.FC<any> = (props) => <Tab {...props} />;
export const TabsContent: React.FC<any> = (props) => <Box {...props} />;
