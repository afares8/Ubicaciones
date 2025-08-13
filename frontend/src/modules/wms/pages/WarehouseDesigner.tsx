import React, { useState } from 'react';
import {
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  Alert,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { wmsApi } from '../api/wms';
import { useWMSStore } from '../store/wms';

const WarehouseDesigner: React.FC = () => {
  const { selectedWarehouse, setError, clearError } = useWMSStore();
  const queryClient = useQueryClient();
  
  const [pattern, setPattern] = useState('SEC{01-03}-AIS{01-10}-RK{01-05}-LV{01-04}-BIN{01-30}');
  const [locationType, setLocationType] = useState('Storage');
  const [attributes, setAttributes] = useState('{"temp": "ambient"}');

  const { data: locations, isLoading } = useQuery(
    ['locations', selectedWarehouse],
    () => wmsApi.locations.getByWarehouse(selectedWarehouse),
    {
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Failed to load locations');
      },
    }
  );

  const bulkGenerateMutation = useMutation(
    (data: { pattern: string; type: string; attributes?: any }) =>
      wmsApi.locations.bulkGenerate(selectedWarehouse, data),
    {
      onSuccess: (response) => {
        clearError();
        queryClient.invalidateQueries(['locations', selectedWarehouse]);
        alert(`Successfully created ${response.data.data.created} locations`);
      },
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Failed to generate locations');
      },
    }
  );

  const handleBulkGenerate = () => {
    let parsedAttributes;
    try {
      parsedAttributes = attributes ? JSON.parse(attributes) : undefined;
    } catch (e) {
      setError('Invalid JSON in attributes field');
      return;
    }

    bulkGenerateMutation.mutate({
      pattern,
      type: locationType,
      attributes: parsedAttributes,
    });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Warehouse Designer
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Bulk Location Generator
              </Typography>
              
              <TextField
                fullWidth
                label="Pattern"
                value={pattern}
                onChange={(e) => setPattern(e.target.value)}
                margin="normal"
                helperText="Example: SEC{01-03}-AIS{01-10}-RK{01-05}-LV{01-04}-BIN{01-30}"
              />
              
              <FormControl fullWidth margin="normal">
                <InputLabel>Location Type</InputLabel>
                <Select
                  value={locationType}
                  onChange={(e) => setLocationType(e.target.value)}
                >
                  <MenuItem value="Receiving">Receiving</MenuItem>
                  <MenuItem value="Storage">Storage</MenuItem>
                  <MenuItem value="Picking">Picking</MenuItem>
                  <MenuItem value="Returns">Returns</MenuItem>
                  <MenuItem value="Quarantine">Quarantine</MenuItem>
                </Select>
              </FormControl>
              
              <TextField
                fullWidth
                label="Attributes (JSON)"
                value={attributes}
                onChange={(e) => setAttributes(e.target.value)}
                margin="normal"
                multiline
                rows={3}
                helperText='Example: {"temp": "ambient", "zone": "A"}'
              />
              
              <Button
                variant="contained"
                onClick={handleBulkGenerate}
                disabled={bulkGenerateMutation.isLoading}
                sx={{ mt: 2 }}
              >
                {bulkGenerateMutation.isLoading ? 'Generating...' : 'Generate Locations'}
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Current Locations ({locations?.data?.length || 0})
              </Typography>
              
              {isLoading ? (
                <Typography>Loading locations...</Typography>
              ) : (
                <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                  {locations?.data?.map((location: any) => (
                    <Paper key={location.id} sx={{ p: 1, mb: 1 }}>
                      <Typography variant="body2">
                        <strong>{location.code}</strong> - {location.name || 'No name'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Type: {location.type || 'N/A'} | Active: {location.is_active ? 'Yes' : 'No'}
                      </Typography>
                    </Paper>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default WarehouseDesigner;
