import logging
from typing import Optional, Union

from openfabric_pysdk.helper import Proxy
from openfabric_pysdk.helper.proxy import ExecutionResult


class Remote:

    # ----------------------------------------------------------------------
    def __init__(self, proxy_url: str, proxy_tag: Optional[str] = None):
        self.proxy_url = proxy_url
        self.proxy_tag = proxy_tag
        self.client: Optional[Proxy] = None

    # ----------------------------------------------------------------------
    def connect(self) -> 'Remote':
        logging.info(f"Connecting to proxy at {self.proxy_url}")
        self.client = Proxy(self.proxy_url, self.proxy_tag, ssl_verify=False)
        return self

    # ----------------------------------------------------------------------
    def execute(self, inputs: dict, uid: str) -> Union[ExecutionResult, None]:
        if self.client is None:
            logging.error(f"Cannot execute request: client not connected")
            return None

        result = self.client.request(inputs, uid)
        return result

    # ----------------------------------------------------------------------
    @staticmethod
    def get_response(output: ExecutionResult) -> Union[dict, None]:
        if output is None:
            logging.error("Cannot get response: execution result is None")
            return None

        output.wait()
        status = str(output.status()).lower()
        
        if status == "completed":
            return output.data()
        if status in ("cancelled", "failed"):
            error_msg = f"The request to the proxy app failed or was cancelled!"
            logging.error(error_msg)
            raise Exception(error_msg)
        
        logging.warning(f"Execution returned unknown status: {status}")
        return None

    # ----------------------------------------------------------------------
    def execute_sync(self, inputs: dict, configs: dict, uid: str) -> Union[dict, None]:
        if self.client is None:
            logging.error(f"Cannot execute sync request: client not connected")
            return None

        output = self.client.execute(inputs, configs, uid)
        return Remote.get_response(output)
