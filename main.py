from fastapi import FastAPI, BackgroundTasks, HTTPException, Header, Depends
from pydantic import BaseModel
import requests
import queue
import threading
import time
from fastapi.middleware.cors import CORSMiddleware


# Define a simple queue for managing tasks
message_queue = queue.Queue()

# Create the FastAPI app
app = FastAPI()


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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
        print('Message with URL buttons sent successfully!')
    else:
        print(f'Failed to send message. Status code: {response.status_code}')
        print(response.text)

# Background task to process the queue
def message_sender_worker():
    while True:
        if not message_queue.empty():
            task = message_queue.get()
            try:
                send_message_with_url_buttons(
                    task["bot_token"],
                    task["chat_id"],
                    task["message"],
                    task["buttons"]
                )
                time.sleep(0.1)  # Sleep for 0.1 seconds to comply with rate limit (10 messages per second)
            except Exception as e:
                print(f"Error sending message: {e}")
            finally:
                message_queue.task_done()
        else:
            time.sleep(0.5)

# Start the background worker thread
threading.Thread(target=message_sender_worker, daemon=True).start()

# FastAPI endpoint to send a message
@app.post("/send_message/")
async def send_message_endpoint(msg: Message, x_bot_token: str = Header(...)):
    # Add the message to the queue
    task = {
        "bot_token": x_bot_token,
        "chat_id": msg.chat_id,
        "message": msg.message,
        "buttons": msg.buttons
    }
    message_queue.put(task)
    return {"status": "Message added to queue"}

# Run the FastAPI app
# Use the command below to run the app:
# uvicorn this_file_name:app --reload
