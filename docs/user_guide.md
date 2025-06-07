
# Hybrid Engine Dashboard - User Guide

Welcome to the Hybrid Engine Dashboard! This guide will help you navigate and use the dashboard to manage your AI-powered workflows.

## 1. Introduction

The Hybrid Engine Dashboard is your window into the Hybrid Engine's operations. It allows you to:
- See an overview of all workflow activity.
- Track the progress and status of individual workflows and their steps.
- Launch new workflows using predefined templates.
- Create and manage branches of existing workflows.

## 2. Navigation

The main navigation is located in the sidebar on the left:

*   **Logo (Hybrid)**: Clicking the logo in the top-left corner will usually refresh the current view or take you to a default page.
*   **Dashboard**: Takes you to the main overview page, showing summary statistics and charts about your workflows.
*   **Workflows**: Displays a list of all your workflows, allowing you to browse, search (future), and filter them.
*   **Templates**: Shows available workflow templates that you can use to start new workflows.

The **Header** at the top of the page displays the application title ("Hybrid Engine") and may contain global actions or settings (like a settings cog icon).

## 3. Dashboard Page

This is the landing page after logging in (or opening the app). It provides:

*   **Metric Cards**:
    *   **Total Workflows**: The total number of workflows ever created.
    *   **Active Workflows**: Workflows currently in `RUNNING` or `PENDING` state.
    *   **Completed Successfully**: Workflows that finished with a `COMPLETED` status.
    *   **Failed/Stopped**: Workflows that ended in `FAILED` or `STOPPED` status.
*   **Workflow Status Distribution**: A pie chart showing the proportion of workflows in different statuses (e.g., Completed, Running, Failed).
*   **Recent Activity**: A list of the most recently updated workflows, with quick links to their detail pages.

## 4. Workflows Page

This page lists all your workflows.

*   **Display**: Workflows are typically displayed as cards, showing:
    *   Name
    *   Current Status (with a visual badge)
    *   A brief description
    *   Progress bar (if applicable)
    *   Last updated timestamp
    *   Workflow ID
*   **Actions**:
    *   **New Workflow Button**: Located at the top-right, this button will navigate you to the "Templates" page to start a new workflow.
    *   **View Details**: Each workflow card has a "View Details" button (or clicking the name) that takes you to the Workflow Detail Page.
    *   **Retry (Conditional)**: For workflows that have `FAILED`, a "Retry" button might appear (functionality depends on backend).
*   **Empty State**: If no workflows exist, you'll see a prompt to create a new one.

## 5. Workflow Detail Page

This page provides an in-depth view of a single workflow.

*   **Header Information**:
    *   Workflow Name and ID.
    *   Indication if it's a branched workflow (with a link to its parent).
    *   **Refresh Button**: Manually re-fetches the latest data for this workflow.
    *   **Branch Button**: Opens a modal to create a new branch from this workflow.
*   **Summary Card**:
    *   Current Status
    *   Creation Date
    *   Last Updated Date
    *   Description
    *   Progress Bar
*   **Tabs**:
    *   **Steps**:
        *   Lists all steps in the workflow.
        *   Each step shows its name, action, ID, status, and an icon.
        *   Clicking a step expands it to show more details: start/end times, duration, dependencies (names and IDs), outputs (as JSON), metadata (tokens, time, cost), errors, and logs.
    *   **Details**:
        *   Provides a comprehensive list of the workflow's properties: ID, Name, Status, Description, Tags, Creation/Update times, Parent ID (if any), and a list of its Branches with links.
    *   **Metrics**:
        *   Displays aggregate metrics for the workflow, such as Total Tokens used, Total Execution Time, and Estimated Cost (if available from the backend).
    *   **DAG (Directed Acyclic Graph)**:
        *   A visual representation of the workflow's steps and their dependencies.
        *   Nodes represent steps, and lines/arrows show the flow of execution.
        *   This helps understand the structure and dependencies within the workflow.

### 5.1. Creating a Workflow Branch

1.  Navigate to the Workflow Detail Page of the workflow you want to branch.
2.  Click the "Branch" button.
3.  A modal will appear:
    *   It will pre-fill a suggested "Branch Name" (e.g., "Original Name Branch X"). You can change this.
    *   Review the information.
4.  Click "Create Branch".
5.  If successful, you'll usually be navigated to the detail page of the newly created branched workflow. The original workflow's "Details" tab will also list this new branch.

## 6. Templates Page

This page allows you to start new workflows using predefined templates.

*   **Display**: Templates are shown as cards, displaying:
    *   Template Name
    *   Description
    *   Category (if defined)
    *   Estimated Duration (if defined)
*   **Actions**:
    *   **Use Template**: Each template card has a "Use Template" button. Clicking this opens a modal.
*   **Using a Template (Modal)**:
    1.  The modal shows the template's name and description.
    2.  If the template requires parameters, input fields will be displayed for each:
        *   **Text Input**: For string parameters (e.g., a prompt, a file path).
        *   **Number Input**: For numerical parameters.
        *   **Checkbox**: For boolean (true/false) parameters.
        *   Required parameters might be indicated.
        *   Parameter descriptions are shown to guide you.
    3.  Fill in the required parameters.
    4.  Click "Create Workflow".
    5.  If successful, a new workflow instance will be created, and you'll typically be redirected to its Workflow Detail Page.
    6.  If there's an error (e.g., missing required parameter, backend issue), an error message will be shown in the modal.

## 7. Interacting with Steps (Workflow Detail Page)

On the "Steps" tab of the Workflow Detail Page:

*   Each step is an expandable item. Click on a step to toggle its details.
*   **Expanded View Shows**:
    *   **Timestamps**: Start and End time of the step.
    *   **Duration**: How long the step took to run.
    *   **Dependencies**: Lists other steps that this step depended on.
    *   **Outputs**: If the step produced any data, it's shown here (often as JSON). This is the data that subsequent steps might use.
    *   **Metadata**: Information like token count (for LLM calls), execution time in seconds, or estimated cost.
    *   **Error**: If the step failed, the error message is displayed here.
    *   **Logs**: Any log messages generated by the step during its execution. Useful for debugging.

This guide covers the main functionalities of the Hybrid Engine Dashboard. As the system evolves, new features and refinements will be added.
