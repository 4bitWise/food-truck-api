# Food Truck API

## Overview
This is a FastAPI-based REST API for managing a food truck's menu and options. It allows users to create, update, retrieve, and delete menu items and options while ensuring data validation and consistency.

## Features
- **Menu Management**: Add, update, retrieve, and delete menu items.
- **Option Management**: Add, update, retrieve, and delete options.
- **Validation**: Ensures unique names and verifies the existence of options before associating them with menu items.
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

---

## Contributing
Feel free to open issues or submit pull requests to improve this project!

---

## License
MIT License

