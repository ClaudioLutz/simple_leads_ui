# Technical Description: Lead Interaction and Activity Tracking

## Overview

This document outlines the technical design for a system to track interactions and activities related to leads (potential companies or contacts). This feature is crucial for sales and business development teams to manage their pipeline, set reminders, and maintain a history of communication.

## Core Entities & Data Models

We will extend the existing database schema (assuming a `Companies` table and potentially a `Contacts` table associated with companies).

**1. Activities Table:**

*   `activity_id` (Primary Key, UUID): Unique identifier for each activity.
*   `company_id` (Foreign Key, References Companies(company_id) ON DELETE SET NULL, Nullable): Associated company.
*   `contact_id` (Foreign Key, References Contacts(contact_id) ON DELETE SET NULL, Nullable): Associated contact (if applicable, assuming a `Contacts` table exists or will be created).
*   `user_id` (Foreign Key, References Users(user_id), Not Null): The user/salesperson who performed or is responsible for the activity.
*   `activity_type` (VARCHAR(100), Not Null): Type of activity (e.g., 'Call', 'Email', 'Meeting', 'LinkedIn Message', 'Note', 'Demo').
*   `subject` (VARCHAR(255), Nullable): A brief subject or title for the activity (e.g., "Follow-up call regarding pricing").
*   `description` (TEXT, Nullable): Detailed notes about the activity, outcome, or next steps.
*   `activity_timestamp` (TIMESTAMP, Not Null, Default: CURRENT_TIMESTAMP): Date and time the activity occurred or is scheduled for.
*   `duration_minutes` (INT, Nullable): Duration of the activity in minutes (e.g., for calls or meetings).
*   `outcome` (VARCHAR(255), Nullable): Result of the activity (e.g., 'Interested', 'Not Interested', 'Voicemail Left', 'Demo Scheduled').
*   `created_at` (TIMESTAMP, Default: CURRENT_TIMESTAMP): Timestamp of record creation.
*   `updated_at` (TIMESTAMP, Default: CURRENT_TIMESTAMP, On Update: CURRENT_TIMESTAMP): Timestamp of last record update.

**2. Reminders Table:**

*   `reminder_id` (Primary Key, UUID): Unique identifier for each reminder.
*   `activity_id` (Foreign Key, References Activities(activity_id) ON DELETE CASCADE, Nullable): Optional link to a specific activity this reminder is for. This allows for reminders on past activities (e.g., "follow up on email sent last week") or future scheduled ones.
*   `company_id` (Foreign Key, References Companies(company_id) ON DELETE CASCADE, Nullable): Associated company for the reminder.
*   `contact_id` (Foreign Key, References Contacts(contact_id) ON DELETE CASCADE, Nullable): Associated contact for the reminder.
*   `user_id` (Foreign Key, References Users(user_id), Not Null): The user who needs to be reminded.
*   `reminder_datetime` (TIMESTAMP, Not Null): Date and time the user should be reminded.
*   `notes` (TEXT, Nullable): Specific instructions or notes for the reminder.
*   `status` (VARCHAR(50), Not Null, Default: 'Pending'): Status of the reminder (e.g., 'Pending', 'Dismissed', 'Completed').
*   `notification_sent` (BOOLEAN, Default: FALSE): Flag to track if a notification has been dispatched.
*   `created_at` (TIMESTAMP, Default: CURRENT_TIMESTAMP): Timestamp of record creation.
*   `updated_at` (TIMESTAMP, Default: CURRENT_TIMESTAMP, On Update: CURRENT_TIMESTAMP): Timestamp of last record update.

**Relationships:**

*   A `Company` can have many `Activities` and many `Reminders`.
*   A `Contact` (if implemented) can have many `Activities` and many `Reminders`.
*   A `User` can have many `Activities` and many `Reminders`.
*   An `Activity` can have multiple `Reminders` (e.g., remind 1 day before, then 1 hour before a scheduled meeting).

## Key Functionalities

**1. Activity Logging:**

