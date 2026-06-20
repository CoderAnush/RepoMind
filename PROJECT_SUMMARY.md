# RepoMind

**AI-Powered Code Intelligence & Documentation Platform**

RepoMind is a production-ready enterprise SaaS platform that automates the ingestion, parsing, indexing, and documentation of software repositories. Designed with a sleek, modern, and highly interactive user interface inspired by tools like Linear and Vercel, RepoMind transforms complex codebases into actionable insights.

## Core Features
- **Architecture Visualization**: Interactive, auto-generated layer classification maps of your codebase (Frontend, Backend, Database, External APIs).
- **AI Code Review Agent**: Multi-agent orchestrator identifying security vulnerabilities, performance bottlenecks, and code smells with precise line-grounded citations.
- **RAG Repository Chat**: Deep contextual chat allowing users to interact directly with their repository's semantics and logic using high-performance vector search.
- **Frictionless Onboarding**: Direct GitHub OAuth integration enabling one-click repository imports.

## Technical Stack
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Framer Motion, React Flow
- **Backend**: FastAPI (Python), PostgreSQL (Supabase), Qdrant Cloud Vector Database
- **AI/ML Orchestration**: LangGraph, OpenAI (`text-embedding-3-small`, `gpt-4o`)
- **Deployment**: Vercel (Frontend SPA), Render (Backend Services)

## Key Achievements
- Engineered a scalable multi-agent LangGraph pipeline capable of dissecting full Abstract Syntax Trees (AST).
- Implemented real-time RAG (Retrieval-Augmented Generation) code queries backed by Qdrant vector search.
- Deployed a highly optimized SPA with GitHub OAuth, JWT token authentication, and robust error handling.

[**View Project on GitHub**](https://github.com/yourusername/RepoMind) | [**Live Demo**](#)
