# Vana Data Refinement Template

This repository serves as a template for creating Dockerized *data refinement instructions* that transform raw user data into normalized (and potentially anonymized) SQLite-compatible databases, so data in Vana can be querying by Vana's Query Engine.

## Overview

Here is an overview of the data refinement process on Vana.

![How Refinements Work](https://files.readme.io/25f8f6a4c8e785a72105d6eb012d09449f63ab5682d1f385120eaf5af871f9a2-image.png "How Refinements Work")

1. DLPs upload user-contributed data through their UI, and run proof-of-contribution against it. Afterwards, they call the refinement service to refine this data point.
1. The refinement service downloads the file from the Data Registry and decrypts it.
1. The refinement container, containing the instructions for data refinement (this repo), is executed
   1. The decrypted data is mounted to the container's `/input` directory
   1. The raw data points are transformed against a normalized SQLite database schema (specifically libSQL, a modern fork of SQLite)
   1. Optionally, PII (Personally Identifiable Information) is removed or masked
   1. The refined data is symmetrically encrypted with a derivative of the original file encryption key
1. The encrypted refined data is uploaded and pinned to a DLP-owned IPFS
1. The IPFS CID is written to the refinement container's `/output` directory
1. The CID of the file is added as a refinement under the original file in the Data Registry
1. Vana's Query Engine indexes that data point, aggregating it with all other data points of a given refiner. This allows SQL queries to run against all data of a particular refiner (schema).

## Project Structure

- `refiner/`: Contains the main refinement logic
    - `refine.py`: Core refinement implementation
    - `config.py`: Environment variables and settings needed to run your refinement
    - `__main__.py`: Entry point for the refinement execution
    - `models/`: Pydantic and SQLAlchemy data models (for both unrefined and refined data)
    - `transformer/`: Data transformation logic
    - `utils/`: Utility functions for encryption, IPFS upload, etc.
- `input/`: Contains raw data files to be refined
- `output/`: Contains refined outputs:
    - `schema.json`: Database schema definition
    - `db.libsql`: SQLite database file
    - `db.libsql.pgp`: Encrypted database file
- `Dockerfile`: Defines the container image for the refinement task
- `requirements.txt`: Python package dependencies

## Getting Started

1. Fork this repository
2. Copy `.env.example` to `.env` and modify the values to match your environment
3. Update the schemas in `refiner/models/` to define your raw and normalized data models
4. Modify the refinement logic in `refiner/transformer/` to match your data structure
5. If needed, modify `refiner/refiner.py` with your file(s) that need to be refined
6. Build and test your refinement container

### Environment variables

Copy `.env.example` to `.env` and configure the following variables:

```dotenv
# Local directories where inputs and outputs are found
# When running on the refinement service, files will be mounted to the /input and /output directory of the container
INPUT_DIR=input
OUTPUT_DIR=output

# This key is derived from the user file's original encryption key, automatically injected into the container by the refinement service
# When developing locally, any string can be used here for testing
REFINEMENT_ENCRYPTION_KEY=0x1234

# Schema configuration
SCHEMA_NAME=Nutrition
SCHEMA_VERSION=0.0.1
SCHEMA_DESCRIPTION=Schema for Population Nutrition, representing essential dietary indicators across demographics
SCHEMA_DIALECT=sqlite

# IPFS configuration
# Required if using https://pinata.cloud (IPFS pinning service)
PINATA_API_KEY=your_pinata_api_key_here
PINATA_API_SECRET=your_pinata_api_secret_here

# Public IPFS gateway URL for accessing uploaded files
# Recommended to use own dedicated IPFS gateway to avoid congestion / rate limiting
# Example: "https://ipfs.my-dao.org/ipfs" (Note: won't work for third-party files)
IPFS_GATEWAY_URL=https://gateway.pinata.cloud/ipfs
```

## Local Development

To run the refinement locally for testing:

```bash
# With Python
pip install --no-cache-dir -r requirements.txt
python -m refiner

# Or with Docker
docker build -t refiner .
docker run \
  --rm \
  --volume $(pwd)/input:/input \
  --volume $(pwd)/output:/output \
  --env PINATA_API_KEY=your_key \
  --env PINATA_API_SECRET=your_secret \
  refiner
```

## Testing

This project includes several methods for testing the data refinement process with the database:

### Manual Testing

You can run manual tests using the provided scripts:

#### Using `run_manual_test.py`

This script sets up the environment and runs the refiner with test data:

> Note: First run `python create_test_data.py` to create test data, and then `python run_manual_test.py` to run the refiner.

```bash
python run_manual_test.py
```

The script will:
1. Create input and output directories if they don't exist
2. Set environment variables for the refiner
3. Process any JSON files in the input directory
4. Output the refinement URL and database schema

#### Using `run_test.sh`

```shell
chmod +x run_test.sh
```

For a more comprehensive test that includes data generation:

```bash
./run_test.sh
```

This shell script will:
1. Generate test FHIR data using `create_test_data.py`
2. Run the refiner on the generated data
3. Display the results and any errors

### Creating Test Data

You can generate sample FHIR data for testing:

```bash
python create_test_data.py
```

This will create sample Patient and MedicationStatement resources in the input directory.

### Database Inspection

After running tests, you can inspect the SQLite database in the output directory:

```bash
sqlite3 output/refined.db
```

Common commands:
- `.tables` - List all tables
- `.schema` - Show database schema
- `SELECT * FROM patient;` - View patient data
- `SELECT * FROM medication;` - View medication data

### Troubleshooting

If you encounter database errors:
1. Check that the table names in your models match those in your transformers
2. Ensure the Base class is properly imported from the correct module
3. Verify that the database is being initialized before data insertion

## Contributing

If you have suggestions for improving this template, please open an issue or submit a pull request.

## License

[MIT License](LICENSE)

