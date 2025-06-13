# Technical Description: Contact Planning and Tracking System

## Overview

This document outlines the technical design for a system dedicated to planning, executing, and tracking contact attempts with leads. This goes beyond simple activity logging by introducing strategic planning, sequencing of touchpoints, and potentially automated assistance for sales and outreach teams. This system will build upon the previously defined `Activities` and `Reminders` structures.

## Core Concepts & Data Models

**1. Contact Strategies/Cadences (New Table):**

*   `strategy_id` (Primary Key, UUID): Unique identifier for each contact strategy.
*   `name` (VARCHAR(255), Not Null): Name of the strategy (e.g., "Initial Outreach Sequence", "Post-Demo Follow-up").
*   `description` (TEXT, Nullable): Detailed description of the strategy.
*   `created_by_user_id` (Foreign Key, References Users(user_id)): User who created this strategy template.
*   `is_template` (BOOLEAN, Default: TRUE): Whether this is a reusable template or a specific plan for one lead.
*   `created_at` (TIMESTAMP, Default: CURRENT_TIMESTAMP): Timestamp of record creation.
*   `updated_at` (TIMESTAMP, Default: CURRENT_TIMESTAMP, On Update: CURRENT_TIMESTAMP): Timestamp of last record update.

**2. Strategy Steps (New Table):**

*   `step_id` (Primary Key, UUID): Unique identifier for each step in a strategy.
*   `strategy_id` (Foreign Key, References Contact_Strategies(strategy_id) ON DELETE CASCADE, Not Null): The strategy this step belongs to.
*   `step_number` (INT, Not Null): Order of this step in the sequence (e.g., 1, 2, 3).
*   `delay_days` (INT, Not Null, Default: 0): Number of days to wait after the previous step's completion (or start of strategy) before this step is due.
*   `activity_type` (VARCHAR(100), Not Null): Suggested type of activity for this step (e.g., 'Email', 'Call', 'LinkedIn Connect').
*   `subject_template` (VARCHAR(255), Nullable): Template for the activity subject (e.g., "Following up on our conversation"). Can include placeholders.
*   `description_template` (TEXT, Nullable): Template for the activity description or email body. Can include placeholders like `{{contact_name}}`, `{{company_name}}`.
*   `is_automated` (BOOLEAN, Default: FALSE): Whether this step can be automated (e.g., sending a templated email).
*   `created_at` (TIMESTAMP, Default: CURRENT_TIMESTAMP): Timestamp of record creation.
*   `updated_at` (TIMESTAMP, Default: CURRENT_TIMESTAMP, On Update: CURRENT_TIMESTAMP): Timestamp of last record update.

**3. Lead Contact Plans (New Table - Linking Strategies to Leads):**

*   `plan_id` (Primary Key, UUID): Unique identifier for a specific lead's contact plan.
*   `company_id` (Foreign Key, References Companies(company_id) ON DELETE CASCADE, Not Null): The target company for this plan.
*   `contact_id` (Foreign Key, References Contacts(contact_id) ON DELETE CASCADE, Nullable): The specific target contact for this plan.
*   `strategy_id` (Foreign Key, References Contact_Strategies(strategy_id) ON DELETE SET NULL, Nullable): The strategy template this plan is based on (if any). A plan can also be custom.
*   `user_id` (Foreign Key, References Users(user_id), Not Null): The user responsible for executing this plan.
*   `status` (VARCHAR(50), Not Null, Default: 'Not Started'): Current status of the plan (e.g., 'Not Started', 'In Progress', 'Completed', 'Paused', 'Aborted').
*   `current_step_id` (Foreign Key, References Strategy_Steps(step_id) ON DELETE SET NULL, Nullable): The current active or last completed step in the plan.
*   `plan_start_date` (TIMESTAMP, Default: CURRENT_TIMESTAMP): When the plan was initiated for the lead.
*   `next_step_due_date` (TIMESTAMP, Nullable): Calculated due date for the next action.
*   `created_at` (TIMESTAMP, Default: CURRENT_TIMESTAMP): Timestamp of record creation.
*   `updated_at` (TIMESTAMP, Default: CURRENT_TIMESTAMP, On Update: CURRENT_TIMESTAMP): Timestamp of last record update.

**Relationship to Existing Tables:**

