MODEL_MAPPING = {
    'gemini-3-pro':'gemini-3-pro-preview'
}

def get_model_id(model_name: str) -> str:
    return MODEL_MAPPING.get(model_name, model_name) 
