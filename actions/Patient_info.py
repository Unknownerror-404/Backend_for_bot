import psycopg2
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionGetPatientInfo(Action):
    def name(self) -> str:
        return "action_get_patient_info"

    def run(self, dispatcher, tracker, domain):

        # Example slot value (patient name taken from user)
        patient_name = tracker.get_slot("patient_name")

        try:
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                host="localhost",
                database="mydatabase",
                user="myuser",
                password="mypassword"
            )
            cursor = conn.cursor()

            # Query your table
            query = """
                SELECT name, age, diagnosis
                FROM patients
                WHERE name = %s
            """
            cursor.execute(query, (patient_name,))
            result = cursor.fetchone()

            if result:
                name, age, diagnosis = result

                # Send info back to user
                dispatcher.utter_message(
                    text=f"Name: {name}\nAge: {age}\nDiagnosis: {diagnosis}"
                )
            else:
                dispatcher.utter_message(
                    text="I couldn't find that patient in the system."
                )

        except Exception as e:
            dispatcher.utter_message(text=f"Database error: {str(e)}")

        finally:
            if conn:
                conn.close()

        return []
