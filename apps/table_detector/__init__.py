# Client-side components for local poker detection

import os
import sys

# Add the apps directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
apps_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(apps_dir)

# Add both apps directory and project root to path
if apps_dir not in sys.path:
    sys.path.insert(0, apps_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)