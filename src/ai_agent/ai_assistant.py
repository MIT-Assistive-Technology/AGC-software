import os
import base64
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

def encode_image(image_path):
    """Encode image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def is_image_file(file_path):
    """Check if the file is an image."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    return Path(file_path).suffix.lower() in image_extensions

def find_image_in_folder(filename, images_folder="images"):
    """Find an image file in the images folder by filename."""
    # Get the script directory
    script_dir = Path(__file__).parent
    images_path = script_dir / images_folder

    # Create images folder if it doesn't exist
    images_path.mkdir(exist_ok=True)

    # Try exact match first
    potential_path = images_path / filename
    if potential_path.exists() and is_image_file(str(potential_path)):
        return str(potential_path)

    # Try adding common extensions if no extension provided
    if not Path(filename).suffix:
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
            potential_path = images_path / (filename + ext)
            if potential_path.exists():
                return str(potential_path)

    # Search for partial matches (case-insensitive)
    if images_path.exists():
        for file in images_path.iterdir():
            if file.is_file() and is_image_file(str(file)):
                if filename.lower() in file.name.lower():
                    return str(file)

    return None

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Initialize the OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your OpenAI API key.")
        return

    client = OpenAI(api_key=api_key)

    # Initialize conversation history
    conversation_history = []
    system_message = {"role": "system", "content": "You are a helpful assistant with vision capabilities. You can analyze images and answer questions about them. IMPORTANT: For numeric answers, provide only the number without explanation.Keep all responses extremely short."}

    print("AI Assistant with Vision (type 'exit' to quit)")
    print("Usage:")
    print("  - Text only: Just type your question")
    print("  - With image: image:filename.png your question here")
    print("  - Example: image:screenshot.png how much stamina does my character have?")
    print("  - Type 'clear' to reset conversation history")
    print("-" * 70)

    while True:
        # Get user input
        user_input = input("\nYou: ").strip()

        # Exit condition
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break

        # Clear history command
        if user_input.lower() == 'clear':
            conversation_history = []
            print("\n[Conversation history cleared]")
            continue

        if not user_input:
            continue

        try:
            # Check if input contains an image reference
            image_path = None
            text_prompt = user_input

            # Parse image reference if provided (format: image:filename.png question here)
            if "image:" in user_input:
                parts = user_input.split("image:", 1)
                if len(parts) == 2:
                    # Extract everything after "image:"
                    after_image = parts[1].strip()

                    # Check if there's text before "image:"
                    before_text = parts[0].strip()

                    # Split the filename and question
                    # Look for the first space after a potential filename
                    tokens = after_image.split(None, 1)
                    filename = tokens[0] if tokens else after_image
                    question = tokens[1] if len(tokens) > 1 else ""

                    # Try to find the image in the images folder
                    found_path = find_image_in_folder(filename)

                    if found_path:
                        image_path = found_path
                        # Combine any text before and after the image reference
                        text_prompt = before_text + (" " + question if question else "")
                        text_prompt = text_prompt.strip() or "What's in this image?"
                    else:
                        # If not found in images folder, treat as full path
                        # Try to find where the file path ends by looking for extensions
                        possible_path = after_image
                        additional_text = ""

                        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.JPG', '.JPEG', '.PNG', '.GIF', '.BMP', '.WEBP']:
                            if ext in after_image:
                                ext_pos = after_image.find(ext)
                                if ext_pos != -1:
                                    possible_path = after_image[:ext_pos + len(ext)]
                                    additional_text = after_image[ext_pos + len(ext):].strip()
                                    break

                        if os.path.exists(possible_path):
                            image_path = possible_path
                            text_prompt = before_text + (" " + additional_text if additional_text else "")
                            text_prompt = text_prompt.strip() or "What's in this image?"
                        else:
                            print(f"\n[Error: Image '{filename}' not found in images folder]")
                            print("[Tip: Place your images in the 'images' folder or use a full path]")
                            continue

            # Build the message content
            if image_path and os.path.exists(image_path) and is_image_file(image_path):
                # Use vision model for images
                base64_image = encode_image(image_path)

                # Determine the image format
                image_format = Path(image_path).suffix.lower().replace('.', '')
                if image_format == 'jpg':
                    image_format = 'jpeg'

                # Create user message with image
                user_message = {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image_format};base64,{base64_image}",
                                "detail": "high"  # Use high detail for better analysis of specific parts #TODO: is this causing delay?
                            }
                        }
                    ]
                }

                # Build messages with history (vision models don't always support system messages with images)
                messages = [system_message] + conversation_history + [user_message] #TODO: Ensure that this doesn't mean lag after multiple queries
                model = "gpt-4o-mini"  # Vision-capable model
                print(f"\n[Processing image: {Path(image_path).name}]")
                print(f"[Question: {text_prompt}]")
            else:
                # Use regular text model
                user_message = {"role": "user", "content": text_prompt}
                messages = [system_message] + conversation_history + [user_message]
                model = "gpt-3.5-turbo"

                if image_path:
                    print(f"\n[Warning: Image not found or invalid: {image_path}]")

            # Call the OpenAI API
            response = client.chat.completions.create(
                model=model,
                messages=messages
            )

            # Print the response
            ai_response = response.choices[0].message.content
            print("\nAI:", ai_response)

            # Add to conversation history
            # For images, store a text-only version in history to avoid token limits
            if image_path: #TODO: look into how much the abridged text version contains
                conversation_history.append({"role": "user", "content": f"[Image: {Path(image_path).name}] {text_prompt}"})
            else:
                conversation_history.append({"role": "user", "content": text_prompt})

            conversation_history.append({"role": "assistant", "content": ai_response})

            # Keep history manageable (last 10 exchanges = 20 messages)
            if len(conversation_history) > 20: #TODO: ok, here's our answer to the questions above, but is it better to summarize or something else? how can we mark critical prompts to not forget?
                conversation_history = conversation_history[-20:]

        except Exception as e:
            print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
