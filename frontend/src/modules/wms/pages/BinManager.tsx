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
  Chip,
  IconButton,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Print, Edit } from '@mui/icons-material';
import { useQuery, useMutation } from 'react-query';
import { wmsApi } from '../api/wms';
import { useWMSStore } from '../store/wms';

const BinManager: React.FC = () => {
  const { selectedWarehouse, setError } = useWMSStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBin, setSelectedBin] = useState<any>(null);

  const { data: searchResults, isLoading } = useQuery(
    ['bins-search', searchQuery, selectedWarehouse],
    () => wmsApi.bins.search({ q: searchQuery, whs: selectedWarehouse, limit: 100 }),
    {
      enabled: searchQuery.length > 2,
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Error al buscar ubicaciones');
      },
    }
  );

  const { data: capacityData } = useQuery(
    ['bin-capacity', selectedBin?.id],
    () => wmsApi.bins.getCapacity(selectedBin.id),
    {
      enabled: !!selectedBin,
    }
  );

  const printLabelMutation = useMutation(
    (data: { locationId: number; format: string }) =>
      wmsApi.labels.generate(data.locationId, data.format),
    {
      onSuccess: () => {
        alert('Etiqueta enviada a impresora exitosamente');
      },
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Error al imprimir etiqueta');
      },
    }
  );

  const columns: GridColDef[] = [
    { field: 'code', headerName: 'Código de Ubicación', width: 200 },
    { field: 'name', headerName: 'Nombre', width: 150 },
    { field: 'type', headerName: 'Tipo', width: 120 },
    {
      field: 'is_active',
      headerName: 'Estado',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Activo' : 'Inactivo'}
          color={params.value ? 'success' : 'default'}
          size="small"
        />
      ),
    },
    {
      field: 'actions',
      headerName: 'Acciones',
      width: 150,
      renderCell: (params) => (
        <Box>
          <IconButton
            size="small"
            onClick={() => setSelectedBin(params.row)}
          >
            <Edit />
          </IconButton>
          <IconButton
            size="small"
            onClick={() => printLabelMutation.mutate({ locationId: params.row.id, format: 'zpl' })}
          >
            <Print />
          </IconButton>
        </Box>
      ),
    },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Gestor de Ubicaciones
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Buscar Ubicaciones
              </Typography>
              
              <TextField
                fullWidth
                label="Buscar por código o nombre de ubicación"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                margin="normal"
                helperText="Ingrese al menos 3 caracteres para buscar"
              />
              
              <Box sx={{ height: 400, mt: 2 }}>
                <DataGrid
                  rows={searchResults?.data || []}
                  columns={columns}
                  loading={isLoading}
                  initialState={{
                    pagination: {
                      paginationModel: { page: 0, pageSize: 10 },
                    },
                  }}
                  pageSizeOptions={[10, 25, 50]}
                  disableRowSelectionOnClick
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Detalles de Ubicación
              </Typography>
              
              {selectedBin ? (
                <Box>
                  <Typography variant="body1" gutterBottom>
                    <strong>Código:</strong> {selectedBin.code}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>Nombre:</strong> {selectedBin.name || 'N/A'}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>Tipo:</strong> {selectedBin.type || 'N/A'}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>Sección:</strong> {selectedBin.section || 'N/A'}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>Pasillo:</strong> {selectedBin.aisle || 'N/A'}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>Estante:</strong> {selectedBin.rack || 'N/A'}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>Nivel:</strong> {selectedBin.level || 'N/A'}
                  </Typography>
                  
                  {capacityData?.data && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="h6" gutterBottom>
                        Información de Capacidad
                      </Typography>
                      <Typography variant="body2">
                        Capacidad: {capacityData.data.capacity_qty || 'N/A'} {capacityData.data.capacity_uom || ''}
                      </Typography>
                      <Typography variant="body2">
                        Actual: {capacityData.data.current_qty} ({capacityData.data.current_items} artículos)
                      </Typography>
                      {capacityData.data.utilization_pct && (
                        <Typography variant="body2">
                          Utilización: {capacityData.data.utilization_pct.toFixed(1)}%
                        </Typography>
                      )}
                    </Box>
                  )}
                  
                  <Button
                    variant="contained"
                    startIcon={<Print />}
                    onClick={() => printLabelMutation.mutate({ locationId: selectedBin.id, format: 'zpl' })}
                    sx={{ mt: 2 }}
                    disabled={printLabelMutation.isLoading}
                  >
                    Imprimir Etiqueta
                  </Button>
                </Box>
              ) : (
                <Typography color="text.secondary">
                  Seleccione una ubicación para ver detalles
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default BinManager;
