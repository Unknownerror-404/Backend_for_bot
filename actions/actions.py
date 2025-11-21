import os
import psycopg2
from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher


class ActionGetPatientInfo(Action):

    def name(self) -> str:
        return "action_get_patient_info"

    def run(self, dispatcher, tracker, domain):

        # Get slot values
        patient_name = tracker.get_slot("patient_name")
        patient_id = tracker.get_slot("patient_id")
        disease = tracker.get_slot("disease")

        # At least one must be provided
        if not (patient_name or patient_id or disease):
            dispatcher.utter_message(
                text="Please provide a patient name, ID, or disease."
            )
            return []

        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                port=os.getenv("DB_PORT")
            )
            cursor = conn.cursor()

            conditions = []
            params = []

            if patient_name:
                conditions.append("patient_name = %s")
                params.append(patient_name)

            if patient_id:
                conditions.append("patient_id = %s")
                params.append(patient_id)

            if disease:
                conditions.append("disease = %s")
                params.append(disease)

            where_clause = " AND ".join(conditions)

            query = f"""
                SELECT patient_name, patient_id, disease, disease_info, createdat
                FROM patient_info
                WHERE {where_clause}
                LIMIT 1
            """

            cursor.execute(query, tuple(params))
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
                        f"Created: {CREATION}"
                    )
                )
            else:
                dispatcher.utter_message(
                    text="No patient matches the information provided."
                )

        except Exception as e:
            dispatcher.utter_message(text=f"Database error: {str(e)}")

        finally:
            if conn:
                conn.close()

        return []
