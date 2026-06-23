with open("tests/templates/test_feature_map.py", "r") as f:
    content = f.read()

content = content.replace("from src.templates.feature_map import (", "from typing import Any\n\nfrom src.templates.feature_map import (")

with open("tests/templates/test_feature_map.py", "w") as f:
    f.write(content)
