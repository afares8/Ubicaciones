import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box,
  Container,
} from '@mui/material';
import {
  Warehouse,
  Inventory,
  LocationOn,
  SwapHoriz,
  Assessment,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const drawerWidth = 240;

const menuItems = [
  { text: 'Warehouse Designer', icon: <Warehouse />, path: '/warehouse-designer' },
  { text: 'Bin Manager', icon: <LocationOn />, path: '/bin-manager' },
  { text: 'Stock by Location', icon: <Inventory />, path: '/stock-by-location' },
  { text: 'Operations', icon: <SwapHoriz />, path: '/operations' },
  { text: 'Cycle Count', icon: <Assessment />, path: '/cycle-count' },
];

interface WMSLayoutProps {
  children: React.ReactNode;
}

const WMSLayout: React.FC<WMSLayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{ width: `calc(100% - ${drawerWidth}px)`, ml: `${drawerWidth}px` }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div">
            WMS - Bin Locations Inventory System
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Drawer
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
        variant="permanent"
        anchor="left"
      >
        <Toolbar />
        <List>
          {menuItems.map((item) => (
            <ListItem
              button
              key={item.text}
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
          ))}
        </List>
      </Drawer>
      
      <Box
        component="main"
        sx={{ flexGrow: 1, bgcolor: 'background.default', p: 3 }}
      >
        <Toolbar />
        <Container maxWidth="xl">
          {children}
        </Container>
      </Box>
    </Box>
  );
};

export default WMSLayout;
