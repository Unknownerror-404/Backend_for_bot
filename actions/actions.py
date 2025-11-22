import os
import pyodbc
from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

class ActionGetPatientInfo(Action):

    def name(self) -> str:
        return "action_get_patient_info"

    def run(self, dispatcher, tracker, domain):

        # Get slot values
        patient_name = tracker.get_slot("patient_name")
        patient_id = tracker.get_slot("patient_id")
        disease = tracker.get_slot("disease")

        # Correct metadata extraction
        meta = tracker.latest_message.get("metadata", {})
        user_id = meta.get("user_id")

        # Require authentication
        if not user_id:
            dispatcher.utter_message("You must be logged in to access patient information.")
            return []

        # Ensure at least one filter is provided
        if not (patient_name or patient_id or disease):
            dispatcher.utter_message("Please provide a patient name, ID, or disease.")
            return []

        try:
            # SQL Server connection
            conn = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};'
                'SERVER=localhost\\SQLEXPRESS;'
                'DATABASE=model;'
                'Trusted_Connection=yes;'
            )
            cursor = conn.cursor()

            # Build dynamic WHERE clause
            conditions = ["user_id = ?"]
            params = [user_id]

            if patient_name:
                conditions.append("patient_name = ?")
                params.append(patient_name)

            if patient_id:
                conditions.append("patient_id = ?")
                params.append(patient_id)

            if disease:
                conditions.append("disease = ?")
                params.append(disease)

            where_clause = " AND ".join(conditions)

            query = f"""
                SELECT patient_name, patient_id, disease, disease_info, createdat
                FROM patient_db
                WHERE {where_clause}
            """

            cursor.execute(query, params)

            # fetchone if ID given; else many
            if patient_id:
                result = cursor.fetchone()
                if result:
                    NAME, PID, DISEASE, INFO, CREATION = result
                    dispatcher.utter_message(
                        text=(
                            f"Patient Found:\n"
                            f"Name: {NAME}\n"
                            f"ID: {PID}\n"
                            f"Disease: {DISEASE}\n"
                            f"Info: {INFO}\n"
                            f"Record Created: {CREATION}"
                        )
                    )
                else:
                    dispatcher.utter_message("No patient matches the information provided.")

            else:
                results = cursor.fetchall()
                if not results:
                    dispatcher.utter_message("No patient matches the information provided.")
                else:
                    msg = "Patients found:\n\n"
                    for NAME, PID, DISEASE, INFO, CREATION in results:
                        msg += (
                            f"Name: {NAME}\n"
                            f"ID: {PID}\n"
                            f"Disease: {DISEASE}\n"
                            f"Info: {INFO}\n"
                            f"Record Created: {CREATION}\n"
                            "-------------------------\n"
                        )
                    dispatcher.utter_message(msg)

        except Exception as e:
            dispatcher.utter_message(f"Database error: {str(e)}")

        finally:
            try:
                conn.close()
            except:
                pass

        return []


class ActionExtractMetaData(Action):
    def name(self) -> str:
        return "action_extract_metadata"
    
    def run(self, dispatcher: CollectingDispatcher, tracker, domain):
        metadata = tracker.latest_message.get("metadata", {})
        user_id = metadata.get("user_id")
        if user_id:
            return [SlotSet("user_id", user_id)]
        return []
