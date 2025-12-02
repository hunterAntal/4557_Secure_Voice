# 🎯 SFU Web Voice Chat - Project Plan

**Branch:** `feature/sfu-web-voice-chat`
**Created:** 2025-12-02
**Goal:** Build a web-based group voice chat system (4-5 users) using Selective Forwarding Unit (SFU) architecture

---

## 📋 Project Overview

Transform the existing file-based secure voice transmission system into a real-time web application where users can:
- Share a link to create/join voice calls
- Select microphone and speaker devices in browser
- See who's in the call in real-time
- Have secure voice conversations with 4-5 friends simultaneously

---

## 🏗️ Architecture

```
Browser (User A)                    Server (SFU)                    Browser (User B)
─────────────────────────────────────────────────────────────────────────────────────
getUserMedia() → Capture audio
                 ↓
              Encode audio
                 ↓
              Encrypt (AES)
                 ↓
              WebSocket.send() ──────→ Receive encrypted audio
                                       Decrypt with session key
                                       Mix streams (numpy)
                                       Encrypt mixed result
                                       ─────────────────────→ WebSocket.receive()
                                                              Decrypt
                                                              Decode
                                                              AudioContext.play()
```

---

## ✅ Phase 1: Project Setup & Structure

### 1.1 Directory Structure
- [x] Create `src/` folder
- [x] Move existing modules to `src/`
- [ ] Create `src/web/` for web application
- [ ] Create `src/web/static/` for frontend files
- [ ] Create `src/web/templates/` (if using Jinja2)
- [ ] Create `tests/` for test files
- [ ] Create `docs/` for documentation

**Target Structure:**
```
4557_project/
├── src/
│   ├── web/
│   │   ├── __init__.py
│   │   ├── server.py              # FastAPI application
│   │   ├── room_manager.py        # Room state management
│   │   ├── audio_mixer.py         # Audio mixing logic
│   │   └── static/
│   │       ├── index.html         # Landing page
│   │       ├── call.html          # Call interface
│   │       ├── client.js          # WebSocket client
│   │       └── styles.css         # UI styling
│   ├── audio_processor.py         # Existing (reuse)
│   ├── crypto_module.py           # Existing (reuse)
│   ├── error_correction.py        # Existing (may not need)
│   └── secure_channel.py          # Existing (adapt for web)
├── requirements.txt
├── requirements-web.txt            # New: Web-specific deps
├── README.md
├── SFU_PROJECT_PLAN.md            # This file
└── DEPLOYMENT.md                   # New: Deployment guide
```

### 1.2 Dependencies Setup
- [ ] Update `requirements.txt` or create `requirements-web.txt`
- [ ] Add FastAPI
- [ ] Add uvicorn (ASGI server)
- [ ] Add websockets
- [ ] Add python-multipart (for file uploads if needed)
- [ ] Add jinja2 (for HTML templates)

### 1.3 Git & Version Control
- [x] Create `feature/sfu-web-voice-chat` branch
- [ ] Update `.gitignore` for web-specific files
- [ ] Commit initial structure

---

## ✅ Phase 2: Backend Development

### 2.1 Core Server Setup
- [ ] Create `src/web/server.py` with FastAPI app
- [ ] Set up WebSocket endpoint `/ws/{room_id}`
- [ ] Create HTTP endpoints:
  - [ ] `GET /` - Landing page
  - [ ] `POST /api/create_room` - Create new room
  - [ ] `GET /call/{room_id}` - Call interface
  - [ ] `GET /api/rooms/{room_id}/info` - Room info (optional)

### 2.2 Room Management
- [ ] Create `src/web/room_manager.py`
- [ ] Implement `Room` class:
  - [ ] Track participants (user_id, name, websocket)
  - [ ] Generate unique room IDs
  - [ ] Handle join/leave events
  - [ ] Broadcast participant list updates
  - [ ] Clean up empty rooms

- [ ] Implement `Participant` class:
  - [ ] Store websocket connection
  - [ ] Track mute state
  - [ ] Buffer audio chunks
  - [ ] Manage user metadata (name, id)

### 2.3 Audio Mixing
- [ ] Create `src/web/audio_mixer.py`
- [ ] Implement audio mixing algorithm:
  - [ ] Receive audio from multiple participants
  - [ ] Mix streams (averaging or summing with normalization)
  - [ ] Handle variable buffer sizes
  - [ ] Exclude sender from their own mix (avoid echo)
  - [ ] Handle silence (when no audio available)

