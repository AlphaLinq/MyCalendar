import datetime as dt
import os.path
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]

class CalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Calendar Events")
        self.creds = self.authenticate_google()
        self.events = self.fetch_events()

        # Main Calendar View
        self.calendar = Calendar(self.root, selectmode="day", date_pattern="yyyy-mm-dd")
        self.calendar.pack(pady=20)
        self.calendar.bind("<<CalendarSelected>>", self.show_event_details)

        # Add Event Button
        add_event_button = tk.Button(self.root, text="Add Event", command=self.open_add_event_tab)
        add_event_button.pack(pady=10)

        # Refresh Button
        refresh_button = tk.Button(self.root, text="Refresh Calendar", command=self.refresh_calendar)
        refresh_button.pack(pady=10)

        self.mark_events_on_calendar()

    def authenticate_google(self):
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json")

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)

            with open("token.json", "w") as token:
                token.write(creds.to_json())
        return creds

    def fetch_events(self):
        try:
            service = build("calendar", "v3", credentials=self.creds)
            now = dt.datetime.utcnow().isoformat() + "Z"
            events_result = service.events().list(
                calendarId="primary",
                timeMin=now,
                maxResults=100,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
            return events_result.get("items", [])
        except HttpError as error:
            messagebox.showerror("Error", f"An error occurred: {error}")
            return []

    def mark_events_on_calendar(self):
        for event in self.events:
            date = event["start"].get("dateTime", event["start"].get("date")).split("T")[0]
            self.calendar.calevent_create(dt.datetime.strptime(date, "%Y-%m-%d"), event["summary"], "event")

    def show_event_details(self, event):
        selected_date = self.calendar.get_date()
        events_on_date = [
            e["summary"]
            for e in self.events
            if e["start"].get("dateTime", e["start"].get("date")).split("T")[0] == selected_date
        ]
        if events_on_date:
            messagebox.showinfo("Events", "\n".join(events_on_date))
        else:
            messagebox.showinfo("Events", "No events on this date.")

    def open_add_event_tab(self):
        add_event_window = tk.Toplevel(self.root)
        add_event_window.title("Add Event")

        tk.Label(add_event_window, text="Event Title:").pack(pady=5)
        title_entry = tk.Entry(add_event_window, width=30)
        title_entry.pack(pady=5)

        tk.Label(add_event_window, text="Event Date (YYYY-MM-DD):").pack(pady=5)
        date_entry = tk.Entry(add_event_window, width=30)
        date_entry.pack(pady=5)

        tk.Label(add_event_window, text="Event Time (HH:MM, optional):").pack(pady=5)
        time_entry = tk.Entry(add_event_window, width=30)
        time_entry.pack(pady=5)

        def add_event():
            title = title_entry.get()
            date = date_entry.get()
            time = time_entry.get()
            if not title or not date:
                messagebox.showerror("Error", "Title and Date are required.")
                return

            try:
                service = build("calendar", "v3", credentials=self.creds)
                event = {
                    "summary": title,
                    "start": {"dateTime": f"{date}T{time}:00", "timeZone": "UTC"} if time else {"date": date},
                    "end": {"dateTime": f"{date}T{time}:00", "timeZone": "UTC"} if time else {"date": date},
                }
                service.events().insert(calendarId="primary", body=event).execute()
                messagebox.showinfo("Success", "Event added successfully!")
                add_event_window.destroy()
                self.refresh_calendar()
            except HttpError as error:
                messagebox.showerror("Error", f"An error occurred: {error}")

        tk.Button(add_event_window, text="Add Event", command=add_event).pack(pady=10)

    def refresh_calendar(self):
        self.events = self.fetch_events()
        self.calendar.calevent_remove("all")
        self.mark_events_on_calendar()


if __name__ == "__main__":
    root = tk.Tk()
    app = CalendarApp(root)
    root.mainloop()