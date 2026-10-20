# Copies Metadata/project_settings.config out of a project saved by Bambu Studio
# into bambu/project_settings.config, the template the build scripts write into
# their 3MFs. Usage: update_template.py <saved project .3mf>
import json
import sys
import zipfile
from pathlib import Path

src = sys.argv[1]
data = zipfile.ZipFile(src).read("Metadata/project_settings.config")
config = json.loads(data)
out = Path(__file__).resolve().parent / "project_settings.config"
out.write_bytes(data)
print(f"{out}: {config['printer_settings_id']}, {config['print_settings_id']}, "
      f"filaments {config['filament_settings_id']}, saved by Bambu Studio {config['version']}")
