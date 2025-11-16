import pandas as pd
a = pd.read_csv("attendance.csv")
s = pd.read_csv("students.csv")
# ensure column names
if 'student_id' not in s.columns:
    s = s.rename(columns={col: 'student_id' if 'roll' in col.lower() else col for col in s.columns})
out = a.merge(s[['student_id','name']], on='student_id', how='left')
out = out[['student_id','name','present','timestamp']]
out.to_csv("attendance_with_names.csv", index=False)
print("Saved attendance_with_names.csv")
