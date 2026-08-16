import os

root = r'C:\Users\harsh\.gemini\antigravity\scratch\medintel'

dirs = [
    '.github/workflows',
    '.github/ISSUE_TEMPLATE',
    'backend/app/api/v1/endpoints',
    'backend/app/core',
    'backend/app/db/migrations',
    'backend/app/models',
    'backend/app/schemas',
    'backend/app/services',
    'backend/app/utils',
    'backend/tests',
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
    'models/xgboost/artifacts',
    'models/xgboost/config',
    'models/vertex_ai/medgemma_config',
    'datasets/raw',
    'datasets/processed',
    'datasets/synthetic',
    'knowledge_base/guidelines',
    'knowledge_base/ontologies',
    'knowledge_base/vector_store',
    'prompts/clinical_summarization',
    'prompts/diagnosis_support',
    'prompts/treatment_recommendation',
    'specs/openapi',
    'specs/fhir_specs',
    'tests/unit/backend',
    'tests/unit/frontend',
    'tests/integration',
    'tests/e2e',
    'deployment/docker',
    'deployment/kubernetes',
    'deployment/terraform',
    'scripts/data_pipeline',
    'scripts/model_training',
    'docs/architecture',
    'docs/compliance',
    'docs/api',
    'notebooks/eda',
    'notebooks/model_experiments'
]

files = [
    '.env.example',
    '.gitignore',
    'docker-compose.yml',
    'LICENSE',
    'requirements.txt',
    'backend/Dockerfile',
    'backend/requirements.txt',
    'backend/app/main.py',
    'frontend/Dockerfile',
    'frontend/package.json',
    'frontend/tsconfig.json'
]

for d in dirs:
    path = os.path.join(root, d)
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, '.gitkeep'), 'w') as f:
        pass

for file in files:
    filepath = os.path.join(root, file)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            pass

print("Structure created successfully.")
