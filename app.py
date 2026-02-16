import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Project imports
from database import db
from auth.routes import auth as user_auth_blueprint
from auth.agent_routes import agent_auth
# Optional payment modules
try:
    from payments import mpesa_ke
except Exception:
    mpesa_ke = None

try:
    from payments.stripe import create_checkout_session
except Exception:
    create_checkout_session = None
from utils.sms_sender import send_sms
from models.delivery import get_delivery_by_id
from routes.ads import ads as ads_blueprint

app = Flask(__name__)
CORS(app)

app.secret_key = "super_secret_key_bikow_trade"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bikow.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from flask import session, redirect, url_for, flash

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access required.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

db.init_app(app)  # Move this here after config


# Register auth blueprints
app.register_blueprint(user_auth_blueprint, url_prefix="/user")
app.register_blueprint(agent_auth)

ADMIN_USERNAME = "bikow-nation"
ADMIN_PASSWORD = "brianossei22"

DB_PATH = 'database/bikow.db'
# -------------------- Database Init --------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, price TEXT, description TEXT, category TEXT,
        phone TEXT, image TEXT, timestamp TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS deliveries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, from_location TEXT, to_location TEXT,
        phone TEXT, agent_id INTEGER, proof_file TEXT,
        status TEXT DEFAULT 'Pending', rating INTEGER, timestamp TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS agents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT, phone TEXT, vehicle TEXT,
        is_verified INTEGER DEFAULT 0,
        latitude TEXT, longitude TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT,
        provider TEXT,
        product_id INTEGER,
        timestamp TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

@app.context_processor
def inject_now():
    return {'current_year': datetime.now().year}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -------------------- Routes (unchanged, preserved) --------------------
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/pages/<page>')
def serve_page(page):
    allowed_pages = [
        "shop", "post_item", "delivery", "post_delivery",
        "login", "register", "login_agent", "register_agent", "verify_otp",
        "admin", "admin_login", "approve_agents",
        "checkout", "rate_delivery"
    ]
    if page not in allowed_pages:
        return "❌ Page not found", 404
    return render_template(f"pages/{page}.html")

@app.route('/shop')
def shop():
    if not session.get("user"):
        return redirect(url_for("login"))
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM products ORDER BY id DESC")
    products = c.fetchall()
    conn.close()
    return render_template("pages/shop.html", products=products)

