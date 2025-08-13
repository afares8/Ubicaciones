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
        setError(error.response?.data?.message || 'Error al cargar ubicaciones');
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
        alert(`Se crearon exitosamente ${response.data.data.created} ubicaciones`);
      },
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Error al generar ubicaciones');
      },
    }
  );

  const handleBulkGenerate = () => {
    let parsedAttributes;
    try {
      parsedAttributes = attributes ? JSON.parse(attributes) : undefined;
    } catch (e) {
      setError('JSON inválido en el campo de atributos');
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
        Diseñador de Almacén
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Generador Masivo de Ubicaciones
              </Typography>
              
              <TextField
                fullWidth
                label="Patrón"
                value={pattern}
                onChange={(e) => setPattern(e.target.value)}
                margin="normal"
                helperText="Ejemplo: SEC{01-03}-PAS{01-10}-EST{01-05}-NIV{01-04}-UBI{01-30}"
              />
              
              <FormControl fullWidth margin="normal">
                <InputLabel>Tipo de Ubicación</InputLabel>
                <Select
                  value={locationType}
                  onChange={(e) => setLocationType(e.target.value)}
                >
                  <MenuItem value="Recepción">Recepción</MenuItem>
                  <MenuItem value="Almacenamiento">Almacenamiento</MenuItem>
                  <MenuItem value="Picking">Picking</MenuItem>
                  <MenuItem value="Devoluciones">Devoluciones</MenuItem>
                  <MenuItem value="Cuarentena">Cuarentena</MenuItem>
                </Select>
              </FormControl>
              
              <TextField
                fullWidth
                label="Atributos (JSON)"
                value={attributes}
                onChange={(e) => setAttributes(e.target.value)}
                margin="normal"
                multiline
                rows={3}
                helperText='Ejemplo: {"temp": "ambiente", "zona": "A"}'
              />
              
              <Button
                variant="contained"
                onClick={handleBulkGenerate}
                disabled={bulkGenerateMutation.isLoading}
                sx={{ mt: 2 }}
              >
                {bulkGenerateMutation.isLoading ? 'Generando...' : 'Generar Ubicaciones'}
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Ubicaciones Actuales ({locations?.data?.length || 0})
              </Typography>
              
              {isLoading ? (
                <Typography>Cargando ubicaciones...</Typography>
              ) : (
                <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                  {locations?.data?.map((location: any) => (
                    <Paper key={location.id} sx={{ p: 1, mb: 1 }}>
                      <Typography variant="body2">
                        <strong>{location.code}</strong> - {location.name || 'Sin nombre'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Tipo: {location.type || 'N/A'} | Activo: {location.is_active ? 'Sí' : 'No'}
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
