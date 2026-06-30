import psycopg2

conn_str = "postgresql://postgres:SdUOwZoXtsnGSgWjxlpzdDaVJDFazBBn@reseau.proxy.rlwy.net:13742/railway"

try:
    print("Connecting...")
    conn = psycopg2.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT product_name FROM products_1 LIMIT 5")
    rows = cursor.fetchall()
    print("Products in DB:", rows)
    cursor.close()
    conn.close()
except Exception as e:
    print("Error:", e)
