import React, { useState } from 'react';
import {
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  Box,
  Autocomplete,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useQuery } from 'react-query';
import { wmsApi } from '../api/wms';
import { useWMSStore } from '../store/wms';

const StockByLocation: React.FC = () => {
  const { selectedWarehouse, setError } = useWMSStore();
  const [selectedLocation, setSelectedLocation] = useState<any>(null);
  const [itemCode, setItemCode] = useState('');

  const { data: locations } = useQuery(
    ['locations', selectedWarehouse],
    () => wmsApi.locations.getByWarehouse(selectedWarehouse),
    {
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Failed to load locations');
      },
    }
  );

  const { data: stockByLocation, isLoading: stockLoading } = useQuery(
    ['stock-by-location', selectedLocation?.id],
    () => wmsApi.stock.byLocation(selectedLocation.id),
    {
      enabled: !!selectedLocation,
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Failed to load stock');
      },
    }
  );

  const { data: stockByItem } = useQuery(
    ['stock-by-item', selectedWarehouse, itemCode],
    () => wmsApi.stock.byItem(selectedWarehouse, itemCode),
    {
      enabled: itemCode.length > 2,
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Failed to load stock by item');
      },
    }
  );

  const { data: lowStockData } = useQuery(
    ['low-stock', selectedWarehouse],
    () => wmsApi.stock.lowStock({ whs: selectedWarehouse, threshold_pct: 20 }),
    {
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Failed to load low stock data');
      },
    }
  );

  const stockColumns: GridColDef[] = [
    { field: 'item_code', headerName: 'Item Code', width: 150 },
    { field: 'item_name', headerName: 'Item Name', width: 200 },
    { field: 'lot_no', headerName: 'Lot/Serial', width: 120 },
    { field: 'qty', headerName: 'Quantity', width: 100, type: 'number' },
    { field: 'uom', headerName: 'UoM', width: 80 },
    { field: 'last_updated', headerName: 'Last Updated', width: 150, type: 'dateTime' },
  ];

  const lowStockColumns: GridColDef[] = [
    { field: 'location_code', headerName: 'Location', width: 150 },
    { field: 'current_qty', headerName: 'Current Qty', width: 100, type: 'number' },
    { field: 'capacity_qty', headerName: 'Capacity', width: 100, type: 'number' },
    { field: 'utilization_pct', headerName: 'Utilization %', width: 120, type: 'number' },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Stock by Location
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Stock by Location
              </Typography>
              
              <Autocomplete
                options={locations?.data || []}
                getOptionLabel={(option) => `${option.code} - ${option.name || 'No name'}`}
                value={selectedLocation}
                onChange={(_, newValue) => setSelectedLocation(newValue)}
                renderInput={(params) => (
                  <TextField {...params} label="Select Location" margin="normal" />
                )}
              />
              
              <Box sx={{ height: 300, mt: 2 }}>
                <DataGrid
                  rows={stockByLocation?.data || []}
                  columns={stockColumns}
                  loading={stockLoading}
                  pageSize={5}
                  rowsPerPageOptions={[5, 10, 25]}
                  disableSelectionOnClick
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Stock by Item
              </Typography>
              
              <TextField
                fullWidth
                label="Item Code"
                value={itemCode}
                onChange={(e) => setItemCode(e.target.value)}
                margin="normal"
                helperText="Enter at least 3 characters"
              />
              
              {stockByItem?.data && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body1" gutterBottom>
                    <strong>Item:</strong> {stockByItem.data.item_code} - {stockByItem.data.item_name}
                  </Typography>
                  <Box sx={{ height: 250, mt: 1 }}>
                    <DataGrid
                      rows={stockByItem.data.locations || []}
                      columns={stockColumns}
                      pageSize={5}
                      rowsPerPageOptions={[5, 10]}
                      disableSelectionOnClick
                    />
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Low Stock Locations (Below 20% Capacity)
              </Typography>
              
              <Box sx={{ height: 300, mt: 2 }}>
                <DataGrid
                  rows={lowStockData?.data?.data || []}
                  columns={lowStockColumns}
                  pageSize={10}
                  rowsPerPageOptions={[10, 25, 50]}
                  disableSelectionOnClick
                  getRowId={(row) => row.location_id}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default StockByLocation;
