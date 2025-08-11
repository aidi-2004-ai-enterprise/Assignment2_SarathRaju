from locust import HttpUser, task, between

class PenguinUser(HttpUser):
    wait_time = between(1, 3)
    host = "https://penguin-api-iuhex5z56a-pd.a.run.app"  # Cloud Run URL

    @task
    def predict(self):
        payload = {
            "bill_length_mm": 40.0,
            "bill_depth_mm": 18.0,
            "flipper_length_mm": 195,
            "body_mass_g": 4000,
            "year": 2008,
            "sex": "male",
            "island": "Biscoe"
        }
        self.client.post("/predict", json=payload)

