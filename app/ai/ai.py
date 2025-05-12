"""
Photo Tagger and Captioner

This script uses LangChain with Google's Generative AI (Gemini) to analyze photos,
generate relevant tags, and suggest captions.
"""

import os
from typing import Dict, List, Tuple
from PIL import Image
import io
import base64

# LangChain imports
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain.chains import create_extraction_chain, create_structured_output_chain
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.pydantic_v1 import BaseModel, Field

# Google Generative AI
from langchain_google_genai import ChatGoogleGenerativeAI

class PhotoAnalysis(BaseModel):
    """Schema for the photo analysis output."""
    tags: List[str] = Field(description="List of 10 relevant and specific tags for the photo")
    captions: List[str] = Field(description="List of 3 creative and engaging captions for the photo")

def load_image_as_base64(image_path: str) -> str:
    """
    Load an image from path and convert to base64 string.
    """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def process_image(image_path: str) -> Dict:
    """
    Process an image to return a format that can be passed to the LLM.
    """
    if image_path.startswith("http"):
        # For URLs, we'll just pass the URL directly
        return {"image_input": {"image_url": image_path}}
    else:
        # For local files, convert to base64
        return {"image_input": {"image_data": load_image_as_base64(image_path)}}

def create_photo_tagger_captioner(api_key: str, model_name: str = "gemini-1.5-pro"):
    """
    Creates a pipeline for photo tagging and captioning using LangChain and Google Generative AI.
    
    Args:
        api_key: Google API key
        model_name: Google Generative AI model name
    
    Returns:
        A runnable pipeline that takes an image path and returns tags and captions
    """
    # Initialize the Google Generative AI model with vision capabilities
    llm = ChatGoogleGenerativeAI(
        google_api_key=api_key,
        model=model_name,
        temperature=0.7,
        convert_system_message_to_human=True
    )
    
    # Create a prompt for tag and caption generation
    tag_caption_system_prompt = """
    You are an expert photo analyzer that generates tags and captions for images.
    
    Given an image, you must:
    1. Generate exactly 10 relevant, specific, and diverse tags that accurately describe the content, objects, 
       scenes, emotions, colors, and themes present in the image.
    2. Create 3 engaging, creative captions that could be used for posting this image on social media.
    
    Your output should be formatted as JSON with 'tags' and 'captions' fields.
    
    Tags should be single words or short phrases (1-3 words), separated by commas.
    Captions should be complete, engaging sentences with proper punctuation.
    
    Focus solely on the image content - do not make assumptions beyond what is visible.
    """
    
    # Create the LCEL pipeline
    image_processor = RunnableLambda(process_image)
    
    # Create a prompt template that includes the image
    prompt = ChatPromptTemplate.from_messages([
        ("system", tag_caption_system_prompt),
        MessagesPlaceholder(variable_name="image_input"),
        ("human", "Generate tags and captions for this image in JSON format.")
    ])
    
    # Create the extraction chain for structured output
    chain = (
        {"image_input": image_processor} 
        | prompt 
        | llm 
        | StrOutputParser() 
        | JsonOutputParser()  # Parse the JSON response
    )
    
    return chain

def analyze_photo(image_path: str, api_key: str) -> Tuple[List[str], List[str]]:
    """
    Analyze a photo to generate tags and captions.
    
    Args:
        image_path: Path to the image file or URL
        api_key: Google API key
    
    Returns:
        A tuple of (tags, captions)
    """
    # Create the photo analyzer pipeline
    photo_analyzer = create_photo_tagger_captioner(api_key)
    
    # Run the analyzer on the image
    try:
        result = photo_analyzer.invoke(image_path)
        tags = result.get("tags", [])
        captions = result.get("captions", [])
        return tags, captions
    except Exception as e:
        print(f"Error analyzing photo: {e}")
        return [], []

def main():
    """
    Main function to demonstrate the photo tagger and captioner.
    """
    # Get API key from environment variable
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Please set the GOOGLE_API_KEY environment variable")
        return
    
    # Example image path (update with your image path)
    image_path = "path/to/your/image.jpg"
    
    # Analyze the photo
    tags, captions = analyze_photo(image_path, api_key)
    
    # Print the results
    print("Tags:")
    for i, tag in enumerate(tags, 1):
        print(f"{i}. {tag}")
    
    print("\nCaptions:")
    for i, caption in enumerate(captions, 1):
        print(f"{i}. {caption}")

if __name__ == "__main__":
    main()