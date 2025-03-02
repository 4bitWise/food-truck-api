# Food Truck API

## Overview
This is a FastAPI-based REST API for managing a food truck's menu, orders, and cart. It allows users to create and manage menu items, place orders with customizable options, and track order status while ensuring data validation and consistency.

## Features
- **Menu Management**: Add, update, retrieve, and delete menu items with customizable options
- **Option Management**: Add, update, retrieve, and delete options that can be added to menu items
- **Cart Management**: Add items to cart, customize with available options, update quantities, and clear cart
- **Order Management**: Create orders from cart, track order status, and process payments
- **Validation**: Ensures data consistency, validates order status transitions, and verifies option availability
- **MongoDB Integration**: Stores and retrieves data efficiently using PyMongo
- **Testing**: Comprehensive unit tests with pytest using mock collections

## Technologies Used
- **FastAPI**: Web framework for building APIs
- **Pydantic**: Data validation using Python type annotations
- **MongoDB**: Database (via PyMongo)
- **pytest**: Testing framework
- **Python 3.8+**: Core programming language

## Installation

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd food-truck-api
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
venv\Scripts\activate     # On Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure MongoDB
Create a `.env` file in the root directory:
```env
MONGO_URI=mongodb://localhost:27017/food_truck
```

### 5. Start the server
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

### Menu Routes (`/menu`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/menu/` | List all menu items |
| POST | `/menu/` | Create a menu item |
| GET | `/menu/{item_id}` | Get a specific menu item |
| PUT | `/menu/{item_id}` | Update a menu item |
| DELETE | `/menu/{item_id}` | Delete a menu item |

### Options Routes (`/options`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/options/` | List all options |
| POST | `/options/` | Create an option |
| GET | `/options/{option_id}` | Get a specific option |
| PUT | `/options/{option_id}` | Update an option |
| DELETE | `/options/{option_id}` | Delete an option |

### Cart Routes (`/cart`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cart/` | Get current cart |
| POST | `/cart/items` | Add item to cart |
| PUT | `/cart/items/{item_id}` | Update cart item |
| DELETE | `/cart/items/{item_id}` | Remove item from cart |
| DELETE | `/cart/` | Clear cart |

### Order Routes (`/orders`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/orders/` | List all orders |
| POST | `/orders/` | Create order from cart |
| GET | `/orders/{order_id}` | Get order by ID |
| PUT | `/orders/{order_id}/status` | Update order status |
| POST | `/orders/{order_id}/cancel` | Cancel order |
| POST | `/orders/{order_id}/pay` | Process payment |

## Order Status Flow
Orders follow this status progression:
1. `pending` - Initial state when order is created
2. `en préparation` - After payment is processed
3. `prête` - When order is ready for pickup
4. `livrée` - When order is delivered
5. `annulée` - When order is cancelled

Status Transition Rules:
- Orders can only be cancelled when in `pending` state
- Payment changes status from `pending` to `en préparation`
- Status must follow the sequence: pending → en préparation → prête → livrée
- Cancelled orders cannot be modified further

## Data Models

### Menu Item
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "price": 0.00,
  "category": "string",
  "options": ["string"],
  "available": true
}
```

### Option
```json
{
  "id": "string",
  "name": "string",
  "price": 0.00
}
```

### Cart Item
```json
{
  "menu_item_id": "string",
  "quantity": 1,
  "selected_options": ["string"],
  "special_instructions": "string",
  "total_price": 0.00
}
```

### Order
```json
{
  "id": "string",
  "order_number": "FT-YYYY-NNNN",
  "items": [CartItem],
  "total_amount": 0.00,
  "status": "pending",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Price Calculation
- Item total = (base price + sum of option prices) × quantity
- Cart/Order total = sum of all item totals
- All calculations are performed server-side
- Prices are validated against current menu and option prices

## Testing
Run the test suite:
```bash
pytest app/tests -v
```

The test suite includes:
- Unit tests for all routes
- Mock MongoDB collections for testing
- Status transition validation
- Price calculation verification
- Error handling scenarios

## Error Handling
The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request (invalid data/status)
- 404: Not Found
- 500: Server Error

Validation errors include detailed messages about the specific issue.

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
MIT License

