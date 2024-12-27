import os
import pandas as pd
from pathlib import Path
from .model_loader import load_model
from .responder import generate_response
from PIL import Image

def validate_image(image_path):
    try:
        with Image.open(image_path) as img:
            return True
    except:
        return False

def generate_descriptions(input_path, output_dir, prompt, llm_client=['qwen', 'gemini', 'openai', 'llama-vision', 'molmo', 'pixtral']):
    # Convert paths to Path objects for better handling
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    
    # Create output directory for descriptions
    desc_dir = output_dir / 'descriptions'
    desc_dir.mkdir(parents=True, exist_ok=True)
    
    # Get image paths
    if input_path.is_file():
        image_paths = [input_path]
    else:
        image_paths = [
            p for p in input_path.glob('*') 
            if p.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']
        ]
    
    results = []
    
    for img_path in image_paths:
        if not validate_image(img_path):
            print(f"Skipping invalid image: {img_path}")
            continue
            
        for model in llm_client:
            try:
                # Convert path to string for model processing
                img_path_str = str(img_path)
                response = generate_response([img_path_str], prompt, model_choice=model)
                results.append({
                    'image_path': img_path_str,
                    'model': model,
                    'response': response
                })
                print(f"Processed {img_path} with {model}")
            except Exception as e:
                print(f"Error processing {img_path} with {model}: {str(e)}")
                results.append({
                    'image_path': str(img_path),
                    'model': model,
                    'response': f"ERROR: {str(e)}"
                })
    
    # Save results
    if results:
        df = pd.DataFrame(results)
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        csv_path = desc_dir / f'responses_{timestamp}.csv'
        df.to_csv(csv_path, index=False)
        print(f"Results saved to {csv_path}")
    else:
        print("No results to save")