import os
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
import json

# Define Pydantic models for structured output parsing
class TagsOutput(BaseModel):
    tags: List[str] = Field(description="List of relevant tags for the image")

class CaptionOutput(BaseModel):
    caption: str = Field(description="A descriptive caption for the image")

def suggest_captions(image_path: str) -> str:
    """
    Generate a descriptive caption for an image using Google's Gemini Vision model.
    
    :param image_path: Path to the image file
    :return: A descriptive caption string
    """
    # Initialize the vision model
    model = ChatGoogleGenerativeAI(
        model="gemini-pro-vision",
        convert_system_message_to_human=True,
        google_api_key=os.environ.get("GOOGLE_API_KEY")
    )
    
    # Load the image
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    # Create an efficient prompt template focused on caption generation
    caption_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a professional photography caption generator. 
        Generate ONE concise, descriptive caption for this image. 
        The caption should be 1-2 sentences maximum.
        Focus on the main subject, mood, and setting.
        DO NOT include tags or labels.
        DO NOT include introductory phrases like 'This image shows' or 'This is a picture of'.
        DO NOT explain your reasoning."""),
        ("human", {"content": [
            {"type": "text", "text": "Generate a caption for this image:"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ]})
    ])
    
    # Create the output parser
    parser = JsonOutputParser(pydantic_object=CaptionOutput)
    
    # Create the LangChain Expression Language (LCEL) chain
    chain = caption_prompt | model | parser
    
    try:
        # Run the chain
        response = chain.invoke({})
        return response.caption
    except Exception as e:
        print(f"Caption generation failed: {e}")
        return "A photograph."  # Fallback caption


def suggest_tags(image_path: str, top_k: int = 10) -> List[str]:
    """
    Generate relevant tags for an image using Google's Gemini Vision model.
    
    :param image_path: Path to the image file
    :param top_k: Number of suggestions to return
    :return: List of suggested tag strings
    """
    # Initialize the vision model
    model = ChatGoogleGenerativeAI(
        model="gemini-pro-vision",
        convert_system_message_to_human=True,
        google_api_key=os.environ.get("GOOGLE_API_KEY")
    )
    
    # Load the image
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    # Create an efficient prompt template focused on tag generation
    tag_prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a professional photography tag generator.
        Generate exactly {top_k} relevant tags for this image.
        Tags should be single words or short phrases (1-3 words maximum).
        Include tags for subject, style, mood, colors, composition, and technical aspects.
        Format your response as a JSON object with a single key 'tags' containing an array of strings.
        DO NOT include explanations or descriptions.
        DO NOT include numbered lists.
        DO NOT include any other text beyond the JSON object."""),
        ("human", {"content": [
            {"type": "text", "text": "Generate tags for this image:"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
        ]})
    ])
    
    # Create the output parser
    parser = JsonOutputParser(pydantic_object=TagsOutput)
    
    # Create the LCEL chain
    chain = tag_prompt | model | parser
    
    try:
        # Run the chain
        response = chain.invoke({})
        return response.tags[:top_k]  # Ensure we don't exceed top_k
    except Exception as e:
        print(f"Tag suggestion failed: {e}")
        # Fallback tags for demo purposes
        return ["photography", "image", "photo"]