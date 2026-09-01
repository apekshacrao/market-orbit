class StorageService:
    @staticmethod
    async def save_upload(file, user):
        # Starter storage logic stub
        return {
            "dataset_id": "dataset-1",
            "filename": file.filename,
            "status": "PENDING",
            "message": "File uploaded successfully"
        }

    @staticmethod
    def get_dataset_status(dataset_id: str):
        return {"dataset_id": dataset_id, "status": "COMPLETED"}
