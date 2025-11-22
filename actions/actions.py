import os
import pyodbc
from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import requests

class ActionGetPatientInfo(Action):

    def name(self) -> str:
        return "action_get_patient_info"

    def run(self, dispatcher, tracker, domain):

        # Get slot values
        patient_name = tracker.get_slot("patient_name")
        patient_id = tracker.get_slot("patient_id")
        disease = tracker.get_slot("disease")
        meta = tracker.get_latest_input_metadata()
        user_id = meta.get("user_id") if meta else None

        if not (patient_name or patient_id or disease):
            dispatcher.utter_message(
                text="Please provide a patient name, ID, or disease."
            )
            return []

        try:
            # ---------- SQL EXPRESS CONNECTION ----------
            conn = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};'
                'SERVER=localhost\\SQLEXPRESS;'
                'DATABASE=model;'
                'Trusted_Connection=yes;'
            )
            cursor = conn.cursor()

            # ---------- Build WHERE Clause ----------
            conditions = []
            params = []

            if patient_name:
                conditions.append("patient_name = ?")
                params.append(patient_name)

            if patient_id:
                conditions.append("patient_id = ?")
                params.append(patient_id)

            if disease:
                conditions.append("disease = ?")
                params.append(disease)
            
            if user_id:
                conditions.append("user_id = ?")
                params.append(user_id)
            else:
                conditions.append("user_id = ?")
                params.append('Guest')

                dispatcher.utter_message(
                    text="You must be logged in to access patient information."
                )
                return []
            where_clause = " AND ".join(conditions)

            # ---------- If unique identifier (patient_id) -> fetch ONE ----------
            if patient_id:
                query = f"""
                SELECT patient_name, patient_id, disease, disease_info, createdat
                FROM patient_db
                WHERE {where_clause}
                """
                
                cursor.execute(query, params)
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
                    dispatcher.utter_message(text="No patient matches the information provided.")

            else:
                # ---------- No patient_id -> return ALL matching rows ----------
                query = f"""
                    SELECT patient_name, patient_id, disease, disease_info, createdat
                    FROM patient_db
                    WHERE {where_clause}
                    """

                cursor.execute(query, params)
                results = cursor.fetchall()

                if results:
                    msg = "Patients found:\n\n"
                    for row in results:
                        NAME, PID, DISEASE, INFO, CREATION = row
                        msg += (
                            f"Name: {NAME}\n"
                            f"ID: {PID}\n"
                            f"Disease: {DISEASE}\n"
                            f"Info: {INFO}\n"
                            f"Record Created: {CREATION}\n"
                            "-------------------------\n"
                        )
                    dispatcher.utter_message(text=msg)
                else:
                    dispatcher.utter_message(text="No patient matches the information provided.")

        except Exception as e:
            dispatcher.utter_message(text=f"Database error: {str(e)}")

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
        metadata = tracker.latest_message.get("metadata") or {}
        user_id = metadata.get("user_id")
        if user_id:
            return [SlotSet("user_id", user_id)]
        else:
            return []
