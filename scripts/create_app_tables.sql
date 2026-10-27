CREATE TABLE IF NOT EXISTS workspace.tech_careers.student_demo_profiles (
  name STRING NOT NULL,
  interests ARRAY<STRING>,
  subjects ARRAY<STRING>,
  career STRING,
  majors ARRAY<STRING>,
  updated_at TIMESTAMP
) USING DELTA;
