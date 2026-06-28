-- Raw seed data. The `method` column carries the ReportBuilder method NAME as a
-- string. This SQL row is the only reference to churnReport outside its
-- definition -> DB-stored dispatch via a .sql row.
INSERT INTO reports (name, method) VALUES
  ('Monthly revenue', 'monthlyRevenue'),
  ('Customer churn',  'churnReport');
