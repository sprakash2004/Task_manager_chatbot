# TaskMaster Pro

AI-powered task management web app with natural language chatbot interface.

## Features

- **Natural Language Chat**: Talk to the AI assistant to manage tasks
- **Smart Task Management**: Create, complete, delete, and search tasks
- **Categories & Priorities**: Organize tasks by type and importance
- **Due Date Tracking**: Set deadlines and track overdue tasks
- **Real-time Dashboard**: View task statistics and progress
- **Responsive Design**: Works on desktop and mobile

## Quick Start

1. **Install Flask**
   ```bash
   pip install flask
   ```

2. **Run the app**
   ```bash
   python app.py
   ```

3. **Open browser**
   Go to `http://localhost:5000`

## Usage Examples

- "Add buy groceries tomorrow"
- "Show my tasks"
- "Complete the Flask project"
- "Search for work tasks"
- "Show stats"
- "Delete groceries task"

## Project Structure

```
├── app.py              # Flask backend
├── templates/
│   └── index.html     # Frontend interface
└── README.md          # This file
```

## API Endpoints

- `GET /api/tasks` - Get all tasks and stats
- `GET /api/export` - Export tasks as JSON
- `POST /get` - Chat with AI assistant

## Tech Stack

- **Backend**: Flask, Python
- **Frontend**: HTML, CSS, JavaScript
- **Features**: Real-time chat, task management, statistics

---

Built with Flask and modern web technologies.
