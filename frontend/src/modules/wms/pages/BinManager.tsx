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
        setError(error.response?.data?.message || 'Failed to search bins');
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
        alert('Label sent to printer successfully');
      },
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Failed to print label');
      },
    }
  );

  const columns: GridColDef[] = [
    { field: 'code', headerName: 'Bin Code', width: 200 },
    { field: 'name', headerName: 'Name', width: 150 },
    { field: 'type', headerName: 'Type', width: 120 },
    {
      field: 'is_active',
      headerName: 'Status',
      width: 100,
      renderCell: (params) => (
        <Chip
          label={params.value ? 'Active' : 'Inactive'}
          color={params.value ? 'success' : 'default'}
          size="small"
        />
      ),
    },
    {
      field: 'actions',
      headerName: 'Actions',
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
        Bin Manager
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Search Bins
              </Typography>
              
              <TextField
                fullWidth
                label="Search by bin code or name"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                margin="normal"
                helperText="Enter at least 3 characters to search"
              />
              
              <Box sx={{ height: 400, mt: 2 }}>
                <DataGrid
                  rows={searchResults?.data || []}
                  columns={columns}
                  loading={isLoading}
                  pageSize={10}
                  rowsPerPageOptions={[10, 25, 50]}
                  disableSelectionOnClick
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Bin Details
              </Typography>
              
              {selectedBin ? (
                <Box>
                  <Typography variant="body1" gutterBottom>
                    <strong>Code:</strong> {selectedBin.code}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>Name:</strong> {selectedBin.name || 'N/A'}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>Type:</strong> {selectedBin.type || 'N/A'}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>Section:</strong> {selectedBin.section || 'N/A'}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>Aisle:</strong> {selectedBin.aisle || 'N/A'}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>Rack:</strong> {selectedBin.rack || 'N/A'}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>Level:</strong> {selectedBin.level || 'N/A'}
                  </Typography>
                  
                  {capacityData?.data && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="h6" gutterBottom>
                        Capacity Information
                      </Typography>
                      <Typography variant="body2">
                        Capacity: {capacityData.data.capacity_qty || 'N/A'} {capacityData.data.capacity_uom || ''}
                      </Typography>
                      <Typography variant="body2">
                        Current: {capacityData.data.current_qty} ({capacityData.data.current_items} items)
                      </Typography>
                      {capacityData.data.utilization_pct && (
                        <Typography variant="body2">
                          Utilization: {capacityData.data.utilization_pct.toFixed(1)}%
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
                    Print Label
                  </Button>
                </Box>
              ) : (
                <Typography color="text.secondary">
                  Select a bin to view details
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
