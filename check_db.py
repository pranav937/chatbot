import psycopg2

conn_str = "postgresql://postgres:SdUOwZoXtsnGSgWjxlpzdDaVJDFazBBn@reseau.proxy.rlwy.net:13742/railway"

try:
    conn = psycopg2.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'products_1'")
    rows = cursor.fetchall()
    for r in rows:
        print(r)
    
    # Check what price actually contains
    cursor.execute("SELECT price FROM products_1 LIMIT 10")
    print("Sample prices:", cursor.fetchall())
    
    cursor.close()
    conn.close()
except Exception as e:
    print("Error:", e)