*   `Activities` can be linked to a `Lead_Contact_Plans.plan_id` and/or a `Strategy_Steps.step_id` to track execution of planned steps.
*   `Reminders` can be automatically generated based on `next_step_due_date` in `Lead_Contact_Plans`.

## Key Functionalities

**1. Strategy Creation & Management:**

*   Users can define reusable `Contact_Strategies` with multiple `Strategy_Steps`.
*   Steps include details like delay from the previous step, activity type, and message templates.
*   Support for placeholders in templates (e.g., `{{contact.first_name}}`, `{{company.name}}`, `{{user.signature}}`).

**2. Assigning Plans to Leads:**

*   Users can assign a `Contact_Strategy` (template) to a specific `Company` or `Contact`, creating a `Lead_Contact_Plan`.
*   Alternatively, users can build a custom, one-off plan for a lead.

**3. Plan Execution & Tracking:**

*   The system displays the `next_step_due_date` and details for each active `Lead_Contact_Plan`.
*   When a user logs an `Activity` that corresponds to a planned step, the system can automatically advance the `Lead_Contact_Plan` to the next step and update its `status`.
*   The `next_step_due_date` for the subsequent step is calculated based on the `delay_days`.

**4. Automated Scheduling & Reminders:**

*   **Automated Reminders:** Based on the `next_step_due_date` in `Lead_Contact_Plans`, the system automatically creates `Reminders` for the assigned `user_id`. This leverages the existing reminder notification system.
*   **Task List Generation:** Users get a clear view of their due and upcoming planned activities.

**5. Follow-up Suggestions:**

*   **Rule-Based Suggestions:**
    *   If an email activity is logged and there's no reply logged within X days, suggest a follow-up call.
    *   If a "Voicemail Left" outcome is logged, suggest trying again in Y days.
*   **Based on Plan Progress:** The system naturally guides users through the predefined steps of a contact strategy.
*   **Data-Driven Suggestions (Advanced):**
    *   Analyze historical activity data and outcomes to suggest which types of follow-ups are most effective for certain lead profiles or after specific interactions. (e.g., "Leads in the 'Technology' industry respond well to a LinkedIn message 2 days after an initial email."). This requires data analytics capabilities.

**6. Automation of Steps (Optional & Careful Implementation):**

*   For `Strategy_Steps` marked `is_automated` (e.g., sending a templated email):
    *   **Mechanism:** A background worker (e.g., Celery) checks for due automated steps.
    *   It populates templates with lead/user data and uses an integrated email service (e.g., SendGrid, AWS SES, or direct SMTP) to send the communication.
    *   The corresponding `Activity` is automatically logged.
    *   **Crucial Safeguards:**
        *   Strict opt-out mechanisms for leads.
        *   Rate limiting to avoid spamming.
        *   Personalization checks to ensure templates don't look overly generic.
        *   Clear approval workflows before enabling fully automated sending, or user-initiated automation ("Send this automated email now").

## Technical Considerations

*   **API Endpoints:**
    *   CRUD for `Contact_Strategies` and `Strategy_Steps`.
    *   CRUD for `Lead_Contact_Plans` (assigning, starting, pausing, updating status).
    *   Endpoints to list a user's due/upcoming planned activities.
    *   Endpoints to log activities against planned steps.
*   **Background Jobs/Schedulers:**
    *   To calculate `next_step_due_date` and create `Reminders`.
    *   To process any automated steps (if implemented).
    *   To generate follow-up suggestions based on rules.
*   **Template Engine:** A robust template engine (e.g., Jinja2 for Python, Handlebars for Node.js) is needed for populating message templates.
*   **User Interface:**
    *   Visual editor for creating and managing contact strategies.
    *   Dashboard for users to see their active `Lead_Contact_Plans` and due tasks.
    *   Easy way to log activities and link them to planned steps.
    *   Clear display of follow-up suggestions.
*   **Database Design:**
    *   Indexes on foreign keys, `status`, and `next_step_due_date` in `Lead_Contact_Plans`.
    *   Indexes on `strategy_id` and `step_number` in `Strategy_Steps`.

## Analytics & Reporting

*   Track conversion rates of different contact strategies.
*   Identify bottlenecks or effective steps within strategies.
*   Measure user adherence to planned activities.

This system aims to bring more structure and intelligence to the lead engagement process, helping sales teams be more efficient and effective. The rollout can be phased, starting with manual strategy execution and gradually introducing automation and more sophisticated suggestions.
