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
        setError(error.response?.data?.message || 'Error al cargar ubicaciones');
      },
    }
  );

  const { data: stockByLocation, isLoading: stockLoading } = useQuery(
    ['stock-by-location', selectedLocation?.id],
    () => wmsApi.stock.byLocation(selectedLocation.id),
    {
      enabled: !!selectedLocation,
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Error al cargar inventario');
      },
    }
  );

  const { data: stockByItem } = useQuery(
    ['stock-by-item', selectedWarehouse, itemCode],
    () => wmsApi.stock.byItem(selectedWarehouse, itemCode),
    {
      enabled: itemCode.length > 2,
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Error al cargar inventario por artículo');
      },
    }
  );

  const { data: lowStockData } = useQuery(
    ['low-stock', selectedWarehouse],
    () => wmsApi.stock.lowStock({ whs: selectedWarehouse, threshold_pct: 20 }),
    {
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Error al cargar datos de stock bajo');
      },
    }
  );

  const stockColumns: GridColDef[] = [
    { field: 'item_code', headerName: 'Código de Artículo', width: 150 },
    { field: 'item_name', headerName: 'Nombre del Artículo', width: 200 },
    { field: 'lot_no', headerName: 'Lote/Serie', width: 120 },
    { field: 'qty', headerName: 'Cantidad', width: 100, type: 'number' },
    { field: 'uom', headerName: 'UdM', width: 80 },
    { field: 'last_updated', headerName: 'Última Actualización', width: 150, type: 'dateTime' },
  ];

  const lowStockColumns: GridColDef[] = [
    { field: 'location_code', headerName: 'Ubicación', width: 150 },
    { field: 'current_qty', headerName: 'Cant. Actual', width: 100, type: 'number' },
    { field: 'capacity_qty', headerName: 'Capacidad', width: 100, type: 'number' },
    { field: 'utilization_pct', headerName: 'Utilización %', width: 120, type: 'number' },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Stock por Ubicación
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Stock por Ubicación
              </Typography>
              
              <Autocomplete
                options={locations?.data || []}
                getOptionLabel={(option) => `${option.code} - ${option.name || 'Sin nombre'}`}
                value={selectedLocation}
                onChange={(_, newValue) => setSelectedLocation(newValue)}
                renderInput={(params) => (
                  <TextField {...params} label="Seleccionar Ubicación" margin="normal" />
                )}
              />
              
              <Box sx={{ height: 300, mt: 2 }}>
                <DataGrid
                  rows={stockByLocation?.data || []}
                  columns={stockColumns}
                  loading={stockLoading}
                  initialState={{
                    pagination: {
                      paginationModel: { page: 0, pageSize: 5 },
                    },
                  }}
                  pageSizeOptions={[5, 10, 25]}
                  disableRowSelectionOnClick
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Stock por Artículo
              </Typography>
              
              <TextField
                fullWidth
                label="Código de Artículo"
                value={itemCode}
                onChange={(e) => setItemCode(e.target.value)}
                margin="normal"
                helperText="Ingrese al menos 3 caracteres"
              />
              
              {stockByItem?.data && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body1" gutterBottom>
                    <strong>Artículo:</strong> {stockByItem.data.item_code} - {stockByItem.data.item_name}
                  </Typography>
                  <Box sx={{ height: 250, mt: 1 }}>
                    <DataGrid
                      rows={stockByItem.data.locations || []}
                      columns={stockColumns}
                      initialState={{
                        pagination: {
                          paginationModel: { page: 0, pageSize: 5 },
                        },
                      }}
                      pageSizeOptions={[5, 10]}
                      disableRowSelectionOnClick
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
                Ubicaciones con Stock Bajo (Menos del 20% de Capacidad)
              </Typography>
              
              <Box sx={{ height: 300, mt: 2 }}>
                <DataGrid
                  rows={lowStockData?.data?.data || []}
                  columns={lowStockColumns}
                  initialState={{
                    pagination: {
                      paginationModel: { page: 0, pageSize: 10 },
                    },
                  }}
                  pageSizeOptions={[10, 25, 50]}
                  disableRowSelectionOnClick
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
