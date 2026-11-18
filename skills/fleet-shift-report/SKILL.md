---
name: fleet-shift-report
description: Writes a shift handover report for a scooter fleet operations team from fleet data or rough shift notes. Use when the user asks for a shift report, shift handover, end-of-shift summary, Schichtübergabe or raport zmiany for the fleet.
---

# Fleet shift handover report

## 1. Get the data
- If fleet tools are connected (fleet_summary, list_vehicles), call them first.
- Otherwise use the CSV file or the notes the user gave you.
- If you have neither, ask for them. Never invent vehicle IDs or numbers.

## 2. Write the report
Fill in `assets/report-template.md`, section by section.

Rules:
- Every number comes from the data. If something is missing, write "no data".
- Safety issues (brakes, handlebar, steering, frame, battery) are P1 and go first,
  each with the vehicle ID and the next action.
- Maximum one page. Bullets, no long paragraphs.
- Write in the language of the request, unless the user asks for another one
  (German for the warehouse team, English for HQ).

## 3. Finish
End with "Handover to next shift": at most 5 concrete tasks,
each with an owner role (street team, mechanic or dispatcher).

## Example
Request: "Shift report for Altstadt"
Good first line: "Altstadt: 3 vehicles, 1 P1 (SC-1009 loose handlebar, pull from street), 1 needs charging (SC-1010, 6%)."