import base64
from typing import List, Dict, Any, Optional
from io import BytesIO
from PIL import Image
import os
import re
import json
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnablePassthrough

def compress_image(image_path: str, max_size: int = 800, quality: int = 85) -> str:
    """
    Compress an image to reduce token usage while maintaining quality.
    
    Args:
        image_path: Path to the image file
        max_size: Maximum dimension (width or height) for the image
        quality: JPEG quality (1-100)
        
    Returns:
        Base64 encoded string of the compressed image
    """
    with Image.open(image_path) as img:
        # Convert to RGB if needed (removes alpha channel)
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if needed
        width, height = img.size
        if max(width, height) > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Save as JPEG to BytesIO
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)
        
        # Convert to base64
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        return img_base64

def _create_llm_client(model_name: str = "meta-llama/llama-4-scout-17b-16e-instruct", temperature: float = 0.2):
    return ChatGroq(
        model_name=model_name,
        temperature=temperature,
        max_tokens=1024,  
    )

def captions(
    image_path_or_base64: str, 
    count: int = 3, 
    model_name: str = "meta-llama/llama-4-scout-17b-16e-instruct",
) -> List[str]:
    """
    Generate captions for an image using a Groq vision model.
    
    Args:
        image_path_or_base64: Path to image file or base64 encoded image string
        count: Number of captions to generate
        model_name: Groq model name to use
        
    Returns:
        List of caption strings
    """
    # Check if input is a file path or already base64
    if os.path.isfile(image_path_or_base64):
        image_b64 = compress_image(image_path_or_base64)
    else:
        image_b64 = image_path_or_base64
    
    output_parser = JsonOutputParser(pydantic_object=type(
        "CaptionOutput",
        (),
        {"__annotations__": {"captions": List[str]}}
    ))
    
    prompt = f"""
    You are an image captioning expert. Analyze the image and provide exactly {count} distinct, creative captions for it.
    Focus on being descriptive and engaging.
    
    Respond ONLY with a JSON object containing the captions in the following format:
    {{
        "captions": ["caption 1", "caption 2", "caption 3"]
    }}
    
    Do not include any explanations, introductions, or additional text.
    """
    
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
        ]
    )
    
    llm = _create_llm_client(model_name=model_name)
    result = llm.invoke([message])
    
    try:
        parsed_output = output_parser.parse(result.content)
        return parsed_output["captions"]
    except Exception as e:
        print(f"Error parsing output: {e}")
    
        json_match = re.search(r'\{.*\}', result.content, re.DOTALL)
        if json_match:
            try:
                parsed_json = json.loads(json_match.group(0))
                if "captions" in parsed_json and isinstance(parsed_json["captions"], list):
                    return parsed_json["captions"][:count] 
            except:
                pass
        return []

def tags(
    image_path_or_base64: str, 
    count: int = 10, 
    model_name: str = "meta-llama/llama-4-scout-17b-16e-instruct"
) -> List[str]:
    """
    Generate tags for an image using a Groq vision model.
    
    Args:
        image_path_or_base64: Path to image file or base64 encoded image string
        count: Number of tags to generate
        model_name: Groq model name to use
        
    Returns:
        List of tag strings
    """
    if os.path.isfile(image_path_or_base64):
        image_b64 = compress_image(image_path_or_base64)
    else:
        image_b64 = image_path_or_base64
    
    output_parser = JsonOutputParser(pydantic_object=type(
        "TagOutput",
        (),
        {"__annotations__": {"tags": List[str]}}
    ))
    
    prompt = f"""
    You are a photo tagging specialist. Analyze the image and provide exactly {count} relevant tags.
    Focus on concrete objects, colors, themes, emotions, and photographic styles present in the image.
    Each tag should be a single word or short phrase (1-3 words maximum).
    
    Respond ONLY with a JSON object containing the tags in the following format:
    {{
        "tags": ["tag1", "tag2", "tag3", ...]
    }}
    
    Do not include any explanations, introductions, or additional text.
    """
    
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
        ]
    )
    

    llm = _create_llm_client(model_name=model_name)
    result = llm.invoke([message])

    try:
        parsed_output = output_parser.parse(result.content)
        return parsed_output["tags"]
    except Exception as e:
        print(f"Error parsing output: {e}")

        json_match = re.search(r'\{.*\}', result.content, re.DOTALL)
        if json_match:
            try:
                parsed_json = json.loads(json_match.group(0))
                if "tags" in parsed_json and isinstance(parsed_json["tags"], list):
                    return parsed_json["tags"][:count]  
            except:
                pass
        return []