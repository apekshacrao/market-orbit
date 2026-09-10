import csv


class ValidationService:

    REQUIRED_COLUMNS = {
        "campaign_name",
        "channel",
        "spend",
        "revenue",
    }

    @staticmethod
    def validate_dataset_format(file_path: str):
        errors = []

        try:
            with open(file_path, newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                if reader.fieldnames is None:
                    return {
                        "is_valid": False,
                        "errors": ["CSV file has no header row"],
                    }

                columns = set(reader.fieldnames)

                missing_columns = (
                    ValidationService.REQUIRED_COLUMNS - columns
                )

                for column in sorted(missing_columns):
                    errors.append(
                        f"Missing required column: {column}"
                    )

        except FileNotFoundError:
            return {
                "is_valid": False,
                "errors": ["File not found"],
            }

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
        }