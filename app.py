from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from datetime import datetime
import mysql.connector
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load private settings from .env
load_dotenv()

app = Flask(__name__)

# Secret key
app.secret_key = os.getenv("SECRET_KEY")

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ==============================
# DATABASE CONNECTION
# ==============================

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )


# ==============================
# CALCULATE PRINTING COST
# ==============================

def calculate_cost(pages, print_type):

    if pages < 0:
        pages = 0

    if print_type == "Color":

        subtotal = pages * 10

        # KSh 10 discount for color orders
        # of 3 pages or more
        discount = 10 if pages >= 3 else 0

    else:

        subtotal = pages * 5
        discount = 0

    total = subtotal - discount

    if total < 0:
        total = 0

    return discount, total


# ==============================
# STUDENT HOME PAGE
# ==============================

@app.route('/')
def home():

    return render_template('index.html')


# ==============================
# STUDENT SUBMISSION
# ==============================

@app.route('/submit', methods=['POST'])
def submit():

    name = request.form['name']
    phone = request.form['phone']

    file = request.files['assignment']

    if file and file.filename:

        filename = secure_filename(file.filename)

        os.makedirs(
            app.config["UPLOAD_FOLDER"],
            exist_ok=True
        )

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        file.save(filepath)

        now = datetime.now()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO orders
            (
                name,
                phone,
                filename,
                date_time,
                status,
                pages,
                print_type,
                discount,
                total_cost,
                payment_status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                name,
                phone,
                filename,
                now,
                "Pending",
                0,
                "B&W",
                0,
                0,
                "Unpaid"
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

    return f"Thank you {name}! Your assignment has been received."


# ==============================
# ADMIN LOGIN
# ==============================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")

        print("ADMIN_USERNAME =", admin_username)
        print("ADMIN_PASSWORD_SET =", bool(admin_password))

        if (
            username == admin_username
            and password == admin_password
        ):

            session['logged_in'] = True

            return redirect(
                url_for('admin')
            )

        return "Invalid Username or Password"

    return render_template('login.html')


# ==============================
# LOGOUT
# ==============================

@app.route('/logout')
def logout():

    session.clear()

    return redirect(
        url_for('login')
    )


# ==============================
# ADMIN DASHBOARD
# ==============================

@app.route('/admin')
def admin():

    if not session.get('logged_in'):

        return redirect(
            url_for('login')
        )

    search = request.args.get(
        'search',
        ''
    ).strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    # SEARCH
    if search:

        search_value = f"%{search}%"

        cursor.execute(
            """
            SELECT
                id,
                name,
                phone,
                filename,
                date_time,
                status,
                pages,
                print_type,
                discount,
                total_cost,
                payment_status
            FROM orders
            WHERE name LIKE %s
               OR phone LIKE %s
               OR filename LIKE %s
            ORDER BY id DESC
            """,
            (
                search_value,
                search_value,
                search_value
            )
        )

    else:

        cursor.execute(
            """
            SELECT
                id,
                name,
                phone,
                filename,
                date_time,
                status,
                pages,
                print_type,
                discount,
                total_cost,
                payment_status
            FROM orders
            ORDER BY id DESC
            """
        )

    orders = cursor.fetchall()


    # TOTAL ORDERS

    cursor.execute(
        "SELECT COUNT(*) FROM orders"
    )

    total_orders = cursor.fetchone()[0]


    # PENDING

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'Pending'
        """
    )

    pending_orders = cursor.fetchone()[0]


    # PRINTING

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'Printing'
        """
    )

    printing_orders = cursor.fetchone()[0]


    # PRINTED

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'Printed'
        """
    )

    printed_orders = cursor.fetchone()[0]


    # COLLECTED

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'Collected'
        """
    )

    collected_orders = cursor.fetchone()[0]


    # PAID

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE payment_status = 'Paid'
        """
    )

    paid_orders = cursor.fetchone()[0]


    # UNPAID

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE payment_status = 'Unpaid'
        """
    )

    unpaid_orders = cursor.fetchone()[0]


    # TOTAL REVENUE

    cursor.execute(
        """
        SELECT COALESCE(
            SUM(total_cost),
            0
        )
        FROM orders
        WHERE payment_status = 'Paid'
        """
    )

    total_revenue = cursor.fetchone()[0]


    # TODAY'S REVENUE

    cursor.execute(
        """
        SELECT COALESCE(
            SUM(total_cost),
            0
        )
        FROM orders
        WHERE payment_status = 'Paid'
        AND DATE(date_time) = CURDATE()
        """
    )

    today_revenue = cursor.fetchone()[0]


    cursor.close()
    conn.close()


    return render_template(
        "admin.html",
        orders=orders,
        total_orders=total_orders,
        pending_orders=pending_orders,
        printing_orders=printing_orders,
        printed_orders=printed_orders,
        collected_orders=collected_orders,
        paid_orders=paid_orders,
        unpaid_orders=unpaid_orders,
        total_revenue=total_revenue,
        today_revenue=today_revenue,
        search=search
    )


