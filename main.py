from fastapi import FastAPI, BackgroundTasks, HTTPException, Header, Depends
from pydantic import BaseModel
import requests
import queue
import threading
import time
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict

# Create the FastAPI app
app = FastAPI()

# Set up CORS middleware
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define a dictionary to store separate queues for each bot token
message_queues = defaultdict(queue.Queue)

# Define the message model for the POST request
class Message(BaseModel):
    chat_id: str
    message: str
    buttons: list[dict]  # List of buttons with {"text": "Button Label", "url": "https://example.com"}

# Function to send messages using Telegram Bot API
def send_message_with_url_buttons(bot_token, chat_id, message, buttons):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    
    # Construct the inline keyboard
    inline_keyboard = [[{"text": btn["text"], "url": btn["url"]}] for btn in buttons]

    # Payload for the API request
    payload = {
        'chat_id': chat_id,
        'text': message,
        'reply_markup': {
            'inline_keyboard': inline_keyboard
        }
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        print(payload)
        print('Message with URL buttons sent successfully!')
    else:
        print(f'Failed to send message. Status code: {response.status_code}')
        print(response.text)

# Background task to process the queue for each bot token
def message_sender_worker(bot_token):
    queue_for_bot = message_queues[bot_token]
    while True:
        if not queue_for_bot.empty():
            task = queue_for_bot.get()
            try:
                send_message_with_url_buttons(
                    task["bot_token"],
                    task["chat_id"],
                    task["message"],
                    task["buttons"]
                )
                time.sleep(0.1)  # Sleep for 0.1 seconds to comply with rate limit (10 messages per second)
            except Exception as e:
                print(f"Error sending message for bot {bot_token}: {e}")
            finally:
                queue_for_bot.task_done()
        else:
            time.sleep(0.5)

# Function to start a worker thread for each new bot token
def start_worker_for_bot(bot_token):
    if bot_token not in message_queues:
        # Start a new worker thread for this bot token
        threading.Thread(target=message_sender_worker, args=(bot_token,), daemon=True).start()

# FastAPI endpoint to send a message
@app.post("/send_message/")
async def send_message_endpoint(msg: Message, x_bot_token: str = Header(...)):
    # Ensure the worker for this bot token is running
    start_worker_for_bot(x_bot_token)

    # Add the message to the queue for the specific bot token
    task = {
        "bot_token": x_bot_token,
        "chat_id": msg.chat_id,
        "message": msg.message,
        "buttons": msg.buttons
    }
    message_queues[x_bot_token].put(task)
    return {"status": "Message added to queue"}

# Run the FastAPI app
# Use the command below to run the app:
# uvicorn this_file_name:app --reload
