import pandas as pd

def export_excel(results):
    df = pd.DataFrame(results)
    df["rejection_reasons"] = df["rejection_reasons"].apply(lambda x: "\n".join(x))
    path = "resume_results.xlsx"
    df.to_excel(path, index=False)
    return path
