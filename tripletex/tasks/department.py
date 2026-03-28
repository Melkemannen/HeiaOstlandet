import logging

from tripletex_client import TripletexClient

log = logging.getLogger(__name__)


def handle_create_department(client: TripletexClient, fields: dict) -> None:
    name = fields.get("name") or ""
    department = client.create_department(name=name)
    log.info("Created department id=%s name=%s", department["id"], department["name"])
