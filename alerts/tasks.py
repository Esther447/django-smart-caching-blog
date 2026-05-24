import threading
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def send_financing_alert(request_id):
    def _send_alert():
        logger.info(
            f"[ALERT] request_id={request_id} "
            f"status=processed "
            f"timestamp={datetime.now()}"
        )

    thread = threading.Thread(target=_send_alert)
    thread.start()
