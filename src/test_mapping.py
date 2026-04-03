import pandas as pd

lennar_path = 'doc_to_test/lennar check.xlsx'
df = pd.read_excel(lennar_path)
df = df.dropna(subset=['COMMUNITY'])

print("=== VIVANT ===")
print(df[df['COMMUNITY'].astype(str).str.contains('VIVANT', case=False)]['COMMUNITY'].unique())

print("=== REDLAND ===")
print(df[df['COMMUNITY'].astype(str).str.contains('REDLAND', case=False)]['COMMUNITY'].unique())

print("=== ACTIVITIES ===")
print(df['ACTIVITY'].unique())