@app.route('/post_item', methods=['GET', 'POST'])
def post_item():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form['description']
        category = request.form['category']
        phone = request.form['phone']
        image_file = request.files['image']

        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(filepath)

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO products (name, price, description, category, phone, image, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (name, price, description, category, phone, filename, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            conn.commit()
            conn.close()
            return redirect(url_for('shop'))

    return render_template("pages/post_item.html")

@app.route('/delivery')
def delivery():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM deliveries ORDER BY id DESC")
    deliveries = c.fetchall()
    conn.close()
    return render_template("pages/delivery.html", deliveries=deliveries)

@app.route('/post_delivery', methods=['GET', 'POST'])
def post_delivery():
    if request.method == 'POST':
        name = request.form['name']
        from_location = request.form['from_location']
        to_location = request.form['to_location']
        phone = request.form['phone']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM agents WHERE is_verified=1 AND vehicle LIKE ?", (f"%{to_location}%",))
        agent = c.fetchone()
        agent_id = agent[0] if agent else None

        c.execute("""INSERT INTO deliveries (name, from_location, to_location, phone, agent_id, timestamp)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (name, from_location, to_location, phone, agent_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        return redirect(url_for('delivery'))
    return render_template("pages/post_delivery.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        if user == ADMIN_USERNAME and pw == ADMIN_PASSWORD:
            session['admin'] = True
            session["username"] = user.username
            session["role"] = user.role  # 'admin' or 'user'
            return redirect(url_for('admin'))
        return "Invalid login"
    return render_template("pages/login.html")

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM agents WHERE is_verified=1")
    verified_agents = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM products")
    total_products = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM deliveries")
    total_deliveries = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM transactions")
    total_transactions = c.fetchone()[0]
    c.execute("SELECT * FROM transactions ORDER BY id DESC LIMIT 5")
    transactions = c.fetchall()
    conn.close()

    return render_template("pages/admin.html", verified_agents=verified_agents,
                           total_products=total_products,
                           total_deliveries=total_deliveries,
                           total_transactions=total_transactions,
                           transactions=transactions)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        pw = request.form['password']
        if username == ADMIN_USERNAME and pw == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin'))  # ✅ FIXED
        return "Invalid admin login"
    return render_template("pages/admin_login.html")

@app.route("/admin/manual_payments")
def view_manual_payments():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM manual_payments ORDER BY id DESC")
    payments = c.fetchall()
    conn.close()
    return render_template("pages/manual_payments.html", payments=payments)

@app.route("/admin/transactions")
def admin_transactions():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM transactions ORDER BY id DESC")
    transactions = c.fetchall()
    conn.close()
    return render_template("pages/transactions.html", transactions=transactions)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/checkout/<int:product_id>')
def checkout(product_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT id, name, price, user_id FROM products WHERE id=?", (product_id,))
    row = c.fetchone()

    if not row:
        return "Product not found", 404

    product = {
        "id": row[0],
        "name": row[1],
        "price": row[2],
        "owner_id": row[3]
    }

    # Get seller's payment info
    c.execute("SELECT provider, paybill_number FROM users WHERE id=?", (product['owner_id'],))
    seller = c.fetchone()
    conn.close()

    if not seller:
        return "Seller not found", 404

    product['provider'] = seller[0]
    product['paybill'] = seller[1]

    return render_template("pages/checkout.html", product=product)

@app.route('/pay/stripe/<int:product_id>')
def pay_stripe(product_id):
    return redirect(url_for('pay', product_id=product_id))

@app.route('/pay', methods=['POST'])
def pay():
    # Temporarily disable actual payment
    from flask import flash, redirect
    flash("⚠️ Online payments are currently disabled. Please contact admin to complete your order.", "info")
    return redirect('/shop')

@app.route("/mpesa_pay", methods=["POST"])
def mpesa_pay():
    data = request.get_json()
    phone = data.get("phone")
    amount = int(data.get("amount", 10))
    if not phone:
        return jsonify({"error": "Phone number is required"}), 400
    response = mpesa_ke.lipa_na_mpesa(phone, amount)
    return jsonify(response)

@app.route('/pay/manual', methods=['POST'])
def pay_manual():
    name = request.form['sender_name']
    reference = request.form['reference']
    product_id = request.form['product_id']

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS manual_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        reference TEXT,
        product_id INTEGER,
        status TEXT DEFAULT 'Pending',
        timestamp TEXT
    )""")
    c.execute("INSERT INTO manual_payments (name, reference, product_id, timestamp) VALUES (?, ?, ?, ?)",
              (name, reference, product_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    # Get seller info
    c.execute("SELECT phone FROM products WHERE id = ?", (product_id,))
    seller_row = c.fetchone()
    seller_phone = seller_row[0] if seller_row else None

    conn.commit()
    conn.close()

    # 📲 Send SMS to seller
    if seller_phone:
        message = f"📢 New Payment Alert\nFrom: {name}\nRef: {reference}\nProduct ID: {product_id}"
        send_sms(seller_phone, message)

    return "✅ Payment recorded and seller notified via SMS!"

@app.route('/agent/update_location', methods=['POST'])
def update_agent_location():
    if not session.get("agent_id"):
        return "Agent not authenticated", 403
    data = request.get_json()
    lat = data.get("latitude")
    lon = data.get("longitude")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE agents SET latitude=?, longitude=? WHERE id=?", (lat, lon, session['agent_id']))
    conn.commit()
    conn.close()

    # 🔴 Real-time emit to listeners
    socketio.emit("location_update", {
        "agent_id": session['agent_id'],
        "latitude": lat,
        "longitude": lon
    })

    return "Location updated"

@app.route("/get_agent_location/<int:agent_id>")
def get_agent_location(agent_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, latitude, longitude FROM agents WHERE id=?", (agent_id,))
    agent = c.fetchone()
    conn.close()
    if agent:
        return jsonify({"name": agent[0], "lat": agent[1], "lng": agent[2]})
    return jsonify({})

@app.route('/pages/track_all_agents')
def track_all_agents_page():
    return render_template("pages/track_all_agents.html")

@app.route("/api/agents/locations")
def api_all_agent_locations():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, phone, latitude, longitude FROM agents WHERE is_verified=1")
    agents = [{"id": row[0], "name": row[1], "phone": row[2], "lat": float(row[3]), "lng": float(row[4])}
              for row in c.fetchall() if row[3] and row[4]]
    conn.close()
    return jsonify(agents)

@app.route("/assign_delivery", methods=["POST"])
def assign_delivery():
    data = request.get_json()
    name = data.get("name")
    from_location = data.get("from_location")
    to_location = data.get("to_location")
    phone = data.get("phone")
    agent_id = data.get("agent_id")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO deliveries (name, from_location, to_location, phone, agent_id, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
              (name, from_location, to_location, phone, agent_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    c.execute("UPDATE agents SET status='busy' WHERE id=?", (agent_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "msg": "Delivery assigned"})

@app.route('/admin_map')
def admin_map():
    if not session.get("admin"):
        return redirect(url_for("admin_login"))
    return render_template("pages/admin_map.html")

@app.route("/rate_delivery")
def rate_delivery():
    delivery_id = request.args.get('id')

    if not delivery_id:
        return "No delivery ID provided", 400

    delivery = get_delivery_by_id(delivery_id)

    if not delivery:
        return "Delivery not found", 404

    return render_template("pages/rate_delivery.html", delivery=delivery)

@app.route("/verified_agents")
def verified_agents():
    agents = User.query.filter_by(role="agent", verified=True).all()
    return render_template("pages/verified_agents.html", agents=agents)

@app.route("/admin/agents")
def admin_agents():
    agents = User.query.filter_by(role="agent", verified=True).all()  # Only verified agents
    return render_template("pages/admin_agents.html", agents=agents)

@app.route("/ads")
@admin_required
def list_ads():
    ads = Ad.query.all()
    return render_template("ads/list_ads.html", ads=ads)

@app.route("/ads/new", methods=["GET", "POST"])
@admin_required
def add_ad():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        created_by = session.get("username", "admin")
        new_ad = Ad(title=title, description=description, created_by=created_by)
        db.session.add(new_ad)
        db.session.commit()
        flash("Ad added successfully", "success")
        return redirect(url_for("list_ads"))
    return render_template("ads/add_ad.html")

@app.route("/ads/edit/<int:ad_id>", methods=["GET", "POST"])
@admin_required
def edit_ad(ad_id):
    ad = Ad.query.get_or_404(ad_id)
    if request.method == "POST":
        ad.title = request.form.get("title")
        ad.description = request.form.get("description")
        db.session.commit()
        flash("Ad updated successfully", "success")
        return redirect(url_for("list_ads"))
    return render_template("ads/edit_ad.html", ad=ad)

@app.route("/ads/delete/<int:ad_id>")
@admin_required
def delete_ad(ad_id):
    ad = Ad.query.get_or_404(ad_id)
    db.session.delete(ad)
    db.session.commit()
    flash("Ad deleted", "warning")
    return redirect(url_for("list_ads"))

# -------------------- Start --------------------
if __name__ == "__main__":
    app.run()