- [ ] Optimize for real-time performance:
  - [ ] Use numpy for efficient mixing
  - [ ] Minimize latency (<50ms processing)
  - [ ] Handle async audio arrival

### 2.4 Crypto Integration
- [ ] Adapt existing `crypto_module.py` for web use
- [ ] Implement session key management per room:
  - [ ] Generate AES-256 key per room
  - [ ] Distribute key to participants (secure handshake)
  - [ ] Implement key rotation (optional)

- [ ] Simplify crypto for real-time (trade-offs):
  - [ ] **Option A:** Server-side encryption only (trust server)
  - [ ] **Option B:** End-to-end encryption (complex key exchange)
  - [ ] **Recommendation:** Start with Option A, add Option B later

- [ ] Decide on crypto layer:
  - [ ] Keep AES-256-GCM encryption
  - [ ] Keep HMAC-SHA256 for integrity
  - [ ] **Drop per-packet RSA signatures** (too slow for real-time)
  - [ ] Use RSA only for session establishment

### 2.5 WebSocket Protocol
- [ ] Define message types:
  ```python
  {
    "type": "join",           # Client joins room
    "type": "leave",          # Client leaves
    "type": "audio",          # Audio chunk
    "type": "participants",   # Participant list update
    "type": "user_joined",    # New user notification
    "type": "user_left",      # User left notification
    "type": "mute",           # Toggle mute
    "type": "error"           # Error message
  }
  ```

- [ ] Implement WebSocket handlers:
  - [ ] Connection handler (authenticate, add to room)
  - [ ] Message handler (route by type)
  - [ ] Disconnection handler (clean up, notify others)
  - [ ] Error handler (graceful failures)

---

## ✅ Phase 3: Frontend Development

### 3.1 Landing Page (`static/index.html`)
- [ ] Create simple landing page
- [ ] "Create Room" button
- [ ] "Join Room" input (optional)
- [ ] Basic styling with CSS
- [ ] JavaScript to call `/api/create_room`
- [ ] Redirect to `/call/{room_id}` after creation

### 3.2 Call Interface (`static/call.html`)
- [ ] HTML structure:
  - [ ] Microphone selector dropdown
  - [ ] Speaker selector dropdown
  - [ ] Participant list container
  - [ ] Share link input (with copy button)
  - [ ] Mute/Unmute button
  - [ ] Leave call button
  - [ ] Volume indicators (optional)

- [ ] CSS styling:
  - [ ] Clean, modern design
  - [ ] Responsive layout (mobile-friendly)
  - [ ] Visual feedback for active speakers
  - [ ] Muted state indicators
  - [ ] Loading states

### 3.3 WebSocket Client (`static/client.js`)
- [ ] Create `VoiceCallClient` class
- [ ] Implement audio capture:
  - [ ] Request microphone access (`getUserMedia`)
  - [ ] Create AudioContext
  - [ ] Capture audio chunks (ScriptProcessorNode or AudioWorklet)
  - [ ] Convert Float32 to Int16 for transmission
  - [ ] Send chunks via WebSocket

- [ ] Implement audio playback:
  - [ ] Receive mixed audio from server
  - [ ] Convert Int16 to Float32
  - [ ] Create audio buffer
  - [ ] Play through AudioContext

- [ ] Implement WebSocket communication:
  - [ ] Connect to `/ws/{room_id}`
  - [ ] Handle message types (join, leave, audio, participants)
  - [ ] Send audio chunks
  - [ ] Handle reconnection on disconnect

- [ ] Implement device selection:
  - [ ] Enumerate audio devices (`enumerateDevices`)
  - [ ] Populate dropdown menus
  - [ ] Handle device changes
  - [ ] Test audio output routing

- [ ] Implement UI updates:
  - [ ] Update participant list in real-time
  - [ ] Show mute states
  - [ ] Display connection status
  - [ ] Handle errors gracefully

### 3.4 Audio Processing
- [ ] Implement buffer management:
  - [ ] Ring buffer for smooth playback
  - [ ] Handle jitter (variable network delays)
  - [ ] Adaptive buffering (trade latency vs smoothness)

