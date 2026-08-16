import os

root = r'C:\Users\harsh\.gemini\antigravity\scratch\medintel'

dirs = [
    'models/xgboost/artifacts',
    'models/xgboost/config',
    'models/xgboost/metadata',
    'models/xgboost/evaluation',
    'models/xgboost/training',
    'models/vertex_ai/configs',
    'models/vertex_ai/prompts',
    'backend/app/modules/investigation_engine',
    'backend/app/modules/report_engine',
    'backend/app/modules/knowledge_base',
    'frontend/src/assets/icons',
    'frontend/src/assets/images',
    'frontend/src/assets/logos',
    'frontend/src/assets/themes',
    'frontend/src/components/ui',
    'frontend/src/components/layout',
    'frontend/src/components/forms',
    'frontend/src/components/clinical',
    'knowledge_base/referral_criteria',
    'prompts/doctor_summary',
    'prompts/missing_information'
]

files = [
    'backend/app/config/feature_columns.json',
    'backend/app/config/disease_labels.json',
    'docs/database.md',
    'docs/clinical_workflow.md',
    'docs/data_dictionary.md',
    'specs/MASTER_BLUEPRINT.md'
]

for d in dirs:
    path = os.path.join(root, d)
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, '.gitkeep'), 'w') as f:
        f.write('# placeholder')

for file in files:
    filepath = os.path.join(root, file)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            f.write('')

print("Refinement completed.")
