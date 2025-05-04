# Data Loading for Egypt Tourism Chatbot

This directory contains scripts for loading JSON data from the `data` directory into the PostgreSQL database.

## Overview

The data loading process involves:

1. Reading JSON files from the `data` directory
2. Processing each entity type (attractions, cities, accommodations, restaurants, etc.)
3. Generating embeddings for text fields to enable vector search
4. Inserting the data into the appropriate tables
5. Verifying the data loading

## Scripts

- `load_all_data.py`: Main script for loading all data into the database
- `verify_data_loading.py`: Script for verifying that data has been correctly loaded
- `run_data_loading.sh`: Shell script to run both loading and verification in sequence
- Other scripts: Individual data population scripts for specific entity types

## Usage

### Prerequisites

1. Make sure PostgreSQL is running and properly configured
2. Set the `POSTGRES_URI` environment variable to the PostgreSQL connection string:

```bash
export POSTGRES_URI=postgresql://postgres:postgres@localhost:5432/egypt_chatbot
```

### Running the Data Loading Process

To load all data into the database, run:

```bash
./scripts/data_population/run_data_loading.sh
```

This will:
1. Load all JSON data from the `data` directory into the database
2. Verify that the data has been correctly loaded
3. Display summary statistics for each entity type

### Running Individual Scripts

You can also run the individual scripts separately:

```bash
# Load all data
python scripts/data_population/load_all_data.py

# Verify data loading
python scripts/data_population/verify_data_loading.py
```

## Data Structure

The data loading process expects JSON files in the following directories:

- `data/attractions/`: Attraction data (historical sites, museums, etc.)
- `data/cities/`: City data (Cairo, Luxor, Aswan, etc.)
- `data/accommodations/`: Accommodation data (hotels, resorts, etc.)
- `data/restaurants/`: Restaurant data

Each JSON file should follow the schema defined in the `data/schemas/` directory.

## Embeddings

The data loading process generates embeddings for text fields to enable vector search. These embeddings are stored in the database and can be used for semantic search queries.

The embeddings are generated using the `text_to_embedding` function from `src/knowledge/database.py`, which uses the `sentence-transformers` library.

## Troubleshooting

If you encounter issues during the data loading process:

1. Check the logs for error messages
2. Verify that PostgreSQL is running and properly configured
3. Ensure that the JSON files follow the expected schema
4. Check that the required Python packages are installed:
   ```bash
   pip install sentence-transformers
   ```

## Adding New Data

To add new data:

1. Create JSON files following the schema in the appropriate directory
2. Run the data loading script to load the new data into the database

The script uses `ON CONFLICT DO UPDATE` to handle existing records, so it will update existing records and insert new ones.
