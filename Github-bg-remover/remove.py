import requests
import os
from PIL import Image

def validate_image(file_path):
    try:
        if os.path.getsize(file_path) > 5 * 1024 * 1024:
            raise Exception("File too large (Max 5MB)")

        with Image.open(file_path) as img:
            img.verify()
            if img.format not in ['JPEG', 'PNG']:
                raise Exception("Invalid format")
        return True
    except Exception as e:
        raise Exception(f"invalid_image: {str(e)}")

def remove_bg(input_path, output_path):
    try:
        if not validate_image(input_path):
            raise Exception("invalid_image")

        api_key = "23fa5a7eaea439fc1c477eeaa776ed14db6b12f20569524a36ff9a3704a840a6b15619244eeac925c339a6338a5b8473"
        headers = {'x-api-key': api_key}

        # Request transparent PNG output
        params = {'format': 'png'}

        with open(input_path, 'rb') as image_file:
            response = requests.post(
                'https://clipdrop-api.co/remove-background/v1',
                files={'image_file': image_file},
                headers=headers,
                params=params,
                timeout=30
            )

        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)

            # Verify transparency
            with Image.open(output_path) as img:
                if not img.mode == 'RGBA':
                    raise Exception("No alpha channel detected")

            return output_path

        elif response.status_code == 429:
            raise Exception("api_limit: API quota exceeded")
        else:
            raise Exception(f"API Error {response.status_code}: {response.text}")

    except requests.exceptions.Timeout:
        raise Exception("API request timed out")
    except Exception as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        raise e