# Meeting Prep Agent

An AI-powered Meeting Prep Agent that uses Hindsight Memory to remember relationships, commitments, priorities, concerns, and decisions across meetings.

## Problem

Professionals repeatedly meet the same people, but important context from previous meetings is often lost.

This project gives users a "Before You Walk In" meeting brief based on persistent relationship memory.

## Core Idea

Meeting Notes
        ↓
LLM Fact Extraction
        ↓
Hindsight Memory
        ↓
Persistent Relationship Context
        ↓
Recall + Reflect
        ↓
Meeting Brief
        ↓
Better Next Meeting

## Tech Stack

- Python
- FastAPI
- React
- Vite
- SQLite
- Hindsight
- Groq
- Docker

## Core Features

- Meeting memory
- Relationship-aware meeting preparation
- Commitment tracking
- Changed priority detection
- Recent information preference
- Memory Trace
- Meeting Brief generation

## Project Structure

```text
meeting-prep-agent/
├── backend/
├── frontend/
├── data/
├── README.md
├── .gitignore
└── .env.example