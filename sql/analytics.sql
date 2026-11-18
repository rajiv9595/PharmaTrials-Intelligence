-- Clinical research portfolio analysis. Run after the ETL pipeline has loaded records.

-- 1. Study counts by recruitment status.
SELECT overall_status, COUNT(*) AS study_count
FROM studies
GROUP BY overall_status
ORDER BY study_count DESC;

-- 2. Distribution of studies by phase (multi-phase studies contribute once per phase).
SELECT phase_value AS phase, COUNT(DISTINCT s.nct_id) AS study_count
FROM studies AS s
CROSS JOIN LATERAL UNNEST(s.phases) AS phase_value
GROUP BY phase_value
ORDER BY study_count DESC;

-- 3. Study volume by therapeutic condition.
SELECT condition, COUNT(DISTINCT nct_id) AS study_count
FROM study_conditions
GROUP BY condition
ORDER BY study_count DESC
LIMIT 20;

-- 4. Sponsors with the most registered studies.
SELECT lead_sponsor_name, lead_sponsor_class, COUNT(*) AS study_count
FROM studies
WHERE lead_sponsor_name IS NOT NULL
GROUP BY lead_sponsor_name, lead_sponsor_class
ORDER BY study_count DESC
LIMIT 20;

-- 5. Study records by country (site count and distinct registered studies).
SELECT country, COUNT(*) AS registered_sites, COUNT(DISTINCT nct_id) AS study_count
FROM study_locations
WHERE country IS NOT NULL
GROUP BY country
ORDER BY study_count DESC
LIMIT 25;

-- 6. Results availability by study type. Registry results availability is not an efficacy assessment.
SELECT study_type, has_results, COUNT(*) AS study_count
FROM studies
GROUP BY study_type, has_results
ORDER BY study_type, has_results DESC;
