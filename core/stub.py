import json
import logging
import pprint
from typing import Any, Dict, List, Literal, Tuple

import requests

from core.remote import Remote
from openfabric_pysdk.helper import has_resource_fields, json_schema_to_marshmallow, resolve_resources
from openfabric_pysdk.loader import OutputSchemaInst

# Type aliases for clarity
Manifests = Dict[str, dict]
Schemas = Dict[str, Tuple[dict, dict]]
Connections = Dict[str, Remote]


class Stub:

    # ----------------------------------------------------------------------
    def __init__(self, app_ids: List[str]):
        self._schema: Schemas = {}
        self._manifest: Manifests = {}
        self._connections: Connections = {}

        for app_id in app_ids:
            base_url = app_id.strip('/')

            try:
                # Fetch manifest
                manifest = requests.get(f"https://{base_url}/manifest", timeout=5).json()
                logging.info(f"[{app_id}] Manifest loaded")
                self._manifest[app_id] = manifest

                # Fetch input schema
                input_schema = requests.get(f"https://{base_url}/schema?type=input", timeout=5).json()
                logging.info(f"[{app_id}] Input schema loaded")

                # Fetch output schema
                output_schema = requests.get(f"https://{base_url}/schema?type=output", timeout=5).json()
                logging.info(f"[{app_id}] Output schema loaded")
                self._schema[app_id] = (input_schema, output_schema)

                # Establish Remote WebSocket connection
                self._connections[app_id] = Remote(f"wss://{base_url}/app", f"{app_id}-proxy").connect()
                logging.info(f"[{app_id}] Connection established")
            except Exception as e:
                logging.error(f"[{app_id}] Initialization failed: {e}")

    # ----------------------------------------------------------------------
    def call(self, app_id: str, data: Any, uid: str = 'super-user') -> dict:

        connection = self._connections.get(app_id)
        if not connection:
            raise Exception(f"Connection not found for app ID: {app_id}")

        try:
            handler = connection.execute(data, uid)
            result = connection.get_response(handler)

            schema = self.schema(app_id, 'output')
            marshmallow = json_schema_to_marshmallow(schema)
            handle_resources = has_resource_fields(marshmallow())

            if handle_resources:
                try:
                    resource_url = "https://" + app_id + "/resource?reid={reid}"
                    result = resolve_resources(resource_url, result, marshmallow())
                except Exception as e:
                    logging.warning(f"[{app_id}] Error resolving resources: {e}")
                    if "Resource not found" in str(e):
                        logging.info(f"[{app_id}] Continuing with result despite resource not found error")
                    else:
                        raise

            return result
        except Exception as e:
            logging.error(f"[{app_id}] Execution failed: {e}")

    # ----------------------------------------------------------------------
    def manifest(self, app_id: str) -> dict:
        return self._manifest.get(app_id, {})

    # ----------------------------------------------------------------------
    def schema(self, app_id: str, type: Literal['input', 'output']) -> dict:
        _input, _output = self._schema.get(app_id, (None, None))

        if type == 'input':
            if _input is None:
                raise ValueError(f"Input schema not found for app ID: {app_id}")
            return _input
        elif type == 'output':
            if _output is None:
                raise ValueError(f"Output schema not found for app ID: {app_id}")
            return _output
        else:
            raise ValueError("Type must be either 'input' or 'output'")
