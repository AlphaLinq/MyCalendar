import datetime as dt
import os.path
from calendar import calendar


from google.auth.transport.requests import Request  #Hitelesítés kérésekhez
from google.oauth2.credentials import Credentials   #Hitelesítési adatok kezelése
from google_auth_oauthlib.flow import InstalledAppFlow  #OAth 2.0 hitelesítését kezeli
from googleapiclient.discovery import build         #API-k felfedezése és használata
from googleapiclient.errors import HttpError        #HTTP hibák kezelése

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def main():
    creds = None

    # Credentials to authenticate ourself, -> ebből csinálunk egy tokent amiben benne van minden engedély
    # Ha nem létezik akkor is csinálunk egyet

    # token.json tárolja az access és refresh tokeneket, bejelentkezéskor automatikusan létrejön

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json","w") as token:
            token.write(creds.to_json())

    # Authentication vége

    try:
        service = build("calendar","v3",credentials=creds)
        now = dt.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        print("A 10 kovetkezo esemeny: ")
        events_result = (service.events().list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("Nincsenek kozeledo esemyenek")
            return
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            # start = event["start"].get("dateTime")
            print(start, event["summary"])

        napok = {}
        for event in events:
            datum = event["start"].get("dateTime").split("T")
            datum_str = datum[0]
            if datum_str in napok:
                napok[datum_str] += 1
            else:
                napok[datum_str] = 1

        print("----------------------------------")

        for datum, db in napok.items():
            print(f"{datum}: {db} alkalommal")

    except HttpError as error:
        print("Hiba tortent: ", error)

if __name__ == "__main__":
    main()

