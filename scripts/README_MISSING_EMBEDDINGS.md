# Missing Embeddings Generation

This directory contains scripts to identify, generate, and update missing embeddings in the Egypt Tourism Chatbot database.

## Purpose

These scripts address Phase 6.1 of the database migration plan:
- Identify records with missing embeddings across all tables
- Generate embeddings using the same model as existing ones
- Update records with the new embeddings
- Verify that all records have embeddings after the update

## Scripts

- `generate_missing_embeddings.py`: Python script to identify, generate, and update missing embeddings
- `generate_missing_embeddings.sh`: Shell script to run the Python script with validation
- `migrations/20250627_generate_missing_embeddings.sql`: SQL migration script to track the change

## Usage

### Prerequisites

Make sure you have the following installed:
- Python 3.8+
- PostgreSQL client
- Required Python packages: `psycopg2`, `numpy`, `python-dotenv`

### Environment Variables

Create a `.env` file with the following variables:

```
POSTGRES_DB=egypt_chatbot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### Running the Scripts

1. Make the scripts executable:
   ```
   chmod +x scripts/generate_missing_embeddings.py scripts/generate_missing_embeddings.sh
   ```

2. Run the shell script:
   ```
   ./scripts/generate_missing_embeddings.sh
   ```

   This will:
   - First run in dry-run mode to identify missing embeddings
   - Ask for confirmation before proceeding
   - Generate and update embeddings
   - Verify that all embeddings have been generated

3. Alternatively, you can run the Python script directly:
   ```
   # Dry run (identify missing embeddings without updating)
   python3 scripts/generate_missing_embeddings.py --dry-run

   # Generate and update embeddings
   python3 scripts/generate_missing_embeddings.py

   # Process only a specific table
   python3 scripts/generate_missing_embeddings.py --table practical_info
   ```

## Implementation Details

### Embedding Generation

In the current implementation, the script generates random embeddings of the correct dimension (1536) as placeholders. In a production environment, you would replace this with a call to an embedding model API, such as OpenAI's text-embedding-ada-002.

To use a real embedding model, modify the `generate_embedding` function in `generate_missing_embeddings.py`:

```python
def generate_embedding(text: str, dimension: int) -> List[float]:
    """Generate an embedding for the given text."""
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(input=text, model="text-embedding-ada-002")
    embedding = response.data[0].embedding
    return embedding
```

### Tables with Embeddings

The script processes the following tables:
- attractions
- accommodations
- cities
- restaurants
- destinations
- tourism_faqs
- practical_info
- tour_packages
- events_festivals
- itineraries

### Verification

After generating embeddings, the script verifies that all records have embeddings by:
- Counting the total number of records in each table
- Counting the number of records with embeddings
- Calculating the coverage percentage

## Logs

The script generates a log file with a timestamp:
- `embedding_generation_YYYYMMDD_HHMMSS.log`

Check this log for detailed information about the process and any issues encountered.
