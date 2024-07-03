import threading


class ThreadSafeList:
    def __init__(self):
        self.data = []
        self.lock = threading.Lock()

    def append(self, item):
        with self.lock:
            self.data.append(item)

    def overwrite(self, new_data):
        with self.lock:
            self.data = new_data

    def get(self):
        with self.lock:
            return self.data

    def get_by_sensor_id(self, sensor_id):
        with self.lock:
            return [data for data in self.data if data["sensorID"] == sensor_id]

    def __len__(self):
        with self.lock:
            return len(self.data)
