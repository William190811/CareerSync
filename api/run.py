import os

import uvicorn

uvicorn.run("api.app:app", host="0.0.0.0", port=int(os.getenv("DATABRICKS_APP_PORT", "8001")))
