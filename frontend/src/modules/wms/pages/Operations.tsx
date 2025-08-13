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
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { wmsApi } from '../api/wms';
import { useWMSStore } from '../store/wms';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`operations-tabpanel-${index}`}
      aria-labelledby={`operations-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Operations: React.FC = () => {
  const { selectedWarehouse, setError, clearError } = useWMSStore();
  const queryClient = useQueryClient();
  const [tabValue, setTabValue] = useState(0);
  
  const [putawayData, setPutawayData] = useState({
    item: '',
    lot: '',
    qty: 0,
    toLocation: null as any,
  });
  
  const [moveData, setMoveData] = useState({
    item: '',
    lot: '',
    qty: 0,
    fromLocation: null as any,
    toLocation: null as any,
  });
  
  const [transferData, setTransferData] = useState({
    fromWhs: selectedWarehouse,
    toWhs: '',
    item: '',
    lot: '',
    qty: 0,
    fromLocation: null as any,
    toLocation: null as any,
  });

  const { data: locations } = useQuery(
    ['locations', selectedWarehouse],
    () => wmsApi.locations.getByWarehouse(selectedWarehouse),
    {
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Failed to load locations');
      },
    }
  );

  const putawayMutation = useMutation(
    (data: any) => wmsApi.movements.putaway(data),
    {
      onSuccess: () => {
        clearError();
        alert('Put-away operation completed successfully');
        setPutawayData({ item: '', lot: '', qty: 0, toLocation: null });
        queryClient.invalidateQueries(['stock-by-location']);
      },
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Put-away operation failed');
      },
    }
  );

  const moveInternalMutation = useMutation(
    (data: any) => wmsApi.movements.moveInternal(data),
    {
      onSuccess: () => {
        clearError();
        alert('Internal move completed successfully');
        setMoveData({ item: '', lot: '', qty: 0, fromLocation: null, toLocation: null });
        queryClient.invalidateQueries(['stock-by-location']);
      },
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Internal move failed');
      },
    }
  );

  const transferWarehouseMutation = useMutation(
    (data: any) => wmsApi.movements.transferWarehouse(data),
    {
      onSuccess: () => {
        clearError();
        alert('Warehouse transfer completed successfully');
        setTransferData({ fromWhs: selectedWarehouse, toWhs: '', item: '', lot: '', qty: 0, fromLocation: null, toLocation: null });
        queryClient.invalidateQueries(['stock-by-location']);
      },
      onError: (error: any) => {
        setError(error.response?.data?.message || 'Warehouse transfer failed');
      },
    }
  );

  const handlePutaway = () => {
    if (!putawayData.item || !putawayData.toLocation || putawayData.qty <= 0) {
      setError('Please fill in all required fields');
      return;
    }

    putawayMutation.mutate({
      whs: selectedWarehouse,
      lines: [{
        item: putawayData.item,
        lot: putawayData.lot || undefined,
        qty: putawayData.qty,
        toLocationId: putawayData.toLocation.id,
      }],
    });
  };

  const handleInternalMove = () => {
    if (!moveData.item || !moveData.fromLocation || !moveData.toLocation || moveData.qty <= 0) {
      setError('Please fill in all required fields');
      return;
    }

    moveInternalMutation.mutate({
      whs: selectedWarehouse,
      moves: [{
        item: moveData.item,
        lot: moveData.lot || undefined,
        qty: moveData.qty,
        fromLocationId: moveData.fromLocation.id,
        toLocationId: moveData.toLocation.id,
      }],
    });
  };

  const handleWarehouseTransfer = () => {
    if (!transferData.item || !transferData.fromLocation || !transferData.toLocation || 
        !transferData.toWhs || transferData.qty <= 0) {
      setError('Please fill in all required fields');
      return;
    }

    transferWarehouseMutation.mutate({
      fromWhs: transferData.fromWhs,
      toWhs: transferData.toWhs,
      moves: [{
        item: transferData.item,
        lot: transferData.lot || undefined,
        qty: transferData.qty,
        fromLocationId: transferData.fromLocation.id,
        toLocationId: transferData.toLocation.id,
      }],
      sap: { createTransfer: true },
    });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Warehouse Operations
      </Typography>
      
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
            <Tab label="Put-away" />
            <Tab label="Internal Move" />
            <Tab label="Warehouse Transfer" />
          </Tabs>
        </Box>
        
        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" gutterBottom>
            Put-away Operation
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Item Code"
                value={putawayData.item}
                onChange={(e) => setPutawayData({ ...putawayData, item: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Lot/Serial (Optional)"
                value={putawayData.lot}
                onChange={(e) => setPutawayData({ ...putawayData, lot: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="Quantity"
                type="number"
                value={putawayData.qty}
                onChange={(e) => setPutawayData({ ...putawayData, qty: Number(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <Autocomplete
                options={locations?.data || []}
                getOptionLabel={(option) => `${option.code} - ${option.name || 'No name'}`}
                value={putawayData.toLocation}
                onChange={(_, newValue) => setPutawayData({ ...putawayData, toLocation: newValue })}
                renderInput={(params) => <TextField {...params} label="To Location" />}
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                onClick={handlePutaway}
                disabled={putawayMutation.isLoading}
              >
                {putawayMutation.isLoading ? 'Processing...' : 'Execute Put-away'}
              </Button>
            </Grid>
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom>
            Internal Move Operation
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="Item Code"
                value={moveData.item}
                onChange={(e) => setMoveData({ ...moveData, item: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="Lot/Serial (Optional)"
                value={moveData.lot}
                onChange={(e) => setMoveData({ ...moveData, lot: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={1}>
              <TextField
                fullWidth
                label="Quantity"
                type="number"
                value={moveData.qty}
                onChange={(e) => setMoveData({ ...moveData, qty: Number(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <Autocomplete
                options={locations?.data || []}
                getOptionLabel={(option) => `${option.code} - ${option.name || 'No name'}`}
                value={moveData.fromLocation}
                onChange={(_, newValue) => setMoveData({ ...moveData, fromLocation: newValue })}
                renderInput={(params) => <TextField {...params} label="From Location" />}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <Autocomplete
                options={locations?.data || []}
                getOptionLabel={(option) => `${option.code} - ${option.name || 'No name'}`}
                value={moveData.toLocation}
                onChange={(_, newValue) => setMoveData({ ...moveData, toLocation: newValue })}
                renderInput={(params) => <TextField {...params} label="To Location" />}
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                onClick={handleInternalMove}
                disabled={moveInternalMutation.isLoading}
              >
                {moveInternalMutation.isLoading ? 'Processing...' : 'Execute Internal Move'}
              </Button>
            </Grid>
          </Grid>
        </TabPanel>
        
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Warehouse Transfer Operation
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="From Warehouse"
                value={transferData.fromWhs}
                onChange={(e) => setTransferData({ ...transferData, fromWhs: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="To Warehouse"
                value={transferData.toWhs}
                onChange={(e) => setTransferData({ ...transferData, toWhs: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="Item Code"
                value={transferData.item}
                onChange={(e) => setTransferData({ ...transferData, item: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="Lot/Serial (Optional)"
                value={transferData.lot}
                onChange={(e) => setTransferData({ ...transferData, lot: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={1}>
              <TextField
                fullWidth
                label="Quantity"
                type="number"
                value={transferData.qty}
                onChange={(e) => setTransferData({ ...transferData, qty: Number(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <Autocomplete
                options={locations?.data || []}
                getOptionLabel={(option) => `${option.code} - ${option.name || 'No name'}`}
                value={transferData.fromLocation}
                onChange={(_, newValue) => setTransferData({ ...transferData, fromLocation: newValue })}
                renderInput={(params) => <TextField {...params} label="From Location" />}
              />
            </Grid>
            <Grid item xs={12}>
              <Button
                variant="contained"
                onClick={handleWarehouseTransfer}
                disabled={transferWarehouseMutation.isLoading}
              >
                {transferWarehouseMutation.isLoading ? 'Processing...' : 'Execute Warehouse Transfer'}
              </Button>
            </Grid>
          </Grid>
        </TabPanel>
      </Card>
    </Box>
  );
};

export default Operations;
