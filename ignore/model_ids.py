import requests

def get_model_ids(api_url):
    try:
        # Send a GET request to the specified URL
        response = requests.get(api_url)
        
        # Check if the response status code indicates success
        if response.status_code == 200:
            data = response.json()  # Parse the JSON response
            # Extract and return the model IDs
            model_ids = [model["id"] for model in data.get("data", [])]
            return model_ids
        else:
            # If the request failed, return an error message
            return f"Error: Received status code {response.status_code} from API."
    except Exception as e:
        # Handle any exceptions that occur during the request
        return f"An error occurred: {e}"

# Example usage
api_url = "https://api.red-pill.ai/v1/models"
model_ids = get_model_ids(api_url)
print(model_ids)
