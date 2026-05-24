import threading
import logging

logger = logging.getLogger(__name__)

def _send_alert(request_id):
    logger.info(f"[ALERT] Financing request {request_id} processed")

def send_financing_alert(request_id):
    thread = threading.Thread(target=_send_alert, args=(request_id,))
    thread.start()
