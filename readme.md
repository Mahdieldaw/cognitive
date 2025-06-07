
# Hybrid Engine Dashboard

Welcome to the Hybrid Engine Dashboard! This web application serves as the user interface for monitoring, managing, and interacting with workflows processed by the Hybrid Engine.

The Hybrid Engine is a personal cognitive mesh designed to transform a user's knowledge base (like an Obsidian vault) from a passive repository into an active, intelligent partner. It orchestrates diverse AI models to execute complex, multi-step thought processes.

## Features

The Dashboard provides the following key features:

*   **Dashboard Overview**: At-a-glance statistics of workflow activity, including total, active, completed, and failed workflows. Visualizations of workflow status distribution.
*   **Workflow Management**:
    *   List all workflows with their current status, progress, and key details.
    *   View detailed information for each workflow, including its steps, status, metadata, logs, and execution metrics.
    *   Visualize workflow steps as a Directed Acyclic Graph (DAG).
*   **Workflow Creation**:
    *   Browse available workflow templates.
    *   Initiate new workflows by providing parameters to selected templates.
*   **Workflow Branching**: Create new branches from existing workflows to explore alternative execution paths or retry with modifications.
*   **Resilience and Persistence**: (Handled by the backend Python orchestrator) The system is designed to be resilient, with workflow state persisted and recoverable.

## Tech Stack (Frontend Dashboard)

*   **React 18**: For building the user interface.
*   **TypeScript**: For static typing and improved code quality.
*   **Tailwind CSS**: For utility-first styling.
*   **React Router**: For client-side routing.
*   **Recharts**: For data visualization (charts).
*   **Vite/esbuild (implied by importmap usage)**: For fast development and bundling (although not explicitly configured in this prompt, typical for modern React setups using esm.sh).

## Project Vision

This dashboard is part of a larger vision: the "Hybrid Engine." This system aims to solve the problem of ephemeral and siloed AI interactions by integrating AI workflows directly into a user's personal knowledge management system (Obsidian).

*   **Knowledge Layer (Obsidian Vault)**: The single source of truth for workflows, inputs, and outputs.
*   **Orchestration Layer (Python Server)**: The brains of the operation, managing job queues, workflow execution (DAGs), state, and model interactions.
*   **Access Layer (Adapters & Extension)**: Connects to various LLMs and, in the long term, includes a Chrome extension for web interactions.

## Getting Started

Refer to the `docs/development_setup.md` for instructions on how to run this dashboard locally.

## Further Documentation

*   **Architecture**: `docs/architecture.md`
*   **User Guide**: `docs/user_guide.md`
*   **API Integration**: `docs/api_integration.md`
