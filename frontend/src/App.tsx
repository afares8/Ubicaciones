import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { QueryClient, QueryClientProvider } from 'react-query';
import WMSLayout from './modules/wms/components/WMSLayout';
import WarehouseDesigner from './modules/wms/pages/WarehouseDesigner';
import BinManager from './modules/wms/pages/BinManager';
import StockByLocation from './modules/wms/pages/StockByLocation';
import Operations from './modules/wms/pages/Operations';
import CycleCount from './modules/wms/pages/CycleCount';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <WMSLayout>
            <Routes>
              <Route path="/" element={<WarehouseDesigner />} />
              <Route path="/warehouse-designer" element={<WarehouseDesigner />} />
              <Route path="/bin-manager" element={<BinManager />} />
              <Route path="/stock-by-location" element={<StockByLocation />} />
              <Route path="/operations" element={<Operations />} />
              <Route path="/cycle-count" element={<CycleCount />} />
            </Routes>
          </WMSLayout>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
