import requests
from datetime import datetime

# Replace with your Helius API key
API_KEY = "666cfff9-f65d-4e9e-8074-3614dc816a68"

# The token mint address of the Solana token
TOKEN_MINT = "9hjZ8UTNrNWt3YUTHVpvzdQjNbp64NbKSDsbLqKR6BZc"

# The date you want to check the holders for (in UTC)
date_to_check = "2023-10-01"

# Convert the date to a Unix timestamp
date_obj = datetime.strptime(date_to_check, "%Y-%m-%d")
timestamp = int(date_obj.timestamp())

def get_historical_token_holders(api_key, token_mint, timestamp):
    url = f"https://api.helius.xyz/v0/addresses/{token_mint}/holders"
    
    params = {
        "api-key": api_key,
        "timestamp": timestamp  # Pass the timestamp of the desired date
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        holders = response.json()
        print("Token holders on the specified date:")
        for holder in holders:
            print(f"Address: {holder['address']}, Balance: {holder['balance']}")
    else:
        print(f"Failed to retrieve token holders. Status code: {response.status_code}")
        print(response.text)

# Call the function with the API key, token mint address, and timestamp
get_historical_token_holders(API_KEY, TOKEN_MINT, timestamp)
