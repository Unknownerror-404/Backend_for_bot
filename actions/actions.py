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
            host=os.getenv("DB_HOST"),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=os.getenv("DB_PORT")
            )
            cursor = conn.cursor()
            if(patient_id and disease == NULL):
            query = """
                SELECT patient_name, patient_id, disease, disease_info
                FROM patient_info 
                WHERE patient_name = %s
            """
            elif(patient_name and patient_id == NULL):
            query = """
                SELECT DISTINCT patient_name,
                FROM patient_info 
                WHERE disease = %s
            """
            cursor.execute(query, (disease,))
            elif(patient_name and disease == NULL):
             query = """
                SELECT patient_name, disease, disease_info
                FROM patient_info 
                WHERE patient_id = %s
            """
            cursor.execute(query, (patient_id,))
            elif(patient_name == NULL):
             query = """
                SELECT patient_name, patient_id, disease, disease_info
                FROM patient_info
                WHERE patient_id, disease = %s, %s
            """
            cursor.execute(query, (patient_id, disease,))
            elif(patient_id == NULL):
             query = """
                SELECT patient_name, patient_id, disease, disease_info
                FROM patient_info
                WHERE patient_name, disease = %s, %s
            """
            cursor.execute(query, (patient_id, disease,))
            elif(disease == NULL):
             query = """
                SELECT patient_name, patient_id, disease, disease_info
                FROM patient_info
                WHERE patient_id, patient_name = %s, %s
            """
            cursor.execute(query, (patient_id, disease,))
            
            result = cursor.fetchone()

            if result:
               NAME, PID, DISEASE, INFO, = result

                # Send info back to user
                dispatcher.utter_message(
                    text=f" User found,\n Name: {NAME}\nPatient ID: {PID}\nDiagnosis: {DISEASE}\n Additional Patient History: {INFO}.\n The User Registration is found from {CREATION}"
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
