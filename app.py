from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import uuid
import json
import re
from collections import defaultdict

app = Flask(__name__)

# Enhanced task storage with metadata
tasks = {}
categories = ["Work", "Personal", "Shopping", "Health", "Learning", "Other","Coding"]
task_stats = defaultdict(int)

class TaskManager:
    @staticmethod
    def create_task(title, description="", category="Other", priority="Medium", due_date=None):
        task_id = str(uuid.uuid4())[:8]
        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "category": category,
            "priority": priority,
            "status": "Pending",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "due_date": due_date,
            "completed_at": None,
            "tags": []
        }
        tasks[task_id] = task
        task_stats['total'] += 1
        task_stats[category.lower()] += 1
        return task

    @staticmethod
    def complete_task(task_id):
        if task_id in tasks:
            tasks[task_id]["status"] = "Completed"
            tasks[task_id]["completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            task_stats['completed'] += 1
            return True
        return False

    @staticmethod
    def delete_task(task_id):
        if task_id in tasks:
            category = tasks[task_id]["category"]
            del tasks[task_id]
            task_stats['total'] -= 1
            task_stats[category.lower()] -= 1
            return True
        return False

    @staticmethod
    def search_tasks(query):
        results = []
        for task in tasks.values():
            if (query.lower() in task["title"].lower() or 
                query.lower() in task["description"].lower() or
                query.lower() in task["category"].lower()):
                results.append(task)
        return results

    @staticmethod
    def get_overdue_tasks():
        overdue = []
        today = datetime.now().date()
        for task in tasks.values():
            if (task["due_date"] and task["status"] != "Completed" and
                datetime.strptime(task["due_date"], "%Y-%m-%d").date() < today):
                overdue.append(task)
        return overdue

class ChatBot:
    def __init__(self):
        self.conversation_state = {}
        self.waiting_for = None
        self.temp_data = {}

    def process_message(self, message, session_id="default"):
        user_msg = message.lower().strip()
        
        # Handle conversation flow
        if session_id in self.conversation_state:
            return self.handle_conversation_flow(user_msg, session_id)
        
        # Natural language processing
        return self.process_natural_language(user_msg, session_id)

    def handle_conversation_flow(self, message, session_id):
        state = self.conversation_state[session_id]
        
        if state == "adding_task":
            return self.handle_task_creation(message, session_id)
        elif state == "deleting_task":
            return self.handle_task_deletion(message, session_id)
        elif state == "searching":
            return self.handle_search(message, session_id)
        
        # Clear state if unrecognized
        del self.conversation_state[session_id]
        return self.get_help_message()

    def handle_task_creation(self, message, session_id):
        if message == "cancel":
            del self.conversation_state[session_id]
            return {"response": "Task creation cancelled.", "type": "info"}
        
        if "temp_task" not in self.temp_data:
            self.temp_data["temp_task"] = {}
        
        temp_task = self.temp_data["temp_task"]
        
        if "title" not in temp_task:
            temp_task["title"] = message
            return {
                "response": "Great! Now enter a description (or type 'skip'):",
                "type": "input"
            }
        elif "description" not in temp_task:
            temp_task["description"] = "" if message == "skip" else message
            return {
                "response": f"Select category: {', '.join(categories)} (or type 'skip' for 'Other'):",
                "type": "input"
            }
        elif "category" not in temp_task:
            category = message.title() if message.title() in categories else "Other"
            temp_task["category"] = category
            return {
                "response": "Set priority (High/Medium/Low) or type 'skip':",
                "type": "input"
            }
        elif "priority" not in temp_task:
            priority = message.title() if message.title() in ["High", "Medium", "Low"] else "Medium"
            temp_task["priority"] = priority
            return {
                "response": "Set due date (YYYY-MM-DD format) or type 'skip':",
                "type": "input"
            }
        else:
            # Final step - due date
            due_date = None
            if message != "skip":
                try:
                    datetime.strptime(message, "%Y-%m-%d")
                    due_date = message
                except ValueError:
                    pass
            
            # Create the task
            task = TaskManager.create_task(
                title=temp_task["title"],
                description=temp_task["description"],
                category=temp_task["category"],
                priority=temp_task["priority"],
                due_date=due_date
            )
            
            # Clean up
            del self.conversation_state[session_id]
            del self.temp_data["temp_task"]
            
            return {
                "response": f"✅ Task '{task['title']}' created successfully!\n"
                           f"📋 ID: {task['id']}\n"
                           f"📁 Category: {task['category']}\n"
                           f"⚡ Priority: {task['priority']}",
                "type": "success",
                "task": task
            }

    def handle_task_deletion(self, message, session_id):
        if message == "cancel":
            del self.conversation_state[session_id]
            return {"response": "Deletion cancelled.", "type": "info"}
        
        # Try to find task by ID or title
        task_to_delete = None
        if message in tasks:
            task_to_delete = tasks[message]
        else:
            # Search by title
            for task in tasks.values():
                if message.lower() in task["title"].lower():
                    task_to_delete = task
                    break
        
        if task_to_delete:
            TaskManager.delete_task(task_to_delete["id"])
            del self.conversation_state[session_id]
            return {
                "response": f"🗑️ Task '{task_to_delete['title']}' deleted successfully!",
                "type": "success"
            }
        else:
            return {
                "response": "❌ Task not found. Please enter a valid task ID or title (or type 'cancel'):",
                "type": "error"
            }

    def handle_search(self, message, session_id):
        del self.conversation_state[session_id]
        results = TaskManager.search_tasks(message)
        
        if results:
            response = f"🔍 Found {len(results)} task(s):\n\n"
            for task in results:
                status_emoji = "✅" if task["status"] == "Completed" else "⏳"
                priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(task["priority"], "⚪")
                response += f"{status_emoji} {priority_emoji} **{task['title']}**\n"
                response += f"   📋 ID: {task['id']} | 📁 {task['category']}\n\n"
            return {"response": response, "type": "success", "tasks": results}
        else:
            return {"response": f"❌ No tasks found matching '{message}'", "type": "info"}

    def process_natural_language(self, message, session_id):
        # Greetings
        if any(greeting in message for greeting in ["hi", "hello", "hey", "whatsup", "start"]):
            return {
                "response": "👋 Welcome to TaskMaster Pro!\n\n"
                           "🎯 I can help you manage tasks efficiently. Here's what I can do:\n"
                           "• **Add tasks** - 'add task', 'create new task'\n"
                           "• **View tasks** - 'show tasks', 'list all', 'my tasks'\n"
                           "• **Complete tasks** - 'complete [task]', 'done [task]'\n"
                           "• **Delete tasks** - 'delete [task]', 'remove [task]'\n"
                           "• **Search tasks** - 'find [keyword]', 'search [term]'\n"
                           "• **Get stats** - 'stats', 'dashboard', 'summary'\n"
                           "• **Show overdue** - 'overdue tasks'\n\n"
                           "What would you like to do?",
                "type": "welcome"
            }
        
        # Add task commands
        if any(cmd in message for cmd in ["add", "create", "new task"]):
            if "add " in message:
                # Quick add
                task_title = message.replace("add ", "").strip()
                if task_title:
                    task = TaskManager.create_task(task_title)
                    return {
                        "response": f"⚡ Quick task added: '{task['title']}'\n📋 ID: {task['id']}",
                        "type": "success",
                        "task": task
                    }
            
            # Interactive add
            self.conversation_state[session_id] = "adding_task"
            return {
                "response": "📝 Let's create a new task! Enter the task title:",
                "type": "input"
            }
        
        # View tasks
        if any(cmd in message for cmd in ["show", "list", "view", "my tasks", "all tasks"]):
            if not tasks:
                return {"response": "📭 No tasks found. Create your first task!", "type": "info"}
            
            response = f"📋 **Your Tasks** ({len(tasks)} total):\n\n"
            
            # Group by status
            pending_tasks = [t for t in tasks.values() if t["status"] == "Pending"]
            completed_tasks = [t for t in tasks.values() if t["status"] == "Completed"]
            
            if pending_tasks:
                response += "⏳ **Pending Tasks:**\n"
                for task in sorted(pending_tasks, key=lambda x: x["priority"], reverse=True):
                    priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(task["priority"], "⚪")
                    due_info = f" | 📅 Due: {task['due_date']}" if task["due_date"] else ""
                    response += f"{priority_emoji} **{task['title']}**\n"
                    response += f"   📋 ID: {task['id']} | 📁 {task['category']}{due_info}\n\n"
            
            if completed_tasks:
                response += "✅ **Completed Tasks:**\n"
                for task in completed_tasks[-5:]:  # Show last 5 completed
                    response += f"✅ **{task['title']}** (Completed: {task['completed_at']})\n\n"
            
            return {"response": response, "type": "success", "tasks": list(tasks.values())}
        
        # Complete task
        if any(cmd in message for cmd in ["complete", "done", "finish"]):
            task_ref = None
            for cmd in ["complete ", "done ", "finish "]:
                if cmd in message:
                    task_ref = message.replace(cmd, "").strip()
                    break
            
            if task_ref:
                # Find task by ID or title
                task_to_complete = None
                if task_ref in tasks:
                    task_to_complete = tasks[task_ref]
                else:
                    for task in tasks.values():
                        if task_ref.lower() in task["title"].lower():
                            task_to_complete = task
                            break
                
                if task_to_complete:
                    if task_to_complete["status"] == "Completed":
                        return {"response": f"✅ Task '{task_to_complete['title']}' is already completed!", "type": "info"}
                    
                    TaskManager.complete_task(task_to_complete["id"])
                    return {
                        "response": f"🎉 Congratulations! Task '{task_to_complete['title']}' marked as completed!",
                        "type": "success"
                    }
                else:
                    return {"response": f"❌ Task '{task_ref}' not found.", "type": "error"}
            else:
                return {"response": "Please specify which task to complete. Example: 'complete buy groceries'", "type": "info"}
        
        # Delete task
        if any(cmd in message for cmd in ["delete", "remove"]):
            self.conversation_state[session_id] = "deleting_task"
            return {
                "response": "🗑️ Which task would you like to delete? Enter task ID or title (or type 'cancel'):",
                "type": "input"
            }
        
        # Search tasks
        if any(cmd in message for cmd in ["search", "find"]):
            for cmd in ["search ", "find "]:
                if cmd in message:
                    query = message.replace(cmd, "").strip()
                    if query:
                        return self.handle_search(query, session_id)
            
            self.conversation_state[session_id] = "searching"
            return {
                "response": "🔍 What would you like to search for?",
                "type": "input"
            }
        
        # Statistics
        if any(cmd in message for cmd in ["stats", "dashboard", "summary"]):
            total_tasks = len(tasks)
            completed = len([t for t in tasks.values() if t["status"] == "Completed"])
            pending = total_tasks - completed
            overdue = len(TaskManager.get_overdue_tasks())
            
            # Category breakdown
            category_stats = defaultdict(int)
            for task in tasks.values():
                category_stats[task["category"]] += 1
            
            response = "📊 **Task Dashboard:**\n\n"
            response += f"📈 **Overview:**\n"
            response += f"   • Total Tasks: {total_tasks}\n"
            response += f"   • ✅ Completed: {completed}\n"
            response += f"   • ⏳ Pending: {pending}\n"
            response += f"   • ⚠️ Overdue: {overdue}\n\n"
            
            if category_stats:
                response += "📁 **By Category:**\n"
                for category, count in sorted(category_stats.items()):
                    response += f"   • {category}: {count}\n"
            
            completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0
            response += f"\n🎯 **Completion Rate:** {completion_rate:.1f}%"
            
            return {"response": response, "type": "success"}
        
        # Overdue tasks
        if "overdue" in message:
            overdue_tasks = TaskManager.get_overdue_tasks()
            if overdue_tasks:
                response = f"⚠️ **Overdue Tasks** ({len(overdue_tasks)}):\n\n"
                for task in overdue_tasks:
                    days_overdue = (datetime.now().date() - datetime.strptime(task["due_date"], "%Y-%m-%d").date()).days
                    response += f"🔴 **{task['title']}**\n"
                    response += f"   📅 Due: {task['due_date']} ({days_overdue} days overdue)\n"
                    response += f"   📋 ID: {task['id']}\n\n"
                return {"response": response, "type": "warning", "tasks": overdue_tasks}
            else:
                return {"response": "🎉 No overdue tasks! You're doing great!", "type": "success"}
        
        # Help
        if any(cmd in message for cmd in ["help", "commands", "what can you do"]):
            return self.get_help_message()
        
        # Default response
        return {
            "response": "🤔 I didn't understand that. Type 'help' to see available commands, or try:\n"
                       "• 'add task' to create a new task\n"
                       "• 'show tasks' to view your tasks\n"
                       "• 'stats' to see your dashboard",
            "type": "info"
        }

    def get_help_message(self):
        return {
            "response": "🎯 **TaskMaster Pro Commands:**\n\n"
                       "📝 **Task Management:**\n"
                       "• `add [task]` - Quick add task\n"
                       "• `add task` - Interactive task creation\n"
                       "• `show tasks` - View all tasks\n"
                       "• `complete [task]` - Mark task as done\n"
                       "• `delete task` - Remove a task\n\n"
                       "🔍 **Search & Organization:**\n"
                       "• `search [keyword]` - Find tasks\n"
                       "• `stats` - View dashboard\n"
                       "• `overdue tasks` - Show overdue items\n\n"
                       "💡 **Tips:**\n"
                       "• Use task IDs for quick actions\n"
                       "• Set due dates to track deadlines\n"
                       "• Organize with categories and priorities",
            "type": "help"
        }

# Initialize chatbot
chatbot = ChatBot()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get", methods=["POST"])
def chatbot_response():
    user_message = request.form["message"]
    session_id = request.form.get("session_id", "default")
    
    try:
        response_data = chatbot.process_message(user_message, session_id)
        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            "response": f"❌ An error occurred: {str(e)}",
            "type": "error"
        })

@app.route("/api/tasks", methods=["GET"])
def get_tasks_api():
    """REST API endpoint for tasks"""
    return jsonify({
        "tasks": list(tasks.values()),
        "total": len(tasks),
        "stats": dict(task_stats)
    })

@app.route("/api/export", methods=["GET"])
def export_tasks():
    """Export tasks as JSON"""
    export_data = {
        "export_date": datetime.now().isoformat(),
        "tasks": list(tasks.values()),
        "categories": categories,
        "stats": dict(task_stats)
    }
    return jsonify(export_data)

if __name__ == "__main__":
    # Add some sample tasks for demonstration
    TaskManager.create_task("Complete Flask project", "Build an awesome task manager", "Work", "High", "2024-12-31")
    TaskManager.create_task("Buy groceries", "Milk, bread, eggs", "Personal", "Medium", "2024-12-01")
    TaskManager.create_task("Learn Python", "Complete online course", "Learning", "Low")
    
    print("🚀 TaskMaster Pro is starting...")
    print("📋 Sample tasks loaded!")
    print("🌐 Access at: http://localhost:5000")
    
    app.run(debug=True, port=5000)