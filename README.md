# Food Truck API

## Overview
This is a FastAPI-based REST API for managing a food truck's menu, orders, and cart. It allows users to create and manage menu items, place orders, and track order status while ensuring data validation and consistency.

## Features
- **Menu Management**: Add, update, retrieve, and delete menu items.
- **Option Management**: Add, update, retrieve, and delete options.
- **Cart Management**: Add items to cart, update quantities, and clear cart.
- **Order Management**: Create orders from cart, track order status, and process payments.
- **Validation**: Ensures data consistency and validates order status transitions.
- **MongoDB Integration**: Stores and retrieves data efficiently.
- **Testing**: Includes unit, integration, and performance tests.

## Technologies Used
- **FastAPI** (for building the REST API)
- **Pydantic** (for data validation)
- **MongoDB** (for data storage, using PyMongo)
- **pytest** (for unit and integration testing)
- **httpx** (for making API requests in tests)

---

## Installation
### 1. Clone the repository
```bash
git clone <your-repo-url>
cd <your-project-folder>
```

### 2. Create a virtual environment (optional but recommended)
```bash
python -m venv venv  # Create virtual environment
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate  # On Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up MongoDB (if not already running)
Ensure you have MongoDB installed and running locally or use a cloud MongoDB instance.
Modify `database.py` to point to your MongoDB instance if needed.

### 5. Create a `.env` file for environment variables
Create a `.env` file in the root directory and add your MongoDB URI:
```env
MONGO_URI=mongodb+srv://your_username:your_password@your_cluster.mongodb.net/your_db_name
```

### 6. Start the FastAPI server
```bash
python ./app/main.py
```

The API will be available at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

You can access interactive API docs at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Running Tests
### 1. Install testing dependencies (if not already installed)
```bash
pip install pytest pytest-mock httpx pytest-benchmark
```

### 2. Run unit and integration tests
```bash
pytest
```

### 3. Run performance tests (optional)
```bash
pytest --benchmark-only
```

---

## API Endpoints
### Menu Routes (`/menu`)
| Method | Endpoint | Description |
|--------|---------|-------------|
| `GET` | `/menu/` | Get all menu items |
| `POST` | `/menu/` | Create a new menu item |
| `GET` | `/menu/{menu_id}` | Get a specific menu item |
| `PUT` | `/menu/{menu_id}` | Update a menu item |
| `DELETE` | `/menu/{menu_id}` | Delete a menu item |

### Option Routes (`/options`)
| Method | Endpoint | Description |
|--------|---------|-------------|
| `GET` | `/options/` | Get all options |
| `POST` | `/options/` | Create a new option |
| `GET` | `/options/{option_id}` | Get a specific option |
| `PUT` | `/options/{option_id}` | Update an option |
| `DELETE` | `/options/{option_id}` | Delete an option |

### Cart Routes (`/cart`)
| Method | Endpoint | Description |
|--------|---------|-------------|
| `GET` | `/cart/` | Get current cart |
| `POST` | `/cart/items` | Add item to cart |
| `PUT` | `/cart/items/{item_id}` | Update cart item |
| `DELETE` | `/cart/items/{item_id}` | Remove item from cart |
| `POST` | `/cart/clear` | Clear entire cart |

### Order Routes (`/orders`)
| Method | Endpoint | Description |
|--------|---------|-------------|
| `GET` | `/orders/` | Get all orders |
| `POST` | `/orders/` | Create order from cart |
| `GET` | `/orders/order/{order_number}` | Get order by number |
| `PUT` | `/orders/{order_id}/status` | Update order status |
| `POST` | `/orders/{order_id}/cancel` | Cancel order |
| `POST` | `/orders/{order_id}/pay` | Process payment |

#### Order Status Flow
1. `PENDING` - Initial state when order is created
2. `IN_PREPARATION` - After payment is processed
3. `READY` - When food is prepared
4. `DELIVERED` - When order is picked up
5. `CANCELLED` - If order is cancelled (only possible from `PENDING` state)

---

## Contributing
Feel free to open issues or submit pull requests to improve this project!

---

## License
MIT License

