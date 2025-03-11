"""
Scheduler driver for mqHome
Allows scheduling commands to be executed at specific times

Usage:
    Schedule commands to run at specific times using cron-like syntax
    Supports: 
    - Specific time of day (HH:MM)
    - Every X hours/minutes
    - Specific days of week
    - One-time schedules

Init options:
    timezone: int = 0 (UTC offset in hours)
    tasks: list = [] (List of initial scheduled tasks)

Commands:
    add_task(time, command, args={}, days=None) - Add a new scheduled task
    remove_task(task_id) - Remove a task by ID
    list_tasks() - Get list of all scheduled tasks
    clear_tasks() - Remove all tasks
    
Properties:
    tasks - List of current scheduled tasks
    next_run - Time until next scheduled task
"""

import time
from machine import RTC
import json
from peripheral import peripheral


class scheduler(peripheral):
    def __init__(self, mqtt=None, initOptions=None):
        super().__init__(initOptions)
        self.rtc = RTC()

        # Default options
        self.options = {
            "timezone": 0,
            "tasks": []
        }

        # Override with provided options
        if initOptions:
            self.options.update(initOptions)

        self.tasks = []
        self._load_tasks()

        # Start checking schedule
        self._last_check = 0

    def _load_tasks(self):
        """Load tasks from options"""
        for task in self.options["tasks"]:
            self.add_task(**task)

    def _parse_time(self, time_str):
        """Parse time string into hour/minute tuple"""
        if ":" in time_str:
            # HH:MM format
            h, m = time_str.split(":")
            return (int(h), int(m))
        elif "h" in time_str:
            # Every X hours
            h = int(time_str.replace("h", ""))
            return ("*/{}".format(h), 0)
        elif "m" in time_str:
            # Every X minutes
            m = int(time_str.replace("m", ""))
            return (None, "*/{}".format(m))
        return None

    def add_task(self, time, command, args={}, days=None):
        """
        Add a scheduled task
        time: "HH:MM" or "Xh" or "Xm" for every X hours/minutes
        command: Command to execute (dev[id]/command or mqtt message)
        args: Command arguments
        days: List of days (0-6, 0=Monday) or None for every day
        """
        task = {
            "id": len(self.tasks),
            "time": self._parse_time(time),
            "command": command,
            "args": args,
            "days": days,
            "last_run": 0
        }
        self.tasks.append(task)
        return task["id"]

    def remove_task(self, task_id):
        """Remove task by ID"""
        self.tasks = [t for t in self.tasks if t["id"] != task_id]

    def list_tasks(self):
        """Get list of all tasks"""
        return self.tasks

    def clear_tasks(self):
        """Remove all tasks"""
        self.tasks = []

    def _should_run(self, task):
        """Check if task should run now"""
        now = time.localtime()

        # Check day
        if task["days"] is not None:
            if now[6] not in task["days"]:
                return False

        # Check time
        h, m = task["time"]

        if isinstance(h, str) and h.startswith("*/"):
            # Every X hours
            interval = int(h[2:])
            if now[3] % interval != 0 or now[4] != m:
                return False
        elif isinstance(m, str) and m.startswith("*/"):
            # Every X minutes
            interval = int(m[2:])
            if now[4] % interval != 0:
                return False
        else:
            # Specific time
            if now[3] != h or now[4] != m:
                return False

        # Prevent multiple runs in same minute
        if task["last_run"] == now[4]:
            return False

        return True

    def _execute_task(self, task):
        """Execute a scheduled task"""
        cmd = task["command"]
        args = task["args"]

        if cmd.startswith("dev["):
            # Device command
            dev_id = int(cmd[4:cmd.find("]")])
            command = cmd[cmd.find("/")+1:]
            if hasattr(self.mqtt, "peripherals"):
                self.mqtt.peripherals[dev_id].command(command, args)
        else:
            # MQTT message
            if self.mqtt:
                self.mqtt.publish(cmd, json.dumps(args))

        # Update last run time
        task["last_run"] = time.localtime()[4]
        self.onExecuteTask(task)

    def process(self):
        """Check and execute scheduled tasks"""
        now = time.time()

        # Check once per minute
        if now - self._last_check < 60:
            return

        self._last_check = now

        # Check all tasks
        for task in self.tasks:
            if self._should_run(task):
                self._execute_task(task)

    @property
    def next_run(self):
        """Get time until next scheduled task"""
        now = time.localtime()
        next_time = None

        for task in self.tasks:
            h, m = task["time"]

            if isinstance(h, str) or isinstance(m, str):
                # Recurring task, max 1 hour wait
                if next_time is None or next_time > 3600:
                    next_time = 3600
            else:
                # Calculate time until this task
                task_time = h * 3600 + m * 60
                current_time = now[3] * 3600 + now[4] * 60

                wait = task_time - current_time
                if wait < 0:
                    wait += 24 * 3600

                if next_time is None or wait < next_time:
                    next_time = wait

        return next_time if next_time is not None else 24 * 3600

    def commandsList(self):
        """Return list of available commands"""
        return ["add_task", "remove_task", "list_tasks", "clear_tasks", "process"]

    def getState(self):
        """Return current state for the web interface"""
        return {
            "tasks": self.tasks,
            "next_run": self.next_run
        }

    @peripheral._trigger
    def onExecuteTask(self, task):
        pass

    def getObservableMethods(self):
        return ["onExecuteTask"]

    def getObservableProperties(self):
        return []
