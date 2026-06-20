# RepoMind SaaS Showcase & Demonstration Script

This script provides a step-by-step guide for showcasing RepoMind to stakeholders, recruiters, or during portfolio reviews. It outlines the core features, visual highlights, and interactive user journeys.

---

## 1. Landing Page & Visual WOW Factor
* **Objective**: Introduce the platform, demonstrate responsive design, and hook the audience with clean glassmorphic aesthetics.
* **Steps**:
  1. Open the landing page at `http://localhost:3000` (or your deployed URL).
  2. Point out the floating interactive code parsing preview card and real-time metric scoreboards.
  3. Show the modern typography (Inter/Outfit) and dark-mode gradients.
  4. Hover over the capabilities cards (Documentation, Diagrams, RAG Chat) to show micro-animations and border glow transitions.

## 2. GitHub OAuth Authentication & Mock Login
* **Objective**: Show SaaS-grade authentication with social login and instant onboarding.
* **Steps**:
  1. Click **Sign In with GitHub** in the hero section or header.
  2. Explain that the app maps GitHub accounts to local PostgreSQL user profiles.
  3. In a production build, this redirects securely to GitHub's OAuth client. In local/mock environments, it immediately signs in using the mock fallback user.
  4. Point out the redirection callback processing loader before entering the main workspace.

## 3. Importing a Repository
* **Objective**: Demonstrate workspace creation with two different onboarding modes.
* **Steps**:
  1. Click **New Repository** in the dashboard.
  2. Show the two tabs: **Paste GitHub URL** and **Select Repository**.
  3. Select **Select Repository** to display a list of available repositories (modeled after Vercel's importer screen).
  4. Click **Import** on `octocat/Spoon-Knife`.
  5. Watch the active pipeline queue track progress:
     * Clone Codebase
     * AST Syntactic Parsing
     * Embedding generation & indexing to Qdrant Cloud
     * Diagram compilation
  6. Explain that this runs in the background and redirects automatically on completion.

## 4. Interactive Architecture Map
* **Objective**: Demonstrate high-fidelity code visualization.
* **Steps**:
  1. Navigate to `/repositories/[id]/architecture` or click the **Architecture Map** tab.
  2. Pan and zoom around the generated DAG.
  3. Explain the layer categorization system (Frontend, Backend, Database, External APIs).
  4. Hover over individual nodes to highlight their imports/dependencies.
  5. Use the filter bar at the top to isolate layers (e.g., show only Database components).
  6. Click a node to view its detailed code context in the right inspector panel.

## 5. AI Multi-Agent Code Review
* **Objective**: Show the depth of automated intelligence.
* **Steps**:
  1. Click the **Code Review Audit** tab.
  2. Show the aggregated security, performance, quality, and architecture scores.
  3. Expand a finding (e.g., hardcoded API keys, circular dependencies) to view the vulnerability details.
  4. Point out that the report provides direct code snippets and line numbers for context.

## 6. RAG Repository Chat
* **Objective**: Demonstrate code intelligence query capabilities.
* **Steps**:
  1. Click **Repository Chat** in the side panel.
  2. Ask a domain question: *“How is authentication managed in this project?”* or *“Where does database connection pool get initialized?”*.
  3. Point out the grounding line citations linked to files in the repository.
