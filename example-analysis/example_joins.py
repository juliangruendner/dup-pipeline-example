"""Load the DUP pipeline CSV exports into an in-memory SQLite database and run example joins.

The join results are printed and written as CSV files to joins_output/.

Usage: python3 example_joins.py [csv_dir]
"""

import csv
import sqlite3
import sys
from pathlib import Path

DEFAULT_CSV_DIR = Path(__file__).parent / "20260925_1235_88129f43-b72a-4565-af8a-7cc48a3363be" / "csv"
OUTPUT_DIR = Path(__file__).parent / "joins_output"

# CSV file name -> SQL table name
TABLES = {
    "Patients.csv": "patient",
    "MII PR Fall Kontakt mit einer Gesundheitseinrichtung.csv": "encounter",
    "Diagnosis-all-fields.csv": "condition",
    "Laboratory test.csv": "lab",
    "MII PR Prozedur Procedure.csv": "procedure",
    "Medication administration.csv": "med_admin",
    "Medication statement.csv": "med_statement",
    "MII PR Medikation Medication.csv": "medication",
    "Medication Ingredient.csv": "med_ingredient",
}


def load_csvs(csv_dir: Path) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    for file_name, table in TABLES.items():
        with open(csv_dir / file_name, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            cols = ", ".join(f'"{c}"' for c in header)
            con.execute(f"CREATE TABLE {table} ({cols})")
            placeholders = ", ".join("?" for _ in header)
            # Empty CSV cells become NULL so that joins and IS NULL checks behave as expected
            rows = [[v if v != "" else None for v in row] for row in reader]
            con.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)
        print(f"loaded {table:<15} {len(rows):>4} rows  ({file_name})")
    return con


def show(con: sqlite3.Connection, title: str, sql: str, out_file: Path) -> None:
    cur = con.execute(sql)
    header = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(f"\n== {title} ({len(rows)} rows) -> {out_file}")
    widths = [max(len(str(x)) for x in [h, *(r[i] for r in rows)]) for i, h in enumerate(header)]
    print("  ".join(h.ljust(w) for h, w in zip(header, widths)))
    for r in rows:
        print("  ".join(str(v).ljust(w) for v, w in zip(r, widths)))

    # NULL is written as an empty cell, as in the input CSVs
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


# References in the CSVs have the form "<ResourceType>/<id>", while the id columns hold the bare id.

# Strength is a ratio (numerator / denominator). Value and unit stay in separate columns so that values
# can be compared and converted. The unit is taken from *_code, not from *_unit, which is free display
# text ("mg" vs "milligram"). *_system tells which code system the code belongs to: UCUM for units,
# EDQM for dose forms such as tablets (denominator code 10219000 = Tablet).

