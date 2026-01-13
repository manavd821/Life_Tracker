# Create
## POST /api/v1/tasks

# Read
## GET /api/v1/tasks?date=YYYY-MM-DD
## GET /api/v1/tasks/{task_id}
## GET /api/v1/tasks?status={}

# Update
## PATCH /api/v1/tasks/{task_id} -> meta data only
## POST /api/v1/tasks/{task_id}/complete -> Confirm task completion and optionally log behavior
## PATCH /api/v1/tasks/{task_id}/undo-complete -> also handle the logic to remove associate behavior that exists

# Delete
## DELETE /api/v1/tasks/{task_id} // if status is pending or undue