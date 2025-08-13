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
        setError(error.response?.data?.message || 'Failed to load locations');
      },
    }
  );

  const { data: countSessions, refetch: refetchSessions } = useQuery(
    ['count-sessions', selectedWarehouse],
    () => wmsApi.counts.list({ whs: selectedWarehouse, limit: 50 }),
    {
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Failed to load count sessions');
      },
    }
  );

  const { data: sessionDetails } = useQuery(
    ['count-session-details', selectedSession?.id],
    () => wmsApi.counts.getDetails(selectedSession.id),
    {
      enabled: !!selectedSession,
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Failed to load session details');
      },
    }
  );

  const createSessionMutation = useMutation(
    (data: { whs: string; scope: any }) => wmsApi.counts.create(data),
    {
      onSuccess: () => {
        clearError();
        alert('Count session created successfully');
        setSelectedLocations([]);
        refetchSessions();
      },
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Failed to create count session');
      },
    }
  );

  const enterCountsMutation = useMutation(
    (data: { sessionId: number; counts: any[] }) =>
      wmsApi.counts.enterCounts(data.sessionId, data.counts),
    {
      onSuccess: () => {
        clearError();
        alert('Counts entered successfully');
        queryClient.invalidateQueries(['count-session-details', selectedSession?.id]);
      },
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Failed to enter counts');
      },
    }
  );

  const applyCountsMutation = useMutation(
    (data: { sessionId: number; request: any }) =>
      wmsApi.counts.apply(data.sessionId, data.request),
    {
      onSuccess: () => {
        clearError();
        alert('Count adjustments applied successfully');
        refetchSessions();
        queryClient.invalidateQueries(['count-session-details', selectedSession?.id]);
      },
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Failed to apply count adjustments');
      },
    }
  );

  const handleCreateSession = () => {
    if (selectedLocations.length === 0) {
      setError('Please select at least one location');
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
      setError('Please enter at least one count');
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
        comment: 'Cycle count adjustment',
      },
    });
  };

  const sessionColumns: GridColDef[] = [
    { field: 'id', headerName: 'Session ID', width: 100 },
    { field: 'whs_code', headerName: 'Warehouse', width: 120 },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={params.value}
          color={params.value === 'OPEN' ? 'primary' : 'default'}
          size="small"
        />
      ),
    },
    { field: 'created_by', headerName: 'Created By', width: 150 },
    { field: 'created_at', headerName: 'Created At', width: 180, type: 'dateTime' },
  ];

  const detailColumns: GridColDef[] = [
    { field: 'item_code', headerName: 'Item Code', width: 150 },
    { field: 'lot_no', headerName: 'Lot/Serial', width: 120 },
    { field: 'expected_qty', headerName: 'Expected', width: 100, type: 'number' },
    {
      field: 'counted_qty',
      headerName: 'Counted',
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
      headerName: 'Adjusted',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Yes' : 'No'}
          color={params.value ? 'success' : 'default'}
          size="small"
        />
      ),
    },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Cycle Count
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Create New Count Session
              </Typography>
              
              <Autocomplete
                multiple
                options={locations?.data || []}
                getOptionLabel={(option) => `${option.code} - ${option.name || 'No name'}`}
                value={selectedLocations}
                onChange={(_, newValue) => setSelectedLocations(newValue)}
                renderInput={(params) => (
                  <TextField {...params} label="Select Locations" margin="normal" />
                )}
              />
              
              <Button
                variant="contained"
                onClick={handleCreateSession}
                disabled={createSessionMutation.isLoading}
                sx={{ mt: 2 }}
              >
                {createSessionMutation.isLoading ? 'Creating...' : 'Create Count Session'}
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Count Sessions
              </Typography>
              
              <Box sx={{ height: 300, mt: 2 }}>
                <DataGrid
                  rows={countSessions?.data?.data || []}
                  columns={sessionColumns}
                  pageSize={5}
                  rowsPerPageOptions={[5, 10]}
                  disableSelectionOnClick
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
                  Count Session Details - {selectedSession.id}
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body1">
                    Status: <Chip label={selectedSession.status} size="small" />
                  </Typography>
                </Box>
                
                <Box sx={{ height: 400, mt: 2 }}>
                  <DataGrid
                    rows={sessionDetails?.data?.data?.details || []}
                    columns={detailColumns}
                    pageSize={10}
                    rowsPerPageOptions={[10, 25]}
                    disableSelectionOnClick
                  />
                </Box>
                
                {selectedSession.status === 'OPEN' && (
                  <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                    <Button
                      variant="contained"
                      onClick={handleEnterCounts}
                      disabled={enterCountsMutation.isLoading}
                    >
                      {enterCountsMutation.isLoading ? 'Saving...' : 'Save Counts'}
                    </Button>
                    <Button
                      variant="contained"
                      color="secondary"
                      onClick={handleApplyCounts}
                      disabled={applyCountsMutation.isLoading}
                    >
                      {applyCountsMutation.isLoading ? 'Applying...' : 'Apply Adjustments'}
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