- [ ] Optional enhancements:
  - [ ] Volume meter visualization
  - [ ] Echo cancellation (browser built-in)
  - [ ] Noise suppression (browser built-in)
  - [ ] Auto gain control (browser built-in)

---

## ✅ Phase 4: Integration & Testing

### 4.1 Local Testing
- [ ] Test with 2 users (same machine, different browsers)
- [ ] Test with 3-5 users (friends on same network)
- [ ] Measure latency (browser → server → browser)
- [ ] Test audio quality (no distortion, clipping)
- [ ] Test mute/unmute functionality
- [ ] Test device switching
- [ ] Test graceful disconnection

### 4.2 Network Testing
- [ ] Test over LAN (local network)
- [ ] Test over WAN (internet)
- [ ] Test with varying network conditions:
  - [ ] Packet loss simulation
  - [ ] Latency simulation
  - [ ] Bandwidth throttling

### 4.3 Browser Compatibility
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari (macOS/iOS)
- [ ] Edge

### 4.4 Edge Cases
- [ ] User joins mid-call
- [ ] User refreshes page
- [ ] User loses connection temporarily
- [ ] All users leave (room cleanup)
- [ ] Simultaneous joins
- [ ] Rapid mute/unmute
- [ ] Device permission denied

### 4.5 Security Testing
- [ ] Verify encryption is working
- [ ] Test with man-in-the-middle proxy
- [ ] Check for CSRF vulnerabilities
- [ ] Validate WebSocket authentication
- [ ] Test rate limiting (prevent spam)

---

## ✅ Phase 5: Optimization & Polish

### 5.1 Performance Optimization
- [ ] Profile server CPU usage
- [ ] Optimize audio mixing (vectorization with numpy)
- [ ] Reduce WebSocket message size (binary instead of JSON)
- [ ] Implement client-side buffering
- [ ] Add server-side caching (if needed)

### 5.2 Latency Reduction
- [ ] Benchmark current latency
- [ ] Target: <100ms end-to-end
- [ ] Reduce chunk size (trade-off: more packets)
- [ ] Use binary WebSocket frames
- [ ] Consider UDP (WebRTC) for even lower latency (future)

### 5.3 Audio Quality Improvements
- [ ] Test with different sample rates (8kHz, 16kHz, 48kHz)
- [ ] Add optional Opus codec (better than raw PCM)
- [ ] Implement packet loss concealment (PLC)
- [ ] Add automatic gain control
- [ ] Test stereo vs mono

### 5.4 UI/UX Improvements
- [ ] Add user avatars or initials
- [ ] Show speaking indicators (volume bars)
- [ ] Add sound effects (join/leave notifications)
- [ ] Improve error messages
- [ ] Add loading spinners
- [ ] Dark mode toggle (optional)

### 5.5 Feature Enhancements (Optional)
- [ ] Text chat alongside voice
- [ ] Screen sharing
- [ ] Recording functionality
- [ ] Room passwords
- [ ] Persistent rooms (save state to database)
- [ ] User authentication (login)
- [ ] Admin controls (kick users, mute all)

---

## ✅ Phase 6: Deployment

### 6.1 Production Readiness
- [ ] Create `DEPLOYMENT.md` guide
- [ ] Set up environment variables (secrets)
- [ ] Configure HTTPS (required for getUserMedia)
- [ ] Set up CORS headers
- [ ] Add logging and monitoring
- [ ] Implement rate limiting
- [ ] Add health check endpoint (`/health`)

