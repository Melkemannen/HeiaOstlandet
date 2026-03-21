import logging
from datetime import date

from tripletex_client import TripletexClient

log = logging.getLogger(__name__)


def handle_register_hours(client: TripletexClient, fields: dict) -> None:
    employee_email = fields.get("employee_email")
    project_name = fields.get("project_name") or ""
    activity_name = fields.get("activity_name") or ""
    hours = fields.get("hours")
    entry_date = fields.get("date") or str(date.today())

    if hours is not None:
        try:
            hours = float(hours)
        except (TypeError, ValueError):
            hours = None

    # Find employee by email
    employee_id = None
    if employee_email:
        employees = client.list("/employee", params={"email": employee_email, "fields": "id,email"})
        if employees:
            employee_id = employees[0]["id"]
            log.info("Found employee id=%s", employee_id)
        else:
            log.warning("Employee not found for email: %s", employee_email)

    # Find project by name
    project_id = None
    if project_name:
        projects = client.list("/project", params={"name": project_name, "fields": "id,name", "count": 5})
        if projects:
            project_id = projects[0]["id"]
            log.info("Found project id=%s name=%s", project_id, projects[0]["name"])

    # Find activity by name
    activity_id = None
    if activity_name and project_id:
        activities = client.list("/project/activity", params={
            "projectId": project_id,
            "fields": "id,name",
            "count": 20,
        })
        for act in activities:
            if activity_name.lower() in (act.get("name") or "").lower():
                activity_id = act["id"]
                log.info("Found activity id=%s name=%s", activity_id, act["name"])
                break

    if not activity_id:
        # Try general activities
        activities = client.list("/activity", params={"name": activity_name, "fields": "id,name", "count": 5})
        if activities:
            activity_id = activities[0]["id"]
            log.info("Found general activity id=%s", activity_id)

    payload = {
        "date": entry_date,
        "hours": hours or 0,
    }
    if employee_id:
        payload["employee"] = {"id": employee_id}
    if project_id:
        payload["project"] = {"id": project_id}
    if activity_id:
        payload["activity"] = {"id": activity_id}

    result = client.post("/timesheet/entry", payload)
    log.info("Registered hours: %s", result.get("value", {}).get("id"))
