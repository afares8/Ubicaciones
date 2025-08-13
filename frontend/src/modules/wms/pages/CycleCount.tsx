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
  Autocomplete,
} from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { wmsApi } from '../api/wms';
import { useWMSStore } from '../store/wms';

const CycleCount: React.FC = () => {
  const { selectedWarehouse, setError, clearError } = useWMSStore();
  const queryClient = useQueryClient();
  const [selectedLocations, setSelectedLocations] = useState<any[]>([]);
  const [selectedSession, setSelectedSession] = useState<any>(null);
  const [countEntries, setCountEntries] = useState<{ [key: number]: number }>({});

  const { data: locations } = useQuery(
    ['locations', selectedWarehouse],
    () => wmsApi.locations.getByWarehouse(selectedWarehouse),
    {
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Error al cargar ubicaciones');
      },
    }
  );

  const { data: countSessions, refetch: refetchSessions } = useQuery(
    ['count-sessions', selectedWarehouse],
    () => wmsApi.counts.list({ whs: selectedWarehouse, limit: 50 }),
    {
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Error al cargar sesiones de conteo');
      },
    }
  );

  const { data: sessionDetails } = useQuery(
    ['count-session-details', selectedSession?.id],
    () => wmsApi.counts.getDetails(selectedSession.id),
    {
      enabled: !!selectedSession,
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Error al cargar detalles de sesión');
      },
    }
  );

  const createSessionMutation = useMutation(
    (data: { whs: string; scope: any }) => wmsApi.counts.create(data),
    {
      onSuccess: () => {
        clearError();
        alert('Sesión de conteo creada exitosamente');
        setSelectedLocations([]);
        refetchSessions();
      },
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Error al crear sesión de conteo');
      },
    }
  );

  const enterCountsMutation = useMutation(
    (data: { sessionId: number; counts: any[] }) =>
      wmsApi.counts.enterCounts(data.sessionId, data.counts),
    {
      onSuccess: () => {
        clearError();
        alert('Conteos ingresados exitosamente');
        queryClient.invalidateQueries(['count-session-details', selectedSession?.id]);
      },
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Error al ingresar conteos');
      },
    }
  );

  const applyCountsMutation = useMutation(
    (data: { sessionId: number; request: any }) =>
      wmsApi.counts.apply(data.sessionId, data.request),
    {
      onSuccess: () => {
        clearError();
        alert('Ajustes de conteo aplicados exitosamente');
        refetchSessions();
        queryClient.invalidateQueries(['count-session-details', selectedSession?.id]);
      },
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Error al aplicar ajustes de conteo');
      },
    }
  );

  const handleCreateSession = () => {
    if (selectedLocations.length === 0) {
      setError('Por favor seleccione al menos una ubicación');
      return;
    }

    createSessionMutation.mutate({
      whs: selectedWarehouse,
      scope: {
        locations: selectedLocations.map(loc => loc.id),
      },
    });
  };

  const handleEnterCounts = () => {
    const counts = Object.entries(countEntries).map(([detailId, countedQty]) => ({
      detailId: Number(detailId),
      countedQty,
    }));

    if (counts.length === 0) {
      setError('Por favor ingrese al menos un conteo');
      return;
    }

    enterCountsMutation.mutate({
      sessionId: selectedSession.id,
      counts,
    });
  };

  const handleApplyCounts = () => {
    if (!selectedSession) return;

    applyCountsMutation.mutate({
      sessionId: selectedSession.id,
      request: {
        createSapAdjustments: true,
        comment: 'Ajuste de conteo cíclico',
      },
    });
  };

  const sessionColumns: GridColDef[] = [
    { field: 'id', headerName: 'ID de Sesión', width: 100 },
    { field: 'whs_code', headerName: 'Almacén', width: 120 },
    {
      field: 'status',
      headerName: 'Estado',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value === 'OPEN' ? 'ABIERTO' : params.value === 'CLOSED' ? 'CERRADO' : 'APLICADO'}
          color={params.value === 'OPEN' ? 'primary' : 'default'}
          size="small"
        />
      ),
    },
    { field: 'created_by', headerName: 'Creado Por', width: 150 },
    { field: 'created_at', headerName: 'Fecha de Creación', width: 180, type: 'dateTime' },
  ];

  const detailColumns: GridColDef[] = [
    { field: 'item_code', headerName: 'Código de Artículo', width: 150 },
    { field: 'lot_no', headerName: 'Lote/Serie', width: 120 },
    { field: 'expected_qty', headerName: 'Esperado', width: 100, type: 'number' },
    {
      field: 'counted_qty',
      headerName: 'Contado',
      width: 120,
      renderCell: (params) => (
        <TextField
          size="small"
          type="number"
          value={countEntries[params.row.id] || params.value || ''}
          onChange={(e) => setCountEntries({
            ...countEntries,
            [params.row.id]: Number(e.target.value),
          })}
          disabled={selectedSession?.status !== 'OPEN'}
        />
      ),
    },
    {
      field: 'adjusted',
      headerName: 'Ajustado',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Sí' : 'No'}
          color={params.value ? 'success' : 'default'}
          size="small"
        />
      ),
    },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Conteo Cíclico
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Crear Nueva Sesión de Conteo
              </Typography>
              
              <Autocomplete
                multiple
                options={locations?.data || []}
                getOptionLabel={(option) => `${option.code} - ${option.name || 'Sin nombre'}`}
                value={selectedLocations}
                onChange={(_, newValue) => setSelectedLocations(newValue)}
                renderInput={(params) => (
                  <TextField {...params} label="Seleccionar Ubicaciones" margin="normal" />
                )}
              />
              
              <Button
                variant="contained"
                onClick={handleCreateSession}
                disabled={createSessionMutation.isLoading}
                sx={{ mt: 2 }}
              >
                {createSessionMutation.isLoading ? 'Creando...' : 'Crear Sesión de Conteo'}
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Sesiones de Conteo
              </Typography>
              
              <Box sx={{ height: 300, mt: 2 }}>
                <DataGrid
                  rows={countSessions?.data?.data || []}
                  columns={sessionColumns}
                  initialState={{
                    pagination: {
                      paginationModel: { page: 0, pageSize: 5 },
                    },
                  }}
                  pageSizeOptions={[5, 10]}
                  disableRowSelectionOnClick
                  onRowClick={(params) => setSelectedSession(params.row)}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {selectedSession && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Detalles de Sesión de Conteo - {selectedSession.id}
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body1">
                    Estado: <Chip label={selectedSession.status === 'OPEN' ? 'ABIERTO' : selectedSession.status === 'CLOSED' ? 'CERRADO' : 'APLICADO'} size="small" />
                  </Typography>
                </Box>
                
                <Box sx={{ height: 400, mt: 2 }}>
                  <DataGrid
                    rows={sessionDetails?.data?.data?.details || []}
                    columns={detailColumns}
                    initialState={{
                      pagination: {
                        paginationModel: { page: 0, pageSize: 10 },
                      },
                    }}
                    pageSizeOptions={[10, 25]}
                    disableRowSelectionOnClick
                  />
                </Box>
                
                {selectedSession.status === 'OPEN' && (
                  <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                    <Button
                      variant="contained"
                      onClick={handleEnterCounts}
                      disabled={enterCountsMutation.isLoading}
                    >
                      {enterCountsMutation.isLoading ? 'Guardando...' : 'Guardar Conteos'}
                    </Button>
                    <Button
                      variant="contained"
                      color="secondary"
                      onClick={handleApplyCounts}
                      disabled={applyCountsMutation.isLoading}
                    >
                      {applyCountsMutation.isLoading ? 'Aplicando...' : 'Aplicar Ajustes'}
                    </Button>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default CycleCount;
