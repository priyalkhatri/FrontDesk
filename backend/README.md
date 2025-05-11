# Frontdesk AI Supervisor - Backend

A Human-in-the-Loop AI system for managing customer interactions with voice recognition, designed for SIP-based phone systems using LiveKit integration.

## 🚀 Features

- 🎙️ **Voice-based AI receptionist** using LiveKit SIP integration
- 🔄 **Human-in-the-loop system** for unknown queries
- 📚 **Dynamic knowledge base** that learns from interactions
- 🎯 **Real-time speech recognition** and synthesis
- 📊 **Supervisor dashboard** for managing requests
- 💾 **AWS DynamoDB** for scalable data storage
- 📞 **SIP telephony support** for standard phone systems

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Voice Platform**: LiveKit with SIP integration
- **Speech Recognition**: Deepgram
- **Text-to-Speech**: Neuphonic/ElevenLabs
- **Database**: AWS DynamoDB
- **Language**: Python 3.9+
- **Real-time Communication**: WebSockets

## 📋 Prerequisites

- Python 3.9 or higher
- AWS account with DynamoDB access
- LiveKit account with SIP enabled
- Deepgram API key
- Neuphonic/ElevenLabs API key
- (Optional) Twilio account for SMS notifications

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── api/                    # API endpoint definitions
│   │   ├── calls.py           # Call management endpoints
│   │   ├── help_requests.py   # Help request endpoints
│   │   ├── knowledge.py       # Knowledge base endpoints
│   │   └── routes.py          # Route aggregator
│   ├── models/                # Database models
│   │   ├── call_record.py     # Call record model
│   │   ├── help_request.py    # Help request model
│   │   └── knowledge_base.py  # Knowledge base model
│   ├── services/              # Business logic layer
│   │   ├── ai_agent.py        # AI agent core logic
│   │   ├── agent_service.py   # Voice agent service
│   │   ├── audio_processor.py # Audio processing service
│   │   ├── notification_service.py # SMS/notification service
│   │   └── speech_services.py # STT/TTS integration
│   ├── integrations/          # External service integrations
│   │   └── livekit_sip.py     # LiveKit SIP integration
│   ├── config/                # Configuration modules
│   │   ├── __init__.py
│   │   ├── settings.py        # Application settings
│   │   └── livekit_config.py  # LiveKit configuration
│   ├── utils/                 # Utility functions
│   │   └── logger.py          # Logging configuration
│   └── main.py               # FastAPI application entry point
├── scripts/                   # Utility scripts
│   ├── demo.py               # System demonstration
│   └── test_dynamodb.py      # Database testing
├── logs/                      # Application logs directory
│   └── app.log               # Main application log
├── data/                      # Local data storage
│   └── sip_trunk_config.json # SIP configuration
├── requirements.txt          # Python dependencies
├── run.py                    # Main server runner
├── run_agent.py              # Voice agent runner
├── .env.template             # Environment variables template
├── .gitignore                # Git ignore file
└── README.md                 # Project documentation
```

## ⚡ Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-repo/frontdesk-ai-supervisor.git
cd frontdesk-ai-supervisor/backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the backend directory:
```bash
cp .env.template .env
```

Then edit the `.env` file with your actual credentials:

```env
# LiveKit Configuration
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=your-livekit-cloud.livekit.cloud

# AWS Configuration
DYNAMODB_REGION=us-east-1
DYNAMODB_ACCESS_KEY=your_aws_access_key
DYNAMODB_SECRET_KEY=your_aws_secret_key

# Speech Services
DEEPGRAM_API_KEY=your_deepgram_api_key
NEUPHONIC_API_KEY=your_neuphonic_api_key

# SIP Configuration
SIP_ENABLED=True
SIP_DOMAIN=sip.livekit.io
DEFAULT_CALLER_ID=+1234567890

# Optional: SMS Notifications
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_number
```

### 5. Initialize Database
The system will automatically create DynamoDB tables on first run. Ensure your AWS credentials have the necessary permissions:
- `dynamodb:CreateTable`
- `dynamodb:PutItem`
- `dynamodb:GetItem`
- `dynamodb:UpdateItem`
- `dynamodb:Query`
- `dynamodb:Scan`

## 🚀 Running the Application

### Start the Main Server
```bash
# Activate virtual environment first
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Development mode with auto-reload
python run.py

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

### Run the Voice Agent Worker
In a separate terminal:
```bash
python run_agent.py
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check endpoint |
| `/api/help-requests` | GET | List all help requests |
| `/api/help-requests/{id}` | GET | Get specific help request |
| `/api/help-requests/{id}/resolve` | POST | Resolve a help request |
| `/api/knowledge` | GET | List knowledge base entries |
| `/api/knowledge/search` | GET | Search knowledge base |
| `/api/knowledge` | POST | Add knowledge entry |
| `/api/calls` | GET | List call records |
| `/api/calls/test` | GET | Create a test call |
| `/api/calls/{id}` | GET | Get call details |
| `/api/calls/{id}/end` | POST | End an active call |

## 🏛️ Architecture Overview

### Core Components

1. **AI Agent** (`services/ai_agent.py`)
   - Handles incoming calls
   - Processes customer questions
   - Creates help requests for unknown queries
   - Manages knowledge base lookups

2. **LiveKit SIP Integration** (`integrations/livekit_sip.py`)
   - Manages voice-only SIP calls
   - Handles WebSocket connections
   - Processes call events

3. **Speech Services** (`services/speech_services.py`)
   - Integrates with Deepgram for STT
   - Integrates with Neuphonic/ElevenLabs for TTS
   - Supports streaming recognition

4. **Database Models**
   - `HelpRequest`: Tracks unanswered questions
   - `KnowledgeBase`: Stores learned answers
   - `CallRecord`: Maintains call history

### Data Flow

1. Customer calls → LiveKit SIP → AI Agent
2. AI Agent processes question → Knowledge Base lookup
3. If unknown → Create Help Request → Notify Supervisor
4. Supervisor responds → Update Knowledge Base
5. Future calls → AI can answer automatically

## 🔧 Development

### Running Tests
```bash
pytest tests/
```

### Demo System
```bash
python scripts/demo.py
```

### Database Testing
```bash
python scripts/test_dynamodb.py
```

### Code Style
The project follows PEP 8 guidelines. Use `black` for formatting:
```bash
black app/
```

## 🚦 Deployment

### Environment Variables
Ensure all required environment variables are set in production:
- LiveKit credentials
- AWS credentials
- Speech service API keys
- SIP configuration



## 🔍 Monitoring & Logs

- Application logs: `logs/app.log`
- Real-time logs: Check console output
- LiveKit dashboard for call monitoring
- AWS CloudWatch for DynamoDB metrics

## 🚀 Performance Optimization

- Use connection pooling for database
- Implement caching for knowledge base
- Optimize speech recognition settings
- Use async operations throughout

## 🛠️ Troubleshooting

### Common Issues

1. **WebSocket Connection Failures**
   - Check LiveKit credentials
   - Verify network connectivity
   - Ensure proper URL format

2. **Speech Recognition Issues**
   - Verify API keys
   - Check audio format compatibility
   - Monitor API quotas

3. **Database Errors**
   - Verify AWS credentials
   - Check table creation permissions
   - Monitor DynamoDB capacity

