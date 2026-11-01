"""Offline source-level validation for the ARCHDS final package."""
from pathlib import Path
import ast

root=Path(__file__).resolve().parents[1]
python_files=list((root/'ai-service'/'app').rglob('*.py'))
for p in python_files:
    ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
required=[
    root/'frontend/src/App.jsx', root/'frontend/src/services/api.js',
    root/'frontend/src/App.css', root/'ai-service/app/diagram.py',
    root/'ai-service/app/report.py', root/'ai-service/app/main.py',
    root/'backend/src/main/java/com/vit/archds/controller/AdvisorController.java'
]
missing=[str(p) for p in required if not p.exists()]
if missing: raise SystemExit('Missing required files: '+', '.join(missing))
app=(root/'frontend/src/App.jsx').read_text(encoding='utf-8')
for token in ['function ArchitectureAdvisor','tab===\'advisor\'','Digital Twin','Delivery']:
    if token not in app: raise SystemExit('Missing UI feature: '+token)
print(f'Python syntax: {len(python_files)} files OK')
print('Required final surfaces: OK')
print('Architecture Advisor: OK')
print('Digital Twin and Delivery surfaces: OK')
