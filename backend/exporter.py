import pandas as pd


def export_excel(results: list[dict]) -> str:
    df = pd.DataFrame(results)

    if "rejection_reasons" in df.columns:
        def normalize_reasons(x):
            if isinstance(x, list):
                return "\n".join(x)
            if isinstance(x, str):
                return x
            return ""

        df["rejection_reasons"] = df["rejection_reasons"].apply(normalize_reasons)

    file_path = "resume_screening_results.xlsx"
    df.to_excel(file_path, index=False)

    return file_path