*   Manual entry of activities by users (calls, meetings, notes).
*   Automated logging for certain activities (e.g., emails sent via an integrated system).
*   Ability to associate activities with specific companies and/or contacts.

**2. Reminder Management:**

*   Users can set reminders for themselves related to companies, contacts, or specific activities.
*   Scheduled reminders trigger notifications.
*   Users can view, manage, and dismiss their pending reminders.

**3. Notification System (for Reminders):**

*   **In-App Notifications:** Display reminders within the application interface.
*   **Email Notifications:** Send email alerts for upcoming or overdue reminders.
*   **Push Notifications (Mobile/Desktop):** If applicable, for more immediate attention.
*   **Mechanism:**
    *   A background job/scheduler (e.g., Celery with RabbitMQ/Redis, or a cron job running a script) will periodically query the `Reminders` table for pending reminders where `reminder_datetime` is near and `notification_sent` is false.
    *   Upon finding such reminders, it will trigger the appropriate notification mechanisms (email, in-app, push) and update `notification_sent` to true.

**4. Calendar Integration (Optional but Recommended):**

*   **Objective:** Allow users to sync scheduled activities (like meetings or demos) with their primary calendars (e.g., Google Calendar, Outlook Calendar).
*   **Methods:**
    *   **OAuth 2.0:** Users authorize the application to access their calendar. The application can then create, update, or delete calendar events corresponding to activities.
    *   **.ics File Export/Import:** Allow users to download an .ics file for an activity to manually import into their calendar, or subscribe to an .ics feed of their activities. This is simpler but less integrated.
*   **Synchronization:**
    *   **Two-way Sync (Complex):** Changes in the application update the calendar, and changes in the calendar (e.g., rescheduling) update the application. This requires careful handling of conflicts and event mapping.
    *   **One-way Sync (Simpler):** Application pushes activities to the calendar.
*   **Data to Sync:** Activity subject, description, start/end times (derived from `activity_timestamp` and `duration_minutes`), attendees (if contact information is available).

**5. Communication Tool Integration (Optional):**

*   **Objective:** Log communications from external tools (e.g., email clients, messaging platforms) as activities.
*   **Methods:**
    *   **Email Forwarding/BCC:** Provide users with a unique email address. When they BCC or forward emails to this address, the system parses the email and creates an activity.
    *   **Browser Extensions/Plugins:** A browser extension could allow users to log emails or LinkedIn messages with a click, sending data to the application's API.
    *   **Direct API Integrations (Complex):** Integrate with APIs of services like Gmail, Outlook 365, or Slack if available and permitted. This requires handling authentication (OAuth) and parsing various data formats.

## Technical Considerations

*   **API Endpoints:**
    *   CRUD operations for `Activities` and `Reminders`.
    *   Endpoints to list activities/reminders by company, contact, or user.
    *   Endpoints for managing reminder status (dismiss, complete).
*   **Database Performance:**
    *   Index foreign keys (`company_id`, `contact_id`, `user_id`) and timestamp fields (`activity_timestamp`, `reminder_datetime`) in the `Activities` and `Reminders` tables for efficient querying.
    *   Index `status` and `notification_sent` on the `Reminders` table for the notification job.
*   **User Interface:**
    *   Clear forms for logging activities and setting reminders.
    *   Timeline views to show history of interactions for a company/contact.
    *   A dedicated section for users to manage their upcoming and overdue reminders.
*   **Security & Privacy:**
    *   Ensure that users can only access and manage activities and reminders relevant to their permissions.
    *   If integrating with external services, securely store API keys and tokens (e.g., using HashiCorp Vault or cloud provider's secret management). Handle user OAuth tokens with care.

## Scalability

*   The notification system should be designed to handle a growing number of users and reminders. Using a message queue for dispatching notifications can improve resilience and scalability.
*   For high-volume activity logging, consider asynchronous processing to avoid blocking user interactions.

This design provides a comprehensive framework for tracking lead interactions. The choice of integrations (calendar, communication tools) can be phased based on priority and available resources.