# 1. Medication administration -> Medication -> Medication Ingredient.
# A Medication either holds its ingredient inline (Medication_ingredient_* columns) or references
# another Medication as ingredient (ingredient.itemReference). LEFT JOINs keep all administrations
# and medications. The ingredient columns come from the referenced Medication Ingredient if there
# is one, otherwise from the medication's inline ingredient.
MED_ADMIN_MED_INGREDIENT = """
SELECT ma.id                                                   AS med_admin_id,
       ma.patient,
       ma.MedicationAdministration_effective_X_Effectivedatetime AS administered_at,
       m.id                                                    AS medication_id,
       m.Medication_code_codingAtcclassde_code                 AS atc,
       CASE WHEN mi.id IS NOT NULL THEN 'referenced' ELSE 'inline' END AS ingredient_source,
       mi.id                                                   AS ingredient_medication_id,
       CASE WHEN mi.id IS NOT NULL
            THEN mi.Medication_ingredient_item_X_Itemcodeableconcept_codingAsk_code
            ELSE m.Medication_ingredient_item_X_Itemcodeableconcept_codingAsk_code END AS ingredient_ask,
       CASE WHEN mi.id IS NOT NULL THEN mi.Medication_ingredient_strength_numerator_value ELSE m.Medication_ingredient_strength_numerator_value END AS strength_numerator_value,
       CASE WHEN mi.id IS NOT NULL THEN mi.Medication_ingredient_strength_numerator_code ELSE m.Medication_ingredient_strength_numerator_code END AS strength_numerator_code,
       CASE WHEN mi.id IS NOT NULL THEN mi.Medication_ingredient_strength_numerator_system ELSE m.Medication_ingredient_strength_numerator_system END AS strength_numerator_system,
       CASE WHEN mi.id IS NOT NULL THEN mi.Medication_ingredient_strength_denominator_value ELSE m.Medication_ingredient_strength_denominator_value END AS strength_denominator_value,
       CASE WHEN mi.id IS NOT NULL THEN mi.Medication_ingredient_strength_denominator_code ELSE m.Medication_ingredient_strength_denominator_code END AS strength_denominator_code,
       CASE WHEN mi.id IS NOT NULL THEN mi.Medication_ingredient_strength_denominator_system ELSE m.Medication_ingredient_strength_denominator_system END AS strength_denominator_system
FROM med_admin ma
LEFT JOIN medication m
       ON ma.MedicationAdministration_medication_X_Medicationreference_reference = 'Medication/' || m.id
LEFT JOIN med_ingredient mi
       ON m.Medication_ingredient_item_X_Itemreference_reference = 'Medication/' || mi.id
ORDER BY ma.patient, administered_at
"""

# 1b. Medication statement -> Medication -> Medication Ingredient. Same pattern as 1.
# The compound Medication 85f96e98... is only referenced by a statement, so this join shows the
# 'referenced' case: one inline ingredient row plus the rows of the referenced glucose solution.
MED_STATEMENT_MED_INGREDIENT = """
SELECT ms.id                                                   AS med_statement_id,
       ms.patient,
       ms.MedicationStatement_status                           AS status,
       COALESCE(ms.MedicationStatement_effective_X_Effectivedatetime,
                ms.MedicationStatement_effective_X_Effectiveperiod_start) AS effective_start,
       ms.MedicationStatement_effective_X_Effectiveperiod_end  AS effective_end,
       m.id                                                    AS medication_id,
       m.Medication_code_codingAtcclassde_code                 AS atc,
       CASE WHEN mi.id IS NOT NULL THEN 'referenced' ELSE 'inline' END AS ingredient_source,
       mi.id                                                   AS ingredient_medication_id,
       CASE WHEN mi.id IS NOT NULL
            THEN mi.Medication_ingredient_item_X_Itemcodeableconcept_codingAsk_code
            ELSE m.Medication_ingredient_item_X_Itemcodeableconcept_codingAsk_code END AS ingredient_ask,
       CASE WHEN mi.id IS NOT NULL
            THEN mi.Medication_ingredient_isActive
            ELSE m.Medication_ingredient_isActive END          AS ingredient_active,
       CASE WHEN mi.id IS NOT NULL THEN mi.Medication_ingredient_strength_numerator_value ELSE m.Medication_ingredient_strength_numerator_value END AS strength_numerator_value,
       CASE WHEN mi.id IS NOT NULL THEN mi.Medication_ingredient_strength_numerator_code ELSE m.Medication_ingredient_strength_numerator_code END AS strength_numerator_code,
       CASE WHEN mi.id IS NOT NULL THEN mi.Medication_ingredient_strength_numerator_system ELSE m.Medication_ingredient_strength_numerator_system END AS strength_numerator_system,
       CASE WHEN mi.id IS NOT NULL THEN mi.Medication_ingredient_strength_denominator_value ELSE m.Medication_ingredient_strength_denominator_value END AS strength_denominator_value,
       CASE WHEN mi.id IS NOT NULL THEN mi.Medication_ingredient_strength_denominator_code ELSE m.Medication_ingredient_strength_denominator_code END AS strength_denominator_code,
       CASE WHEN mi.id IS NOT NULL THEN mi.Medication_ingredient_strength_denominator_system ELSE m.Medication_ingredient_strength_denominator_system END AS strength_denominator_system
FROM med_statement ms
LEFT JOIN medication m
       ON ms.MedicationStatement_medication_X_Medicationreference_reference = 'Medication/' || m.id
LEFT JOIN med_ingredient mi
       ON m.Medication_ingredient_item_X_Itemreference_reference = 'Medication/' || mi.id
ORDER BY ms.patient, effective_start
"""

