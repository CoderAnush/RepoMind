# RepoMind: AI-Powered Code Intelligence & Documentation Platform

RepoMind is a production-ready enterprise SaaS platform that automatically ingests, parses, indexes, and documents software repositories. It utilizes deep Abstract Syntax Tree (AST) parsing, multi-agent AI orchestrations via LangGraph, and semantic retrieval to serve a high-fidelity React frontend dashboard with class diagrams, quality scorecards, and interactive chat.

---

## 1. System Design & Architecture

RepoMind is built using a modern decoupled SaaS architecture.

```mermaid
flowchart TD
    User([SaaS Client Browser]) -->|HTTPS| Vercel[Vercel CDN / Frontend Host]
    Vercel -->|Serves App Bundle| SPA[React SPA Client]
    
    SPA -->|Sign-up / Sign-in| SupabaseAuth[Supabase Auth Service]
    SPA -->|Authenticated APIs: 443| RenderService[Render Web Service]
    
    subgraph Render Task Container
        RenderService -->|Parse & Token Verification| SupabaseAuth
        RenderService -->|Relational Queries| SupabaseDB[(Supabase PostgreSQL)]
        RenderService -->|Embeddings Search| QdrantCloud[(Qdrant Cloud Vector DB)]
        RenderService -->|Multi-Agent Analysis| LLM[OpenAI / Anthropic APIs]
    end
```

### Key Architectural Layers:
1. **Frontend Dashboard (Vercel)**: A React-TypeScript SPA utilizing Tailwind CSS for glassmorphism, rendering Mermaid diagrams dynamically, and providing smooth tabs for README, API spec, onboarding, and conversational chat interfaces.
2. **Backend API (Render)**: A FastAPI ASGI backend executing ingestion jobs, running python AST parsers, slicing code chunks, and running LangGraph agents.
3. **Identity & User Session (Supabase Auth)**: Decentralized user management via JSON Web Tokens (JWT) signed with a project-level HS256 secret.
4. **Metadata Store (Supabase Database)**: Relational PostgreSQL engine holding user tables, repository status indexes, pre-generated documentation, and diagrams.
5. **Code Vector Index (Qdrant Cloud)**: High-performance vector database storing code embeddings (`text-embedding-3-small`) to enable semantic search with line-grounded code citations.

---

## 2. Environment Variable Guide

To run or deploy the application, configure the following environment variables:

### Backend Configuration (`backend/.env` or Render Env Vars)
```env
# Relational Database Connection
DATABASE_URL=postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0.pooler.supabase.com:5432/postgres?sslmode=require

# Supabase Auth Configuration
SUPABASE_URL=https://[PROJECT_ID].supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1Ni...
SUPABASE_JWT_SECRET=your-supabase-jwt-secret-key-goes-here

# Vector Storage (Qdrant Cloud)
QDRANT_HOST=https://[CLUSTER_ID].aws.cloud.qdrant.io
QDRANT_API_KEY=your-qdrant-cloud-write-api-key

# LLM Providers Configuration
LLM_PROVIDER=openai # Set to 'openai' or 'anthropic'
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# System Config
REPO_CLONE_DIR=/tmp/repomind_clones
```

### Frontend Configuration (`frontend/.env` or Vercel Env Vars)
```env
VITE_API_URL=https://repomind-backend.onrender.com/api/v1
```

---

## 3. Developer Setup Guide

Follow these steps to run a local development environment.

### 3.1 Prerequisite Tools
* Python `3.10` or `3.11`
* Node.js `18` or `20`
* Docker (Optional, for local container validation)

### 3.2 Running the Backend API
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file using the template in Section 2.
5. Launch the Uvicorn development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### 3.3 Running the Frontend App
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install node dependencies:
   ```bash
   npm install
   ```
3. Run the Vite local server:
   ```bash
   npm run dev
   ```
4. Access the web client at `http://localhost:3000`.

---

## 4. Deployment Instructions

### 4.1 Supabase Configuration
1. Go to the [Supabase Console](https://supabase.com/).
2. Create a new project.
3. Under **Settings** > **API**:
   * Copy the **Project URL**.
   * Copy the **anon public API key**.
   * Copy the **JWT Secret** (used for `SUPABASE_JWT_SECRET`).
4. Under **Authentication** > **Providers**:
   * Select **Email** and ensure **Enable Signup** is toggled ON.
   * Turn **Confirm Email** OFF for ease of demo verification.

### 4.2 Qdrant Cloud Cluster Configuration
1. Register on [Qdrant Cloud](https://cloud.qdrant.io/).
2. Provision a free cluster.
3. Generate a write-access API key.
4. Note down your cluster hostname URL and token.

### 4.3 Render Backend Deployment
1. Log in to [Render](https://render.com/).
2. Select **New** > **Web Service**.
3. Point to your RepoMind GitHub repository.
4. Input the following options:
   * **Name**: `repomind-backend`
   * **Environment**: `Docker`
   * **Docker Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
   * **Docker Build Context**: `backend`
   * **Dockerfile Path**: `backend/Dockerfile`
5. Under **Environment Variables**, add the keys detailed in Section 2.
6. Click **Deploy Web Service**.

### 4.4 Vercel Frontend Deployment
1. Log in to [Vercel](https://vercel.com/).
2. Add a new project pointing to your RepoMind repository.
3. Configure the following fields:
   * **Root Directory**: `frontend`
   * **Framework Preset**: `Vite`
   * **Build Command**: `npm run build`
   * **Output Directory**: `dist`
4. Under **Environment Variables**, add:
   * `VITE_API_URL` = [Your Deployed Render URL] (e.g. `https://repomind-backend.onrender.com/api/v1`)
5. Click **Deploy**.

---

## 5. Rollback Procedures

### 5.1 Backend Rollback (Render)
If a backend deployment introduces regression bugs:
1. Navigate to the Web Service dashboard on Render.
2. Go to the **Events** tab.
3. Find the previous stable build and select **Rollback to this deploy**.

### 5.2 Frontend Rollback (Vercel)
If a frontend deployment breaks:
1. Navigate to the project dashboard on Vercel.
2. Select the **Deployments** tab.
3. Identify the previous functional deployment, click the menu options (...), and select **Promote to Production**.
