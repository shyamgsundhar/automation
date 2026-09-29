# Tech News Automation Bot

An automated technology and AI news aggregator built with Python. It
collects articles from RSS feeds, filters and deduplicates them,
generates concise AI-powered summaries, and delivers the results to a
Discord channel.

The workflow runs on a schedule through GitHub Actions, so the bot can
operate without keeping a local machine running.

## Table of Contents

-   [Overview](#overview)
-   [Features](#features)
-   [How It Works](#how-it-works)
-   [Technology Stack](#technology-stack)
-   [Project Structure](#project-structure)
-   [Prerequisites](#prerequisites)
-   [Configuration](#configuration)
-   [Run Locally](#run-locally)
-   [Automated Execution](#automated-execution)
-   [Database and Duplicate
    Prevention](#database-and-duplicate-prevention)
-   [Troubleshooting](#troubleshooting)
-   [Security Notes](#security-notes)
-   [Future Improvements](#future-improvements)

## Overview

Keeping up with technology news often means checking multiple websites
and feeds throughout the day. This project automates that routine by
gathering news from configured RSS sources, preparing short summaries
with AI APIs, and posting the results to Discord.

The summaries are written in conversational Tamil transliteration
(Thanglish), making the updates quick and approachable to read.

## Features

-   **RSS-based collection:** Fetches technology and AI articles from
    configured RSS feeds.
-   **Fresh-article filtering:** Processes eligible articles and filters
    out previously sent links.
-   **Duplicate prevention:** Stores sent article URLs in PostgreSQL so
    the same article is not repeatedly posted.
-   **AI-powered summaries:** Uses Groq and NVIDIA API integrations to
    generate concise article summaries.
-   **Discord delivery:** Publishes summarized news to a configured
    Discord channel through a webhook.
-   **Scheduled automation:** Runs twice daily using GitHub Actions.
-   **Manual workflow execution:** Supports manually starting the GitHub
    Actions workflow for testing or an on-demand run.
-   **Secret-based configuration:** Keeps API keys, webhook URLs, and
    database credentials outside the source code.

## How It Works

``` text
Configured RSS Feeds
        |
        v
Fetch Articles
        |
        v
Filter Fresh Articles
        |
        v
Check Previously Sent URLs
        |
        v
Retrieve Article Content
        |
        v
Generate AI Summary
        |
        v
Post Summary to Discord
        |
        v
Store Sent Article URL in PostgreSQL
```

## Technology Stack

  Component           Technology
  ------------------- ----------------------------------------
  Language            Python
  News collection     RSS feeds
  AI summarization    Groq API and NVIDIA API
  Database            PostgreSQL (Neon)
  Notifications       Discord Webhooks
  Scheduling and CI   GitHub Actions
  Configuration       Environment variables / GitHub Secrets

## Project Structure

``` text
.
├── app/
│   ├── article.py       # Article content retrieval
│   ├── config.py        # Application configuration
│   ├── database.py      # PostgreSQL connection and persistence
│   ├── discord.py       # Discord webhook delivery
│   ├── feeds.py         # RSS feed collection
│   ├── filter.py        # Article filtering and selection
│   ├── main.py          # Application entry point and orchestration
│   ├── summarizer.py    # AI-powered summary generation
│   └── check_api.py     # API connectivity diagnostic utility
├── .github/
│   └── workflows/
│       └── tech-news.yaml
├── requirements.txt
└── .env                 # Local environment variables (not committed)
```

## Prerequisites

Before running the project, make sure you have:

-   Python installed (the GitHub Actions workflow currently uses Python
    3.14).
-   A Groq API key.
-   An NVIDIA API key.
-   A Discord webhook URL for the destination channel.
-   A PostgreSQL database URL (for example, a Neon PostgreSQL connection
    string).
-   Git, if you plan to clone and run the repository locally.

## Configuration

Create a `.env` file in the project root for local execution. Add the
environment variables expected by the application:

``` dotenv
GROQ_API_KEY=your_groq_api_key
NVIDIA_API_KEY=your_nvidia_api_key
DISCORD_WEBHOOK_URL=your_discord_webhook_url
DATABASE_URL=your_postgresql_connection_string
```

Replace each placeholder with your own value. Do not commit `.env` or
share secret values.

The same values must be configured as repository Actions secrets for
scheduled GitHub Actions runs:

`GROQ_API_KEY`, `NVIDIA_API_KEY`, `DISCORD_WEBHOOK_URL`, and
`DATABASE_URL`.

## Run Locally

1.  Clone the repository:

    ``` bash
    git clone https://github.com/shyamgsundhar/automation.git
    cd automation
    ```

2.  Create and activate a virtual environment.

    **Windows PowerShell**

    ``` powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```

    **macOS / Linux**

    ``` bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  Install dependencies:

    ``` bash
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    ```

4.  Add the required values to `.env`.

5.  Run the bot from the repository root:

    ``` bash
    python -m app.main
    ```

To run the API connectivity diagnostic:

``` bash
python -m app.check_api
```

The diagnostic checks API connectivity; it does not by itself guarantee
that every model completion request will succeed.

## Automated Execution

The GitHub Actions workflow is located at:

``` text
.github/workflows/tech-news.yaml
```

It is configured to run at:

-   **6:00 AM IST** (00:30 UTC)
-   **6:00 PM IST** (12:30 UTC)

The workflow can also be started manually from the repository's
**Actions** tab using **Run workflow**.

For scheduled execution, add the required credentials under:

**Repository → Settings → Secrets and variables → Actions**

Do not put API keys or connection strings directly into the YAML file.

## Database and Duplicate Prevention

The application uses PostgreSQL to persist sent article URLs. This helps
prevent the same article from being posted repeatedly across scheduled
runs.

The database connection is supplied through `DATABASE_URL`. Ensure the
database is reachable by the environment running the bot and that the
application has the required permissions.

## Troubleshooting

### API key formatting errors

If a workflow reports an invalid HTTP header or whitespace/control
characters in a secret, check the corresponding GitHub Actions secret
for accidental leading/trailing whitespace or newline characters.
Re-enter the secret carefully, or use the workflow's normalization logic
if configured.

Never print the full secret value in workflow logs.

### API connectivity succeeds but summarization fails

A successful connectivity check confirms only that the tested endpoint
is reachable. The actual chat-completion request can still fail because
of model availability, request errors, rate limits, timeouts, or
provider-side issues. Review the application logs for the specific
exception.

### No news appears in Discord

Check that: - The Discord webhook URL is configured correctly. - RSS
feeds are reachable and returning articles. - Articles are not being
excluded as duplicates or by filtering rules. - The workflow completed
successfully and the application logs show a successful Discord
delivery.

## Security Notes

-   Keep `.env` out of version control.
-   Store API keys, database credentials, and Discord webhook URLs in
    GitHub Actions Secrets for cloud execution.
-   Never include secret values in screenshots, README examples,
    commits, or logs.
-   Rotate a credential if it is accidentally exposed.

## Future Improvements

Potential next steps for the project include: - Add configurable topic
categories and source prioritization. - Improve retry handling and
structured logging for external API failures. - Add automated tests for
filtering, deduplication, and message formatting. - Track run metrics
such as articles fetched, summarized, skipped, and delivered. - Add
configurable summary language and length.
