@echo off

REM ==============================
REM ROOT FILES
REM ==============================

type nul > README.md
type nul > LICENSE
type nul > .gitignore
type nul > .gitattributes
type nul > docker-compose.yml
type nul > docker-compose.prod.yml

REM ==============================
REM CLIENT
REM ==============================

mkdir client
mkdir client\public
mkdir client\src
mkdir client\src\components
mkdir client\src\hooks
mkdir client\src\pages
mkdir client\src\services
mkdir client\src\types
mkdir client\src\utils
mkdir client\src\store
mkdir client\src\styles

type nul > client\public\index.html
type nul > client\public\favicon.ico
type nul > client\public\manifest.json

type nul > client\src\components\RecorderUI.tsx
type nul > client\src\components\EngagementTracker.tsx
type nul > client\src\components\NotesDisplay.tsx
type nul > client\src\components\ActionItems.tsx
type nul > client\src\components\KeywordCloud.tsx
type nul > client\src\components\SessionsList.tsx
type nul > client\src\components\Dashboard.tsx
type nul > client\src\components\Navbar.tsx
type nul > client\src\components\LoadingSpinner.tsx
type nul > client\src\components\ErrorBoundary.tsx

type nul > client\src\hooks\useRecording.ts
type nul > client\src\hooks\useSessions.ts
type nul > client\src\hooks\useEngagement.ts
type nul > client\src\hooks\useAudio.ts
type nul > client\src\hooks\useApi.ts

type nul > client\src\pages\Home.tsx
type nul > client\src\pages\RecordingPage.tsx
type nul > client\src\pages\SessionsPage.tsx
type nul > client\src\pages\AnalyticsPage.tsx
type nul > client\src\pages\SessionDetail.tsx
type nul > client\src\pages\NotFound.tsx

type nul > client\src\services\api.ts
type nul > client\src\services\auth.ts
type nul > client\src\services\storage.ts

type nul > client\src\types\index.ts

type nul > client\src\utils\formatters.ts
type nul > client\src\utils\validators.ts
type nul > client\src\utils\constants.ts
type nul > client\src\utils\helpers.ts

type nul > client\src\store\appStore.ts

type nul > client\src\styles\index.css
type nul > client\src\styles\globals.css
type nul > client\src\styles\variables.css

type nul > client\src\App.tsx
type nul > client\src\index.tsx
type nul > client\src\index.css

type nul > client\.env
type nul > client\.env.local
type nul > client\.gitignore
type nul > client\package.json
type nul > client\tsconfig.json
type nul > client\tailwind.config.js
type nul > client\postcss.config.js
type nul > client\Dockerfile
type nul > client\.dockerignore

REM ==============================
REM SERVER
REM ==============================

mkdir server
mkdir server\modules
mkdir server\models
mkdir server\routes
mkdir server\utils
mkdir server\database
mkdir server\database\migrations
mkdir server\tests
mkdir server\logs
mkdir server\uploads
mkdir server\uploads\audio
mkdir server\uploads\videos
mkdir server\uploads\temp

type nul > server\app.py
type nul > server\config.py
type nul > server\requirements.txt
type nul > server\.env
type nul > server\.env.local
type nul > server\.gitignore
type nul > server\Dockerfile
type nul > server\.dockerignore
type nul > server\wsgi.py

type nul > server\modules\__init__.py
type nul > server\modules\speech_to_text.py
type nul > server\modules\nlp_engine.py
type nul > server\modules\engagement_tracker.py
type nul > server\modules\emotion_detector.py
type nul > server\modules\audio_processor.py

type nul > server\models\__init__.py
type nul > server\models\session.py
type nul > server\models\note.py
type nul > server\models\engagement.py
type nul > server\models\user.py

type nul > server\routes\__init__.py
type nul > server\routes\audio.py
type nul > server\routes\engagement.py
type nul > server\routes\sessions.py
type nul > server\routes\notes.py
type nul > server\routes\analytics.py
type nul > server\routes\health.py

type nul > server\utils\__init__.py
type nul > server\utils\validators.py
type nul > server\utils\decorators.py
type nul > server\utils\file_handler.py
type nul > server\utils\logger.py
type nul > server\utils\constants.py

type nul > server\database\__init__.py
type nul > server\database\connection.py
type nul > server\database\models.py
type nul > server\database\migrations\init.sql
type nul > server\database\migrations\schema.py

type nul > server\tests\__init__.py
type nul > server\tests\test_audio.py
type nul > server\tests\test_nlp.py
type nul > server\tests\test_engagement.py
type nul > server\tests\test_sessions.py
type nul > server\tests\test_api.py
type nul > server\tests\conftest.py

type nul > server\logs\app.log

REM ==============================
REM DOCS
REM ==============================

mkdir docs

type nul > docs\API_DOCUMENTATION.md
type nul > docs\SETUP_GUIDE.md
type nul > docs\ARCHITECTURE.md
type nul > docs\DEPLOYMENT.md

REM ==============================
REM VSCODE
REM ==============================

mkdir .vscode

type nul > .vscode\launch.json
type nul > .vscode\settings.json
type nul > .vscode\extensions.json

echo Project Structure Created Successfully!
pause