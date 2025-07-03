# Payment Service API

## Endpoints

### Health Check
- **GET** `/health` - Service health status

### Authentication
- **POST** `/auth/login` - User authentication
- **POST** `/auth/refresh` - Token refresh
- **GET** `/auth/me` - Current user info

### Core Operations
- **GET** `/payment_service/` - List all items
- **POST** `/payment_service/` - Create new item
- **GET** `/payment_service/{id}` - Get item by ID
- **PUT** `/payment_service/{id}` - Update item
- **DELETE** `/payment_service/{id}` - Delete item

## Response Format
```json
{
  "status": "success|error",
  "data": {},
  "message": "Optional message",
  "timestamp": "2024-06-10T10:00:00Z"
}
```

## Error Codes
- 400: Bad Request
- 401: Unauthorized  
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error
