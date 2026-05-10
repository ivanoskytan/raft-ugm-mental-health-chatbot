# RAFT Mental Health Chatbot
This project implements a Retrieval-Augmented Fine-Tuning (RAFT) approach for a specialized mental health chatbot. The system combines the knowledge retrieval of a RAG (Retrieval-Augmented Generation) system with the specialized behavior of a fine-tuned LLM.

## Architecture Components
- Web App: Flask based web application with RESTful API endpoints, utilizing Javascript to handle dynamic interfaces.
- Vectorstore Builder: Creates and manages semantic search indexes.
- RAFT Preparation Pipeline: Generates a specialized fine-tuning dataset through five phases.

## Tech Stack
- Language: Python 3.12 & Javascript
- Web Framework: Flask
- Databases: PostgreSQL (knowledge retrieval system) & MongoDB (users and chats data)

## Guide
### 1. Running the web app
To launch the user interface and API services for deployment or local testing:
`python main.py run-web app`

### 2. Building the vectorstore (domain knowledge)
To process your documents and build the semantic search index:
`python main.py run-engine vectorstore-builder`

### 3. Running the RAFT Pipeline
You can run the entire 5-phase data preparation sequence or target a specific phase using the --phase flag:
- Full Pipeline: `python main.py run-engine raft-preparation-pipeline`

- Specific Phase: `python main.py run-engine raft-preparation-pipeline --phase 4` (e.g., for CoT Augmentation)

### 4. Maintenance & Cleanup
To reset local data or clear cached outputs:
- Clear prepared data: `python main.py clean raft-data`