# 2. Medication -> Medication Ingredient only, to show the ingredient link independent of administrations.
MED_INGREDIENT = """
SELECT m.id                                                   AS medication_id,
       m.Medication_ingredient_item_X_Itemreference_reference AS ingredient_ref,
       mi.Medication_code_codingAtcclassde_code               AS ingredient_atc,
       mi.Medication_ingredient_item_X_Itemcodeableconcept_codingSnomed_code AS ingredient_snomed,
       mi.Medication_ingredient_isActive                      AS ingredient_active,
       mi.Medication_ingredient_strength_numerator_value      AS strength_numerator_value,
       mi.Medication_ingredient_strength_numerator_code       AS strength_numerator_code,
       mi.Medication_ingredient_strength_numerator_system     AS strength_numerator_system,
       mi.Medication_ingredient_strength_denominator_value    AS strength_denominator_value,
       mi.Medication_ingredient_strength_denominator_code     AS strength_denominator_code,
       mi.Medication_ingredient_strength_denominator_system   AS strength_denominator_system
FROM medication m
JOIN med_ingredient mi
  ON m.Medication_ingredient_item_X_Itemreference_reference = 'Medication/' || mi.id
"""

# 3. Patient -> number of administrations and distinct ATC codes.
PATIENT_MED_SUMMARY = """
SELECT p.id                     AS patient_id,
       p.Patient_gender         AS gender,
       p.Patient_birthDate      AS birth_date,
       COUNT(DISTINCT ma.id)    AS n_administrations,
       GROUP_CONCAT(DISTINCT m.Medication_code_codingAtcclassde_code) AS atc_codes
FROM patient p
JOIN med_admin ma ON ma.patient = 'Patient/' || p.id
LEFT JOIN medication m
       ON ma.MedicationAdministration_medication_X_Medicationreference_reference = 'Medication/' || m.id
GROUP BY p.id
ORDER BY n_administrations DESC
"""

# 4. Lab test -> Encounter: lab values with the encounter period they belong to.
LAB_ENCOUNTER = """
SELECT DISTINCT
       l.id                                    AS lab_id,
       l.patient,
       l.Observation_code_coding_code          AS loinc,
       l.Observation_value_X_Valuequantity_value AS value,
       l.Observation_value_X_Valuequantity_code  AS unit,
       l.Observation_effective_X_Effectivedatetime AS measured_at,
       e.id                                    AS encounter_id,
       e.Encounter_period_start                AS enc_start,
       e.Encounter_period_end                  AS enc_end
FROM lab l
JOIN encounter e ON l.Observation_encounter_reference = 'Encounter/' || e.id
ORDER BY l.patient, measured_at
"""


def main() -> None:
    csv_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV_DIR
    con = load_csvs(csv_dir)
    OUTPUT_DIR.mkdir(exist_ok=True)
    show(con, "Medication administration -> Medication -> Medication Ingredient", MED_ADMIN_MED_INGREDIENT,
         OUTPUT_DIR / "med_admin_medication_ingredient.csv")
    show(con, "Medication statement -> Medication -> Medication Ingredient", MED_STATEMENT_MED_INGREDIENT,
         OUTPUT_DIR / "med_statement_medication_ingredient.csv")
    show(con, "Medication -> Medication Ingredient", MED_INGREDIENT,
         OUTPUT_DIR / "medication_ingredient.csv")
    show(con, "Patient -> Medication administration -> Medication (summary)", PATIENT_MED_SUMMARY,
         OUTPUT_DIR / "patient_medication_summary.csv")
    show(con, "Laboratory test -> Encounter", LAB_ENCOUNTER,
         OUTPUT_DIR / "lab_encounter.csv")


if __name__ == "__main__":
    main()
