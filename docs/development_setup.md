
# Hybrid Engine Dashboard - Development Setup

This guide provides instructions on how to set up and run the Hybrid Engine Dashboard frontend application locally for development.

## Prerequisites

*   **Node.js and npm/yarn**: Ensure you have a recent version of Node.js installed, which includes npm (Node Package Manager). Yarn is an alternative package manager.
    *   Download Node.js: [https://nodejs.org/](https://nodejs.org/)
*   **Web Browser**: A modern web browser like Chrome, Firefox, or Edge.
*   **Code Editor**: A code editor like VS Code is recommended.

## Project Structure

The frontend application is structured as follows (simplified):

```
hybrid-engine-dashboard/
├── docs/                     # Documentation files
├── public/                   # Static assets (if any, not explicitly used yet)
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── common/
│   │   ├── layout/
│   │   └── workflows/
│   ├── pages/                # Page-level components
│   ├── services/             # API interaction services (currently mocked)
│   ├── App.tsx               # Main application component with routing
│   ├── constants.tsx         # Shared constants (icons, API base URL)
│   ├── index.tsx             # Entry point of the React application
│   └── types.ts              # TypeScript type definitions
├── index.html                # Main HTML file
├── metadata.json             # Application metadata
├── package.json              # Project dependencies and scripts (implicit)
├── tsconfig.json             # TypeScript configuration (implicit)
└── readme.md                 # Project overview
```

**Note**: Since this project uses ES modules directly via `esm.sh` in `index.html` (through an `importmap`), a traditional `package.json` and `node_modules` folder managed by npm/yarn for frontend dependencies might not be strictly necessary for *just running* it as-is if all dependencies are CDN-hosted. However, for a typical development workflow involving local tooling (linters, formatters, build tools), you would usually have a `package.json`.

## Setup and Running

The current setup relies on serving `index.html` and having a browser that supports ES modules and import maps.

**Method 1: Using a simple HTTP server (for basic viewing)**

If you have Python installed, you can quickly serve the files:
1.  Navigate to the root directory of the `hybrid-engine-dashboard` project in your terminal.
2.  Run a simple HTTP server.
    *   For Python 3: `python -m http.server 8000` (or any other port)
3.  Open your web browser and go to `http://localhost:8000`.

Using a tool like `live-server` (installable via npm: `npm install -g live-server`) is even better as it provides live reloading:
1.  Install `live-server`: `npm install -g live-server`
2.  Navigate to the project root.
3.  Run: `live-server`
4.  It will automatically open the application in your browser.

**Method 2: Setting up a Vite project (Recommended for Development)**

For a more robust development experience with features like Hot Module Replacement (HMR), optimized builds, and easy dependency management, it's recommended to integrate this into a Vite project.

If you were starting from scratch or wanted to refactor for a Vite setup:

1.  **Initialize a Vite Project:**
    ```bash
    npm create vite@latest hybrid-engine-dashboard -- --template react-ts
    cd hybrid-engine-dashboard
    npm install
    ```

2.  **Copy Existing Source Files:**
    *   Copy the contents of the `src/` directory from this project into the `src/` directory of your new Vite project.
    *   Copy the `index.html` content (especially the `<div id="root"></div>` and the general structure, but Vite will manage script tags). Vite's `index.html` is the entry point and should be in the project root.
    *   Adjust `index.html` to let Vite handle module loading:
        ```html
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="UTF-8" />
            <link rel="icon" type="image/svg+xml" href="/vite.svg" /> <!-- Or your own favicon -->
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Hybrid Engine Dashboard</title>
            <script src="https://cdn.tailwindcss.com"></script> <!-- Keep Tailwind CDN or set up PostCSS -->
             <style>
              /* Custom scrollbar and global styles */
              html, body, #root { height: 100%; margin: 0; padding: 0; background-color: #111827; color: #f3f4f6; }
              ::-webkit-scrollbar { width: 8px; height: 8px; }
              ::-webkit-scrollbar-track { background: #1f2937; }
              ::-webkit-scrollbar-thumb { background: #4b5563; border-radius: 4px; }
              ::-webkit-scrollbar-thumb:hover { background: #6b7280; }
            </style>
          </head>
          <body>
            <div id="root"></div>
            <script type="module" src="/src/index.tsx"></script>
          </body>
        </html>
        ```

3.  **Install Dependencies:**
    Since the original project uses CDNs via `esm.sh` for `react`, `react-dom`, `react-router-dom`, and `recharts`, you'd install these as actual npm packages:
    ```bash
    npm install react react-dom react-router-dom recharts
    npm install -D @types/react @types/react-dom
    ```
    Then, update all import statements in your `.tsx` files to import directly (e.g., `import React from 'react';` instead of relying on the import map). Vite handles the resolution.

4.  **Tailwind CSS Setup (with Vite):**
    For optimal Tailwind CSS integration with Vite (including purging unused styles for production builds), follow the official Tailwind CSS guide for Vite:
    [Tailwind CSS with Vite](https://tailwindcss.com/docs/guides/vite)

5.  **Run the Development Server:**
    ```bash
    npm run dev
    ```
    This will start a development server (usually on `http://localhost:5173`) with HMR.

## Code Style and Linting (Recommended)

*   **ESLint**: For identifying and fixing problems in JavaScript/TypeScript code.
*   **Prettier**: For consistent code formatting.
*   Consider setting these up in your project if using Method 2.

## API Interaction

*   The application currently uses a mock API service (`src/services/orchestratorService.ts`).
*   The `API_BASE_URL` is defined in `src/constants.tsx`. In a real deployment, this would point to the Python backend server.
*   No actual backend is required to run the frontend with the mock service.

## Building for Production (with Vite - Method 2)

If you set up the project with Vite:
```bash
npm run build
```
This command will create an optimized static build of your application in the `dist` folder, which can then be deployed to any static site hosting service.

This setup guide should help you get the Hybrid Engine Dashboard running for development and further exploration.
