import psycopg2
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionGetPatientInfo(Action):
    def name(self) -> str:
        return "action_get_patient_info"

    def run(self, dispatcher, tracker, domain):
        patient_name = NULL
        patient_id = NULL
        disease = NULL
        # Example slot value (patient name taken from user)
        if tracker.get_slot("patient_name"):
            patient_name = tracker.get_slot("patient_name")
        elif tracker.get_slot("patient_id"):
            patient_id = tracker.get_slot("patient_id")
        elif tracker.get_slot("disease"):
            disease = tracker.get_slot("disease")
        else: 
            return ("Please provide either the Patient's name, Id or Disease category.")
        
        try:
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                host="localhost",
                database="mydatabase",
                user="myuser",
                password="mypassword"
            )
            cursor = conn.cursor()
            if(patient_id, disease == NULL):
            query = """
                SELECT patient_id, disease, disease_info
                FROM patients
                WHERE patient_name = %s
            """
            elif(patient_name, patient_id == NULL):
            query = """
                SELECT DISTINCT patient_name,
                FROM patients
                WHERE disease = %s
            """
            cursor.execute(query, (disease,))
            elif(patient_name, disease == NULL):
            """
                SELECT patient_name, disease, disease_info
                FROM patients
                WHERE patient_id = %s
            """
            cursor.execute(query, (patient_id,))

            
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
