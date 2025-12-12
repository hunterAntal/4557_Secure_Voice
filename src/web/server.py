"""
SFU Voice Chat Server - Module 1: FastAPI Basics

This is a simple FastAPI server that demonstrates the fundamentals.
We'll build on this step-by-step to create our voice chat application.
"""

# Import FastAPI - the web framework we're using
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import secrets  # For generating random room IDs

# Create the FastAPI application
# This is like opening a restaurant - you create the "app" that will serve customers
app = FastAPI(
    title="SFU Voice Chat",  # Name of your API
    description="Real-time voice chat using Selective Forwarding Unit architecture",
    version="1.0.0"
)


# ============================================================================
# ENDPOINT 1: Homepage (GET /)
# ============================================================================
# The @app.get("/") is a "decorator" - it tells FastAPI:
# "When someone visits the root URL (/), run this function"

@app.get("/", response_class=HTMLResponse)
async def homepage():
    """
    This endpoint serves the landing page where users can create a room.

    - Route: GET /
    - Returns: HTML page
    - Purpose: Entry point for users
    """
    # For now, we return simple HTML
    # Later, we'll make this fancier with CSS and JavaScript

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SFU Voice Chat</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 100px auto;
                text-align: center;
            }
            button {
                padding: 15px 30px;
                font-size: 18px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            button:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
        <h1>Secure Voice Chat</h1>
        <p>Click below to create a new voice chat room</p>
        <button onclick="createRoom()">Create Room</button>

        <script>
            // When user clicks "Create Room", call the API
            async function createRoom() {
                // Make a POST request to /api/create_room
                const response = await fetch('/api/create_room', {
                    method: 'POST'
                });

                // Get the response (which contains the room ID)
                const data = await response.json();

                // Redirect to the call page
                window.location.href = `/call/${data.room_id}`;
            }
        </script>
    </body>
    </html>
    """

    return html_content


# ============================================================================
# ENDPOINT 2: Create Room (POST /api/create_room)
# ============================================================================
# This endpoint creates a new voice chat room and returns a unique room ID

@app.post("/api/create_room")
async def create_room():
    """
    Creates a new voice chat room.

    - Route: POST /api/create_room
    - Returns: JSON with room_id
    - Purpose: Generate unique room for users to join
    """
    # Generate a random room ID (like "a7b3c9d2e4f6")
    # secrets.token_urlsafe() creates a cryptographically secure random string
    # The number (12) controls length - higher = longer, more unique
    room_id = secrets.token_urlsafe(12)

    # Return JSON response
    # In FastAPI, you can just return a Python dict and it converts to JSON!
    return {
        "room_id": room_id,
        "message": "Room created successfully",
        "url": f"/call/{room_id}"
    }


# ============================================================================
# ENDPOINT 3: Join Room / Call Page (GET /call/{room_id})
# ============================================================================
# The {room_id} is a "path parameter" - it's part of the URL
# Example: /call/abc123 → room_id will be "abc123"

@app.get("/call/{room_id}", response_class=HTMLResponse)
async def call_page(room_id: str):
    """
    Serves the voice call interface for a specific room.

    - Route: GET /call/{room_id}
    - Returns: HTML page with call interface
    - Purpose: Where users actually make voice calls

    Args:
        room_id: The unique identifier for the room (from URL)
    """
    # For now, just show a simple page
    # Later, this will have microphone selection, participant list, etc.

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Voice Call - Room {room_id}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
            }}
            .header {{
                background-color: #f0f0f0;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            .info {{
                background-color: #e3f2fd;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
            }}
            button {{
                padding: 10px 20px;
                margin: 5px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }}
            .mute-btn {{
                background-color: #4CAF50;
                color: white;
            }}
            .leave-btn {{
                background-color: #f44336;
                color: white;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Voice Call</h1>
            <p>Room ID: <strong>{room_id}</strong></p>
        </div>

        <div class="info">
            <h3>Share this link with friends:</h3>
            <input type="text" id="share-link" readonly
                   style="width: 100%; padding: 10px; font-size: 14px;">
            <button onclick="copyLink()">Copy Link</button>
        </div>

        <div>
            <h3>Controls:</h3>
            <button class="mute-btn" onclick="alert('Mute functionality coming in Module 2!')">
                🎤 Mute
            </button>
            <button class="leave-btn" onclick="window.location.href='/'">
                🚪 Leave Call
            </button>
        </div>

        <div style="margin-top: 30px; padding: 20px; background-color: #fff3cd; border-radius: 5px;">
            <h3>👥 Participants:</h3>
            <p>WebSocket functionality coming in Module 2!</p>
            <p>For now, this is just a static page.</p>
        </div>

        <script>
            // Set the share link value when page loads
            document.getElementById('share-link').value = window.location.href;

            function copyLink() {{
                const linkInput = document.getElementById('share-link');
                linkInput.select();
                document.execCommand('copy');
                alert('Link copied to clipboard!');
            }}
        </script>
    </body>
    </html>
    """

    return html_content


# ============================================================================
# ENDPOINT 4: Health Check (GET /health)
# ============================================================================
# This is a simple endpoint to check if the server is running
# Useful for monitoring and debugging

@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.

    - Route: GET /health
    - Returns: JSON with status
    - Purpose: Verify server is running
    """
    return {
        "status": "healthy",
        "message": "SFU Voice Chat server is running!"
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
# This runs when you execute: python server.py
# It starts the web server using uvicorn

if __name__ == "__main__":
    import uvicorn

    # uvicorn.run() starts the web server
    # - app: The FastAPI application we created above
    # - host: "0.0.0.0" means accept connections from any IP (not just localhost)
    # - port: 8000 is the port number (you'll visit http://localhost:8000)
    # - reload: True means auto-restart when code changes (great for development!)

    print("=" * 60)
    print("🚀 Starting SFU Voice Chat Server...")
    print("=" * 60)
    print("\n📍 Visit: http://localhost:8000")
    print("📍 API Docs: http://localhost:8000/docs (auto-generated!)")
    print("\nPress CTRL+C to stop the server\n")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload on code changes
    )
