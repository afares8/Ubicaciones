# WMS Bin-Locations Inventory System

A comprehensive Warehouse Management System (WMS) for bin location tracking and inventory management, integrated with SAP Business One 9.3 PL5 via DI API.

## Architecture

- **Frontend**: React + TypeScript SPA with Material-UI
- **Backend**: FastAPI with SQLAlchemy + Alembic migrations
- **SAP Integration**: C# Windows Service using SAP DI API (SAPbobsCOM)
- **Database**: SQL Server with dedicated `wms` schema
- **Authentication**: JWT-based with role-based access control
- **Label Printing**: ZPL generation with PrintNode integration

## Features

### Warehouse Structure Management
- Hierarchical location structure: Section → Aisle → Rack → Level → Bin
- Bulk location generation with pattern support
- Location attributes and capacity management
- ZPL label generation and printing
- **Multi-language Support**: Complete Spanish interface (Sistema de Inventario por Ubicaciones)

### Stock Management
- Real-time stock tracking by location
- Lot/serial number support
- Stock queries by location, item, or summary
- Low stock alerts and capacity utilization

### Warehouse Operations
- **Put-away**: Receive items into specific bin locations
- **Internal Moves**: Move stock between bins within same warehouse
- **Cross-Warehouse Transfers**: Transfer stock between warehouses (creates SAP Stock Transfer)
- **Issue/Receipt**: Issue stock for consumption or receive additional stock
- **Cycle Counts**: Physical inventory counting with SAP adjustments

### SAP Integration
- Good Receipt documents for stock receipts
- Good Issue documents for stock issues
- Inventory Transfer documents for cross-warehouse moves
- Automatic lot/serial assignment for managed items
- Comprehensive error handling and retry logic

### Audit & Compliance
- Complete audit trail for all operations
- User activity logging with timestamps
- Idempotent API operations
- Role-based access control (Admin, WarehouseManager, Operator, Auditor)

## Quick Start

### Prerequisites
- SQL Server (for database)
- SAP Business One 9.3 PL5 with DI API installed
- Node.js 16+ (for frontend)
- Python 3.12+ (for backend)
- .NET Framework 4.8 (for SAP DI service)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database and SAP connection details
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### SAP DI Service Setup
```bash
cd sap-di-service
# Build the C# project (ensure x86/x64 matches your SAP DI API installation)
# Configure environment variables for SAP connection
# Run as Windows Service or console application
```

## Environment Variables

### Backend (.env)
```
SAP_DB_HOST=localhost
SAP_DB_PORT=1433
SAP_DB_NAME=SBODemoUS
SAP_DB_USER=sa
SAP_DB_PASSWORD=your_password
JWT_SECRET=your-secret-key
SAP_DI_BASE_URL=http://localhost:8001
PRINTNODE_API_KEY=your_printnode_key
```

### SAP DI Service
```
SAP_DI_SERVER=localhost
SAP_COMPANY_DB=SBODemoUS
SAP_USERNAME=manager
SAP_PASSWORD=your_sap_password
SAP_DI_HOST=localhost
SAP_DI_PORT=8001
```

## API Documentation

The FastAPI backend provides comprehensive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

#### Locations
- `POST /api/v1/wms/warehouses/{whs}/locations/bulk-generate` - Bulk generate locations
- `GET /api/v1/wms/warehouses/{whs}/locations` - List locations
- `PUT /api/v1/wms/locations/{locationId}` - Update location

#### Stock
- `GET /api/v1/wms/stock/by-location/{locationId}` - Stock by location
- `GET /api/v1/wms/stock/by-item` - Stock by item across locations
- `GET /api/v1/wms/stock/summary` - Stock summary for reconciliation

#### Operations
- `POST /api/v1/wms/operations/putaway` - Put-away operation
- `POST /api/v1/wms/operations/move-internal` - Internal move
- `POST /api/v1/wms/operations/transfer-warehouse` - Cross-warehouse transfer
- `POST /api/v1/wms/operations/issue` - Issue stock

#### Cycle Counts
- `POST /api/v1/wms/counts` - Create count session
- `PUT /api/v1/wms/counts/{id}/enter` - Enter counted quantities
- `POST /api/v1/wms/counts/{id}/apply` - Apply count adjustments

#### Labels
- `POST /api/v1/wms/locations/{locationId}/label` - Generate and print label
- `GET /api/v1/wms/labels/preview/{locationId}` - Preview label

## Business Rules

### Location Codes
- Support ranged tokens: `SEC{01-03}-AIS{01-10}-RK{01-05}-LV{01-04}-BIN{01-30}`
- Unique within warehouse
- Hierarchical structure maintained

### Stock Movement Rules
- Internal moves within same warehouse: No SAP document created
- Cross-warehouse transfers: Always create SAP Inventory Transfer
- Cycle count adjustments: Create SAP Good Issue/Receipt as needed
- FIFO policy by default, FEFO if expiry dates exist

### Concurrency Control
- Optimistic concurrency with conditional updates
- Stock updates use `WHERE qty >= :quantity` to prevent overselling
- Idempotency keys prevent duplicate operations

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### API Integration Tests
```bash
# Test all endpoints with authentication
pytest tests/test_api_integration.py
```

### SAP DI Service Tests
```bash
# Test against staging SAP database
# Verify Good Receipt, Good Issue, and Transfer operations
```

## Deployment

### Production Deployment
- Backend: Docker container with FastAPI
- Frontend: Static build served by Nginx
- SAP DI Service: Windows Service on SAP server
- Database: SQL Server with proper indexing

### Docker Support
```bash
# Backend
docker build -t wms-backend ./backend
docker run -p 8000:8000 wms-backend

# Frontend
docker build -t wms-frontend ./frontend
docker run -p 3000:3000 wms-frontend
```

## Security

### Authentication
- JWT tokens with configurable expiration
- Role-based access control
- Secure password handling

### Roles & Permissions
- **Admin**: Full system access
- **WarehouseManager**: Warehouse operations, cycle counts, transfers
- **Operator**: Daily operations (put-away, moves, picking)
- **Auditor**: Read-only access to audit trails

### Data Protection
- All sensitive data encrypted in transit
- Audit logging for compliance
- No direct SAP database writes

## Monitoring & Maintenance

### Health Checks
- Backend: `GET /health`
- SAP DI Service: `GET /health`
- Database connectivity monitoring

### Logging
- Structured logging with timestamps
- Audit trail for all operations
- Error tracking and alerting

### Performance
- Database indexes for optimal query performance
- Connection pooling for SAP DI API
- Caching for frequently accessed data

## Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review audit logs for operation history
3. Verify SAP connection status via health endpoints
4. Check database connectivity and schema

## License

This project is proprietary software developed for warehouse management operations.
