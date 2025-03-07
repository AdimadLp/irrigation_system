from google.cloud.firestore_v1.base_query import FieldFilter
from app.database.firebase import db
from datetime import datetime


class Logs:
    @classmethod
    def get_collection(cls):
        collection_name = "logs"
        return db.collection(collection_name)

    @classmethod
    def process_logs(cls, logs):
        collection = cls.get_collection()
        batch = db.batch()
        inserted_count = 0

        for log_entry in logs:
            try:
                #  log_entry is expected to be a dictionary
                doc_ref = collection.document()  # auto-generates a document ID
                log_data = {
                    "logID": doc_ref.id,  # store the auto-generated document ID
                    "timestamp": datetime.strptime(
                        log_entry["asctime"], "%Y-%m-%d %H:%M:%S,%f"
                    ),
                    "scriptname": log_entry["scriptname"],
                    "custom_funcname": log_entry["custom_funcname"],
                    "levelname": log_entry["levelname"],
                    "message": log_entry["message"],
                }
                batch.set(doc_ref, log_data)
                inserted_count += 1

            except (ValueError, KeyError, TypeError) as e:
                print(f"Invalid log entry format: {e}, log entry: {log_entry}")
        try:
            if inserted_count > 0:
                batch.commit()
                return inserted_count
            else:
                return 0
        except Exception as e:
            print(f"Error committing logs batch : {e}")
            return 0
