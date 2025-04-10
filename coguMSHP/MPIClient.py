import requests


class MPIClient:
    """
    Client générique réutilisable pour interagir avec le MPI central
    """

    def __init__(self, username, api_key, mpi_base_url):
        self.username = username
        self.api_key = api_key
        self.mpi_base_url = mpi_base_url
        self.token = self.get_token()

    def get_token(self):
        response = requests.post(
            f"{self.mpi_base_url}/platform/token/",
            json={"username": self.username, "api_key": self.api_key},
            timeout=5
        )

        if response.status_code != 200:
            raise Exception(f"Échec authentification MPI: {response.text}")

        return response.json()["access"]

    def synchroniser_patient(self, patient_data):
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

        response = requests.post(
            f"{self.mpi_base_url}/mpi/patients/",
            json=patient_data,
            headers=headers,
            timeout=5
        )

        if response.status_code not in [200, 201]:
            raise Exception(f"Erreur MPI: {response.status_code} - {response.text}")

        return response.json()