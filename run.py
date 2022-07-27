import os
from app import app

DEBUG = bool(os.environ.get("DEBUG", 1))
# Launch the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    app.run(host="0.0.0.0", port=port, debug=DEBUG)