# ==============================
# UPDATE PRICING
# ==============================

@app.route(
    '/update_pricing/<int:order_id>',
    methods=['POST']
)
def update_pricing(order_id):

    if not session.get('logged_in'):

        return redirect(
            url_for('login')
        )

    try:

        pages = int(
            request.form['pages']
        )

    except (ValueError, TypeError):

        return "Invalid number of pages", 400


    if pages < 0:

        return "Number of pages cannot be negative", 400


    print_type = request.form['print_type']


    if print_type not in [
        "B&W",
        "Color"
    ]:

        return "Invalid print type", 400


    discount, total_cost = calculate_cost(
        pages,
        print_type
    )


    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE orders
        SET
            pages = %s,
            print_type = %s,
            discount = %s,
            total_cost = %s
        WHERE id = %s
        """,
        (
            pages,
            print_type,
            discount,
            total_cost,
            order_id
        )
    )


    conn.commit()

    cursor.close()
    conn.close()


    return redirect(
        url_for('admin')
    )


# ==============================
# UPDATE PAYMENT
# ==============================

@app.route(
    '/update_payment/<int:order_id>',
    methods=['POST']
)
def update_payment(order_id):

    if not session.get('logged_in'):

        return redirect(
            url_for('login')
        )


    payment_status = request.form[
        'payment_status'
    ]


    if payment_status not in [
        "Paid",
        "Unpaid"
    ]:

        return "Invalid payment status", 400


    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE orders
        SET payment_status = %s
        WHERE id = %s
        """,
        (
            payment_status,
            order_id
        )
    )


    conn.commit()

    cursor.close()
    conn.close()


    return redirect(
        url_for('admin')
    )


# ==============================
# PRINT ORDER
# ==============================

@app.route(
    '/print/<int:order_id>',
    methods=['POST']
)
def print_order(order_id):

    if not session.get('logged_in'):

        return redirect(
            url_for('login')
        )


    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            filename,
            status,
            payment_status,
            total_cost
        FROM orders
        WHERE id = %s
        """,
        (order_id,)
    )


    order = cursor.fetchone()


    if not order:

        cursor.close()
        conn.close()

        return "Order not found", 404


    filename = order[0]
    current_status = order[1]
    payment_status = order[2]
    total_cost = order[3]


    filepath = os.path.abspath(
        os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )
    )


    if not os.path.exists(filepath):

        cursor.close()
        conn.close()

        return "Assignment file not found", 404


    if current_status != "Pending":

        cursor.close()
        conn.close()

        return redirect(
            url_for('admin')
        )


    # If a price exists,
    # payment must be confirmed.

    if (
        total_cost > 0
        and payment_status != "Paid"
    ):

        cursor.close()
        conn.close()

        return (
            "Payment is not confirmed. "
            "Mark the order as Paid before printing."
        )


    try:

        os.startfile(
            filepath,
            "print"
        )


        cursor.execute(
            """
            UPDATE orders
            SET status = %s
            WHERE id = %s
            """,
            (
                "Printed",
                order_id
            )
        )


        conn.commit()


    except Exception as e:

        cursor.close()
        conn.close()

        return (
            f"Printing failed: {e}"
        ), 500


    cursor.close()
    conn.close()


    return redirect(
        url_for('admin')
    )


# ==============================
# UPDATE STATUS
# ==============================

@app.route(
    '/update_status/<int:order_id>',
    methods=['POST']
)
def update_status(order_id):

    if not session.get('logged_in'):

        return redirect(
            url_for('login')
        )


    new_status = request.form[
        'status'
    ]


    allowed_statuses = [
        "Pending",
        "Printing",
        "Printed",
        "Collected"
    ]


    if new_status not in allowed_statuses:

        return "Invalid status", 400


    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE orders
        SET status = %s
        WHERE id = %s
        """,
        (
            new_status,
            order_id
        )
    )


    conn.commit()

    cursor.close()
    conn.close()


    return redirect(
        url_for('admin')
    )


# ==============================
# VIEW FILE
# ==============================

@app.route(
    '/file/<filename>'
)
def view_file(filename):

    if not session.get('logged_in'):

        return redirect(
            url_for('login')
        )


    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=False
    )


# ==============================
# DOWNLOAD FILE
# ==============================

@app.route(
    '/download/<filename>'
)
def download_file(filename):

    if not session.get('logged_in'):

        return redirect(
            url_for('login')
        )


    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        as_attachment=True
    )


# ==============================
# RUN APPLICATION
# ==============================

if __name__ == '__main__':

    app.run(
        debug=True
    )