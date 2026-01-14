import re
from dateutil import parser

def calculate_experience(resume_text):
    full_time_years = 0
    internship_months = 0

    matches = re.findall(r'(\d+\.?\d*)\s*(years|months)', resume_text.lower())
    for value, unit in matches:
        value = float(value)
        if unit == "years":
            full_time_years += value
        else:
            internship_months += value

    internship_years = (internship_months / 12) * 0.5
    return round(full_time_years + internship_years, 2)