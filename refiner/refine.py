import json
import logging
import os
from typing import List

from refiner.models.fihr import MedicationDB, PatientDB
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
        output = Output()

        transformer = FHIRTransformer(self.db_path)
        session = transformer.Session()  # Usa la sesión creada por DataTransformer

        for input_filename in os.listdir(settings.INPUT_DIR):
            input_file = os.path.join(settings.INPUT_DIR, input_filename)
            if os.path.splitext(input_file)[1].lower() == '.json':
                with open(input_file, 'r') as f:
                    input_data = json.load(f)

                    # --- Soporte para Bundle ---
                    resources = []
                    if isinstance(input_data, dict) and input_data.get("resourceType") == "Bundle":
                        for entry in input_data.get("entry", []):
                            if "resource" in entry:
                                resources.append(entry["resource"])
                    elif isinstance(input_data, list):
                        resources = input_data
                    else:
                        resources = [input_data]
                    # --- Fin soporte Bundle ---

                    for resource in resources:
                        models = transformer.transform(resource)
                        for model in models:
                            # Evita duplicados de PatientDB
                            if isinstance(model, PatientDB):
                                exists = session.query(PatientDB).filter_by(id=model.id).first()
                                if not exists:
                                    session.add(model)
                            # Evita duplicados de MedicationDB
                            elif isinstance(model, MedicationDB):
                                exists = session.query(MedicationDB).filter_by(id=model.id).first()
                                if not exists:
                                    session.add(model)
                            else:
                                session.add(model)
                    session.commit()
                    logging.info(f"Transformed {input_filename}")

                    schema = OffChainSchema(
                        name=settings.SCHEMA_NAME,
                        version=settings.SCHEMA_VERSION,
                        description=settings.SCHEMA_DESCRIPTION,
                        dialect=settings.SCHEMA_DIALECT,
                        schema=transformer.get_schema() if hasattr(transformer, "get_schema") else ""
                    )
                    output.schema_content = schema

                    schema_file = os.path.join(settings.OUTPUT_DIR, 'schema.json')
                    with open(schema_file, 'w') as f:
                        json.dump(schema.model_dump(), f, indent=4)
                        schema_ipfs_hash = upload_json_to_ipfs(schema.model_dump())
                        logging.info(f"Schema uploaded to IPFS with hash: {schema_ipfs_hash}")

                    encrypted_path = encrypt_file(settings.REFINEMENT_ENCRYPTION_KEY, self.db_path)
                    ipfs_hash = upload_file_to_ipfs(encrypted_path)
                    output.refinement_url = f"{settings.IPFS_GATEWAY_URL}/{ipfs_hash}"
                    continue

        session.close()
        logging.info("Data transformation completed successfully")
        return output