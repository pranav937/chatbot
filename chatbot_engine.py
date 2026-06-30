import psycopg2
from typing import Tuple, List, Dict, Any

class ChatbotEngine:
    def __init__(self):
        self.conn_str = "postgresql://postgres:SdUOwZoXtsnGSgWjxlpzdDaVJDFazBBn@reseau.proxy.rlwy.net:13742/railway"

    def get_greeting(self) -> str:
        return (
            "Hello! I am your Database-Powered Product Assistant.\n\n"
            "I will guide you step-by-step to find the exact product you need.\n\n"
            "Let's get started!"
        )

    def _execute_query(self, query: str, params: Tuple = None) -> List[Any]:
        try:
            conn = psycopg2.connect(self.conn_str)
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except Exception as e:
            print(f"Database error: {e}")
            return []

    def get_options_for_step(self, step: int, filters: Dict[str, str]) -> List[str]:
        if step == 1:
            query = "SELECT DISTINCT main_category FROM products_1 WHERE main_category IS NOT NULL AND main_category != 'nan' LIMIT 20"
            results = self._execute_query(query)
            return [str(r[0]) for r in results if r[0]]
            
        elif step == 2:
            main_cat = filters.get("main_category")
            query = "SELECT DISTINCT category FROM products_1 WHERE main_category = %s AND category IS NOT NULL AND category != 'nan' LIMIT 20"
            results = self._execute_query(query, (main_cat,))
            return [str(r[0]) for r in results if r[0]]
            
        elif step == 3:
            cat = filters.get("category")
            query = "SELECT DISTINCT subcategory FROM products_1 WHERE category = %s AND subcategory IS NOT NULL AND subcategory != 'nan' LIMIT 20"
            results = self._execute_query(query, (cat,))
            return [str(r[0]) for r in results if r[0]]
            
        elif step == 4:
            subcat = filters.get("subcategory")
            query = "SELECT DISTINCT location FROM products_1 WHERE subcategory = %s AND location IS NOT NULL AND location != 'nan' LIMIT 15"
            results = self._execute_query(query, (subcat,))
            options = [str(r[0]) for r in results if r[0]]
            options.append("Any Location")
            return options
            
        elif step == 5:
            # Calculate average price from the DB for the selected filters
            try:
                conn = psycopg2.connect(self.conn_str)
                cursor = conn.cursor()
                
                base_query = "SELECT AVG(price) FROM products_1 WHERE price IS NOT NULL AND price > 0"
                params = []
                
                if filters.get("main_category"):
                    base_query += " AND main_category = %s"
                    params.append(filters["main_category"])
                if filters.get("category"):
                    base_query += " AND category = %s"
                    params.append(filters["category"])
                if filters.get("subcategory"):
                    base_query += " AND subcategory = %s"
                    params.append(filters["subcategory"])
                if filters.get("location") and filters["location"] != "Any Location":
                    base_query += " AND location = %s"
                    params.append(filters["location"])
                    
                cursor.execute(base_query, tuple(params))
                result = cursor.fetchone()
                
                cursor.close()
                conn.close()
                
                avg_price = result[0] if result and result[0] else None
                
                if avg_price:
                    avg = int(avg_price)
                    # Round to nearest 100 for cleaner UI
                    avg = max(100, round(avg / 100) * 100)
                    return [f"Below ₹{avg:,}", f"₹{avg:,} - ₹{avg*2:,}", f"Above ₹{avg*2:,}", "Any Price"]
                else:
                    return ["Below ₹1,000", "₹1,000 - ₹5,000", "Above ₹5,000", "Any Price"]
            except Exception as e:
                print(f"Error calculating average price: {e}")
                return ["Below ₹1,000", "₹1,000 - ₹5,000", "Above ₹5,000", "Any Price"]
            
        return []

    def search_filtered_products(self, filters: Dict[str, str]) -> str:
        try:
            conn = psycopg2.connect(self.conn_str)
            cursor = conn.cursor()
            
            base_query = "SELECT product_name, company_name, price, location, rating FROM products_1 WHERE 1=1 "
            params = []
            
            if filters.get("main_category"):
                base_query += " AND main_category = %s"
                params.append(filters["main_category"])
            if filters.get("category"):
                base_query += " AND category = %s"
                params.append(filters["category"])
            if filters.get("subcategory"):
                base_query += " AND subcategory = %s"
                params.append(filters["subcategory"])
            if filters.get("location") and filters["location"] != "Any Location":
                base_query += " AND location = %s"
                params.append(filters["location"])
                
            budget = filters.get("budget")
            if budget and budget != "Any Price":
                # Parse dynamic budget strings (e.g., "Below ₹5,000", "₹5,000 - ₹10,000")
                budget_str = budget.replace("₹", "").replace(",", "").strip()
                if budget_str.startswith("Below"):
                    val = int(budget_str.replace("Below", "").strip())
                    base_query += f" AND price < {val}"
                elif budget_str.startswith("Above"):
                    val = int(budget_str.replace("Above", "").strip())
                    base_query += f" AND price > {val}"
                elif "-" in budget_str:
                    parts = budget_str.split("-")
                    val1 = int(parts[0].strip())
                    val2 = int(parts[1].strip())
                    base_query += f" AND price >= {val1} AND price <= {val2}"
                
            base_query += " LIMIT 10"
            
            cursor.execute(base_query, tuple(params))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            if not results:
                return "Sorry, I couldn't find any products matching those filters."
            
            response = f"**Found {len(results)} product(s) for your selection:**\n\n"
            for row in results:
                product_name, company, price, location, rating = row
                
                def is_valid(v):
                    if v is None: return False
                    if isinstance(v, str) and v.lower() == 'nan': return False
                    if isinstance(v, float) and v != v: return False
                    return True
                
                response += f"- **{product_name}**\n"
                if is_valid(company): response += f"  - Company: {company}\n"
                if is_valid(price): response += f"  - Price: ₹{price}\n"
                if is_valid(location): response += f"  - Location: {location}\n"
                if is_valid(rating): response += f"  - Rating: {rating}\n"
                response += "\n"
                
            return response
            
        except Exception as e:
            return f"Error connecting to database or searching: {e}"

    def search_products_by_keyword(self, keyword: str) -> str:
        kw_lower = keyword.lower().strip()
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
        if kw_lower in greetings:
            return "Hello! How can I help you today? You can search for a product or use the buttons above."
            
        # Strip common conversational prefixes to find the actual product keyword
        prefixes = [
            "search for", "find me", "find", "looking for", "show me", 
            "what is the price of", "price of", "i want", "do you have", 
            "where can i get", "i need"
        ]
        
        search_term = kw_lower
        for prefix in prefixes:
            if search_term.startswith(prefix):
                search_term = search_term[len(prefix):].strip()
                break
                
        search_term = search_term.strip("?.! ")
        
        if not search_term:
            return "Could you please specify what product you are looking for?"
            
        try:
            conn = psycopg2.connect(self.conn_str)
            cursor = conn.cursor()
            
            # Simple keyword search on the products_1 table
            query = """
                SELECT product_name, company_name, price, location, rating 
                FROM products_1 
                WHERE product_name ILIKE %s
                LIMIT 5
            """
            cursor.execute(query, (f"%{search_term}%",))
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            if not results:
                return f"Sorry, I couldn't find any products matching '{search_term}' in the database."
            
            response = f"**Found {len(results)} product(s) matching '{search_term}':**\n\n"
            for row in results:
                product_name, company, price, location, rating = row
                
                def is_valid(v):
                    if v is None: return False
                    if isinstance(v, str) and v.lower() == 'nan': return False
                    if isinstance(v, float) and v != v: return False
                    return True
                
                response += f"- **{product_name}**\n"
                if is_valid(company): response += f"  - Company: {company}\n"
                if is_valid(price): response += f"  - Price: ₹{price}\n"
                if is_valid(location): response += f"  - Location: {location}\n"
                if is_valid(rating): response += f"  - Rating: {rating}\n"
                response += "\n"
                
            return response
            
        except Exception as e:
            return f"Error connecting to database or searching: {e}"
