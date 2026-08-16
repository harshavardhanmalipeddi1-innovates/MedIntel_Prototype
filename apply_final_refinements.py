import os
import shutil

root = r'C:\Users\harsh\.gemini\antigravity\scratch\medintel'

# Remove duplicate modules
for d in ['knowledge_base', 'reporting']:
    p = os.path.join(root, 'backend', 'app', 'modules', d)
    if os.path.exists(p):
        shutil.rmtree(p)

# Remove config JSON files from backend/app/config/
for f in ['feature_columns.json', 'disease_labels.json']:
    p = os.path.join(root, 'backend', 'app', 'config', f)
    if os.path.exists(p):
        os.remove(p)

# Place JSON files in models/xgboost/config/
xgb_config_dir = os.path.join(root, 'models', 'xgboost', 'config')
os.makedirs(xgb_config_dir, exist_ok=True)

for f in ['feature_columns.json', 'disease_labels.json', 'model_metadata.json']:
    p = os.path.join(xgb_config_dir, f)
    if not os.path.exists(p):
        with open(p, 'w') as fp:
            fp.write('{}')

print("Final refinements complete.")
