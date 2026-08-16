import os
import shutil

root = r'C:\Users\harsh\.gemini\antigravity\scratch\medintel'

# Clean old subdirectories
dirs_to_clean = [
    'backend', 'frontend', 'models', 'datasets', 'knowledge_base',
    'prompts', 'specs', 'tests', 'deployment', 'scripts', 'docs', 'notebooks', '.github'
]

for d in dirs_to_clean:
    p = os.path.join(root, d)
    if os.path.exists(p):
        shutil.rmtree(p)

dirs = [
    '.github/workflows',
    'backend/app/api/v1/endpoints',
    'backend/app/config',
    'backend/app/db/migrations',
    'backend/app/ml',
    'backend/app/modules/authentication',
    'backend/app/modules/patient_management',
    'backend/app/modules/clinical_assessment',
    'backend/app/modules/prediction_engine',
    'backend/app/modules/knowledge_engine',
    'backend/app/modules/reasoning_engine',
    'backend/app/modules/reporting',
    'frontend/public',
    'frontend/src/assets',
    'frontend/src/components/common',
    'frontend/src/components/clinical',
    'frontend/src/context',
    'frontend/src/hooks',
    'frontend/src/pages',
    'frontend/src/services',
    'frontend/src/types',
    'frontend/src/utils',
    'models/xgboost',
    'models/vertex_ai',
    'datasets/raw',
    'datasets/processed',
    'knowledge_base/diseases',
    'knowledge_base/symptoms',
    'knowledge_base/physical_exam',
    'knowledge_base/investigations',
    'knowledge_base/lab_tests',
    'knowledge_base/imaging',
    'knowledge_base/red_flags',
    'knowledge_base/medications',
    'knowledge_base/physiotherapy',
    'knowledge_base/clinical_guidelines',
    'knowledge_base/followup',
    'prompts/compare',
    'prompts/reasoning',
    'prompts/investigations',
    'prompts/treatment',
    'prompts/physiotherapy',
    'prompts/report',
    'prompts/followup',
    'prompts/red_flags',
    'prompts/patient_summary',
    'specs/openapi',
    'tests/unit',
    'tests/integration',
    'deployment/docker',
    'scripts/data_pipeline',
    'scripts/model_training',
    'docs',
    'notebooks'
]

files = [
    'backend/app/config/settings.py',
    'backend/app/config/constants.py',
    'backend/app/config/feature_mapping.py',
    'backend/app/config/disease_mapping.py',
    'backend/app/config/logging.py',
    'backend/app/ml/feature_builder.py',
    'backend/app/ml/preprocessing.py',
    'backend/app/ml/model_loader.py',
    'backend/app/ml/predictor.py',
    'backend/app/ml/postprocessing.py',
    '.github/workflows/ci.yml'
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
            f.write('# placeholder')

print("MVP Structure aligned.")
