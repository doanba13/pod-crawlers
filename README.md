# Print-on-Demand Order Crawler

This project crawls order data from multiple print-on-demand platforms (Printful, Printify, and Burger Prints) and saves them in a standardized JSON format.

## Features

- Fetches orders from multiple print-on-demand platforms
- Standardizes order data across different platforms
- Saves orders in JSON format organized by date and platform
- Runs automatically on a daily schedule
- Handles errors gracefully

## Project Structure

```
.
├── crawlers/
│   ├── base.py
│   ├── printful.py
│   ├── printify.py
│   └── burger_prints.py
├── models/
│   └── order.py
├── storage/
│   └── order_storage.py
├── jobs/
│   └── crawl_orders.py
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your API tokens:
   ```bash
   cp .env.example .env
   ```
4. Edit the `.env` file with your API tokens and desired storage path

## Configuration

The following environment variables are required:

- `PRINTFUL_API_TOKEN`: Your Printful API token
- `PRINTIFY_API_TOKEN`: Your Printify API token
- `BURGER_PRINTS_API_TOKEN`: Your Burger Prints API token
- `STORAGE_PATH`: Path where order data will be stored (default: ./data/orders)

## Usage

Run the crawler:

```bash
python jobs/crawl_orders.py
```

The script will:

1. Run immediately when started
2. Schedule itself to run daily at 1 AM
3. Save orders in JSON files organized by platform and date

## Data Format

Orders are saved in the following structure:

```
data/
└── orders/
    ├── printful/
    │   └── 2024-03-26.json
    ├── printify/
    │   └── 2024-03-26.json
    └── burger_prints/
        └── 2024-03-26.json
```

Each JSON file contains an array of standardized order objects with the following structure:

```json
{
  "platform": "string",
  "order_id": "string",
  "order_date": "datetime",
  "customer": {
    "name": "string",
    "email": "string",
    "address": "string",
    "city": "string",
    "country": "string",
    "zip_code": "string"
  },
  "items": [
    {
      "product_name": "string",
      "quantity": "integer",
      "price": "float",
      "variant": "string",
      "size": "string",
      "color": "string"
    }
  ],
  "subtotal": "float",
  "shipping_cost": "float",
  "total_cost": "float",
  "status": "string",
  "tracking_number": "string",
  "raw_data": "object"
}
```

## Notes

- For Printify, you need to set your shop ID in the code before fetching orders
- The script runs daily at 1 AM by default
- Orders are saved in JSON format for easy processing and analysis
- The original raw data from each platform is preserved in the `raw_data` field
- "final_price" -> price that POD platform charge us 😡
