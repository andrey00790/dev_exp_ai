# Admin Portal API

## Endpoints

### Health Check
- **GET** `/health` - Service health status

### Authentication
- **POST** `/auth/login` - User authentication
- **POST** `/auth/refresh` - Token refresh
- **GET** `/auth/me` - Current user info

### Core Operations
- **GET** `/admin_portal/` - List all items
- **POST** `/admin_portal/` - Create new item
- **GET** `/admin_portal/{id}` - Get item by ID
- **PUT** `/admin_portal/{id}` - Update item
- **DELETE** `/admin_portal/{id}` - Delete item

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
