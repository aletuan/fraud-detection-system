import os
import sys
from pathlib import Path

# Add the src directory to Python path
root_dir = Path(__file__).parent
src_dir = root_dir / "src"
sys.path.append(str(src_dir)) 