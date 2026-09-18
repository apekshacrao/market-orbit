from pathlib import Path

from app.services.validation_service import ValidationService


def create_csv(tmp_path: Path, content: str):
    file_path = tmp_path / "test.csv"
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


def test_valid_csv(tmp_path):
    file_path = create_csv(
        tmp_path,
        "campaign_name,channel,spend,conversions,revenue\n"
        "Summer Sale,Google Ads,1200,30,4500\n",
    )

    result = ValidationService.validate_dataset_format(file_path)

    assert result["is_valid"] is True
    assert result["errors"] == []


def test_missing_required_column(tmp_path):
    file_path = create_csv(
        tmp_path,
        "campaign_name,channel,spend\n"
        "Summer Sale,Google Ads,1200\n",
    )

    result = ValidationService.validate_dataset_format(file_path)

    assert result["is_valid"] is False
    assert "Missing required column: conversions" in result["errors"]

def test_file_not_found():
    result = ValidationService.validate_dataset_format(
        "does-not-exist.csv"
    )

    assert result["is_valid"] is False
    assert result["errors"] == ["File not found"]

def test_valid_csv_without_revenue(tmp_path):
    file_path = create_csv(
        tmp_path,
        "campaign_name,channel,spend,conversions\n"
        "Lead Campaign,Google Ads,1200,30\n",
    )

    result = ValidationService.validate_dataset_format(file_path)

    assert result["is_valid"] is True