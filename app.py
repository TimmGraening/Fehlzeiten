import streamlit as st
from webuntis import WebUntis
from datetime import datetime
import pandas as pd

st.title("Fehlzeiten-Auswertung mit WebUntis")

# Zeitraum
start_date = datetime(2025, 2, 10)
end_date = datetime(2025, 7, 23)

# Login-Eingabe
school = "Carl-v.-Ossietzky-GYM"
server = "borys.webuntis.com"
username = st.text_input("Benutzername", type="default")
password = st.text_input("Passwort", type="password")

if username and password:
    try:
        with WebUntis(
            school=school,
            user=username,
            password=password,
            server=server,
            useragent="FehlzeitenTool/1.0"
        ) as session:

            # Klassen abrufen
            classes = session.klassen()
            class_options = {f"{c.name} ({c.id})": c.id for c in classes}
            class_name = st.selectbox("Klasse auswählen", list(class_options.keys()))
            class_id = class_options[class_name]

            students = session.get_students(class_id=class_id)
            data = []

            st.info("Daten werden geladen – bitte kurz warten...")

            for student in students:
                absences = session.get_absences(
                    student.id,
                    start=start_date,
                    end=end_date
                )

                counted_hours = 0
                unexcused_hours = 0
                counted_days = set()
                unexcused_days = set()
                tardies = 0

                for a in absences:
                    if a.excuse_status == "unentschuldigt":
                        unexcused_hours += a.lesson_count
                        unexcused_days.add(a.date)
                    else:
                        counted_hours += a.lesson_count
                        counted_days.add(a.date)

                events = session.get_student_events(student.id, start=start_date, end=end_date)
                for event in events:
                    if "verspät" in event.text.lower():
                        tardies += 1

                added_unexcused_days = 0
                if tardies >= 8:
                    added_unexcused_days = 1 + (tardies - 8) // 6

                total_unexcused_days = len(unexcused_days) + added_unexcused_days
                total_days = len(counted_days.union(unexcused_days)) + added_unexcused_days

                data.append({
                    "Name": f"{student.surname}, {student.forename}",
                    "Ges. Fehlstunden": counted_hours + unexcused_hours,
                    "Unentsch. Fehlstunden": unexcused_hours,
                    "Ges. Fehltage": total_days,
                    "Unentsch. Fehltage": total_unexcused_days,
                    "Verspätungen": tardies
                })

            df = pd.DataFrame(data).sort_values(by="Name")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "CSV herunterladen",
                csv,
                f"fehlzeiten_{class_name.replace(' ', '_')}.csv",
                "text/csv",
                key="download-csv"
            )

    except Exception as e:
        st.error(f"Fehler beim Login oder beim Abrufen der Daten: {e}")
