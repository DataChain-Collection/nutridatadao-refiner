import json
import logging
import os

from refiner.models.offchain_schema import OffChainSchema
from refiner.models.output import Output
from refiner.transformer.fhir_transformer import FHIRTransformer
from refiner.config import settings
from refiner.utils.encrypt import encrypt_file
from refiner.utils.ipfs import upload_file_to_ipfs, upload_json_to_ipfs


class Refiner:
    def __init__(self):
        self.db_path = os.path.join(settings.OUTPUT_DIR, 'db.libsql')

    def transform(self) -> Output:
        """Transform all input files into the database."""
        logging.info("Starting data transformation")

        # Initialize transformer
        transformer = FHIRTransformer(self.db_path)
        all_resources = []

        # Create output directory if it does not exist
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

        # Set to track IDs of already processed resources
        processed_resource_ids = set()

        # Process all files in the input directory
        for filename in os.listdir(settings.INPUT_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(settings.INPUT_DIR, filename)
                logging.info(f"Processing file: {file_path}")

                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)

                    # Handle both single resources and bundles
                    if isinstance(data, dict):
                        if data.get('resourceType') == 'Bundle':
                            # Process each entry in the bundle
                            for entry in data.get('entry', []):
                                if 'resource' in entry and isinstance(entry['resource'], dict):
                                    resource = entry['resource']
                                    resource_id = f"{resource.get('resourceType')}/{resource.get('id')}"

                                    # Skip if we've already processed this resource
                                    if resource_id in processed_resource_ids:
                                        logging.info(f"Skipping duplicate resource: {resource_id}")
                                        continue

                                    all_resources.append(resource)
                                    processed_resource_ids.add(resource_id)
                        else:
                            # Single resource
                            resource_id = f"{data.get('resourceType')}/{data.get('id')}"

                            # Skip if we've already processed this resource
                            if resource_id in processed_resource_ids:
                                logging.info(f"Skipping duplicate resource: {resource_id}")
                                continue

                            all_resources.append(data)
                            processed_resource_ids.add(resource_id)
                except Exception as e:
                    logging.error(f"Error processing file {file_path}: {e}")
                    continue

        # Process all collected resources
        if all_resources:
            transformer.process(all_resources)
            logging.info(f"Transformed {len(all_resources)} resources")
        else:
            logging.warning("No valid FHIR resources found to process")

        # Get the database schema
        schema_data = transformer.get_schema()

        # Create schema based on FHIR schema
        schema = OffChainSchema(
            name=settings.SCHEMA_NAME,
            version=settings.SCHEMA_VERSION,
            description=settings.SCHEMA_DESCRIPTION,
            dialect=settings.SCHEMA_DIALECT,
            tables=schema_data["tables"],
            relationships=schema_data["relationships"]
        )

        # Save schematic to file
        schema_file = os.path.join(settings.OUTPUT_DIR, 'schema.json')
        with open(schema_file, 'w') as f:
            json.dump(schema.model_dump(), f, indent=4)

        # Upload schema to IPFS
        schema_ipfs_hash = upload_json_to_ipfs(schema.model_dump())
        logging.info(f"Schema uploaded to IPFS with hash: {schema_ipfs_hash}")

        # Encrypt and upload database to IPFS
        encrypted_path = encrypt_file(settings.REFINEMENT_ENCRYPTION_KEY, self.db_path)
        ipfs_hash = upload_file_to_ipfs(encrypted_path)
        refinement_url = f"{settings.IPFS_GATEWAY_URL}/{ipfs_hash}"

        # Create output object
        output = Output(
            refinement_url=refinement_url,
            schema=schema
        )

        # Create output.json file
        output_file = os.path.join(settings.OUTPUT_DIR, 'output.json')
        with open(output_file, 'w') as f:
            json.dump({
                "refinement_url": refinement_url,
                "schema": schema.model_dump()
            }, f, indent=4)

        logging.info("Data transformation completed successfully")
        return output
