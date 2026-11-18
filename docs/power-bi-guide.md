# Power BI connection guide

1. Run the pipeline and confirm `data/processed/studies.csv` exists.
2. Open Power BI Desktop and select **Get data → Text/CSV**.
3. Load `studies.csv` for the first overview page.
4. For normalized detail pages, use PostgreSQL via **Get data → PostgreSQL database** and connect to `localhost:5432`, database `pharma_trials`.
5. Use `nct_id` as the relationship key between `studies` and child tables `study_conditions`, `study_interventions` and `study_locations`.
6. Set `nct_id` columns to text. Treat date strings as text until you explicitly parse their precision; the registry may provide year-only or year-month values.

## Suggested report pages

- **Research overview:** distinct study count, recruiting count, completed count, results-posted count.
- **Therapeutic areas:** study counts by condition and phase.
- **Sponsors and interventions:** leading sponsors, sponsor class and intervention type.
- **Geography:** distinct studies and registered sites by country.
- **Data quality:** missing titles, missing identifiers, duplicate NCT IDs and enrollment validation issues from `quality_report.json`.

## Suggested DAX measures

```DAX
Total Studies = DISTINCTCOUNT(studies[nct_id])

Recruiting Studies =
CALCULATE(
    [Total Studies],
    studies[overall_status] = "RECRUITING"
)

Completed Studies =
CALCULATE(
    [Total Studies],
    studies[overall_status] = "COMPLETED"
)

Studies With Results =
CALCULATE(
    [Total Studies],
    studies[has_results] = TRUE()
)
```

Do not interpret `has_results` as positive results. It only indicates results availability on the registry.