### 6.2 HTTPS Setup
- [ ] Obtain SSL certificate (Let's Encrypt)
- [ ] Configure nginx/caddy reverse proxy
- [ ] Test HTTPS WebSocket connection (wss://)

### 6.3 Hosting Options
**Option A: Self-Hosted**
- [ ] Set up server (DigitalOcean, AWS EC2, etc.)
- [ ] Install Python 3.9+
- [ ] Install dependencies
- [ ] Run with uvicorn
- [ ] Set up systemd service (auto-restart)

**Option B: Platform-as-a-Service**
- [ ] Deploy to Heroku, Fly.io, or Railway
- [ ] Configure buildpacks
- [ ] Set environment variables
- [ ] Deploy via git push

**Option C: Serverless**
- [ ] Deploy to AWS Lambda + API Gateway
- [ ] Configure WebSocket routes
- [ ] Handle cold starts

### 6.4 Scaling Considerations
- [ ] Load balancing (if multiple servers)
- [ ] Shared state (Redis for room management)
- [ ] WebSocket sticky sessions
- [ ] Monitor server resources (CPU, RAM, bandwidth)

---

## ✅ Phase 7: Documentation

### 7.1 User Documentation
- [ ] Update `README.md` with web app instructions
- [ ] Create `USAGE_GUIDE.md` for web interface
- [ ] Add screenshots/GIFs of UI
- [ ] Document supported browsers
- [ ] Troubleshooting guide

### 7.2 Developer Documentation
- [ ] API documentation (endpoints)
- [ ] WebSocket protocol specification
- [ ] Architecture diagram
- [ ] Code comments in key modules
- [ ] Contributing guide (if open source)

### 7.3 Deployment Documentation
- [ ] `DEPLOYMENT.md` with step-by-step instructions
- [ ] Docker setup (optional)
- [ ] Environment variables reference
- [ ] SSL/TLS setup guide
- [ ] Monitoring and logging setup

---

## 🎯 Success Criteria

### Minimum Viable Product (MVP)
- [x] Clean project structure
- [ ] 2-5 users can join a voice call
- [ ] Real-time audio transmission (<200ms latency)
- [ ] Web interface with mic/speaker selection
- [ ] Show participant list
- [ ] Basic encryption (AES-256)
- [ ] Works over LAN/localhost
- [ ] Runs on one browser (Chrome)

### Production Ready
- [ ] <100ms latency end-to-end
- [ ] Works on WAN (internet)
- [ ] HTTPS enabled
- [ ] Cross-browser support
- [ ] Error handling and recovery
- [ ] Clean, intuitive UI
- [ ] Deployment guide
- [ ] Load tested (10+ simultaneous rooms)

### Nice to Have
- [ ] Opus codec for better compression
- [ ] WebRTC for P2P (lower latency)
- [ ] Mobile support (iOS/Android browsers)
- [ ] Recording feature
- [ ] Text chat
- [ ] Screen sharing

---

## 📊 Timeline Estimate

| Phase | Estimated Time | Status |
|-------|---------------|--------|
| Phase 1: Setup | 1-2 hours | 🟡 In Progress |
| Phase 2: Backend | 1-2 days | ⚪ Not Started |
| Phase 3: Frontend | 1-2 days | ⚪ Not Started |
| Phase 4: Testing | 1 day | ⚪ Not Started |
| Phase 5: Optimization | 1-2 days | ⚪ Not Started |
| Phase 6: Deployment | 0.5-1 day | ⚪ Not Started |
| Phase 7: Documentation | 0.5 day | ⚪ Not Started |
| **Total** | **5-9 days** | **10% Complete** |

---

## 🔄 Current Status

**Branch:** `feature/sfu-web-voice-chat`
**Last Updated:** 2025-12-02
**Completed:**
- ✅ Removed audio files from root
- ✅ Created `src/` directory
- ✅ Moved Python modules to `src/`
- ✅ Project plan created

**Next Steps:**
1. Create `src/web/` directory structure
2. Update `requirements.txt` with web dependencies
3. Start building FastAPI server (`src/web/server.py`)

---

## 📝 Notes & Decisions

### Technology Choices
- **Backend:** Python FastAPI (async, fast, easy WebSocket support)
- **Frontend:** Vanilla JavaScript (no framework overhead, keep it simple)
- **Audio:** Web Audio API (built-in browser support)
- **WebSocket:** Native (no Socket.IO needed)
- **Crypto:** Reuse existing AES-256/HMAC, drop RSA per-packet signatures

### Architecture Trade-offs
- **SFU vs P2P Mesh:** SFU chosen for simplicity, easier NAT traversal, server control
- **Server-side vs E2E encryption:** Start with server-side (simpler), can add E2E later
- **WebSocket vs WebRTC:** WebSocket for MVP (simpler), WebRTC for future optimization

### Known Limitations
- UDP not available in browsers (WebSocket is TCP-based)
- getUserMedia requires HTTPS (http://localhost is exception)
- Safari requires user gesture for audio playback
- Mobile browsers may have autoplay restrictions

---

## 🤝 Contributing

This is a learning project. Key areas for improvement:
- Latency optimization
- Audio quality tuning
- Cross-browser compatibility
- Security hardening
- UI/UX design

---

**Ready to build!** 🚀
