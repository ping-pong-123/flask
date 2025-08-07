# app/routes.py
# app/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Scan
from app import db, login_manager, socketio # <-- Add 'socketio' here
from .scan import start_scan_async
from flask import jsonify
import requests
import time
import uuid
"""from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Scan
from app import db, login_manager
from .scan import start_scan_async
from flask import jsonify
import requests
from app import db
import time
import uuid
from . import db"""

bp = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@bp.route("/startscan", methods=["GET", "POST"])
@login_required
def start_scan():
    if request.method == "POST":
        if not current_user.is_authenticated:
            return redirect(url_for("main.login"))
        scan_name = request.form["scan_name"]
        target_url = request.form["target_url"]
        auth_type = request.form.get("auth_type")
        username = request.form.get("username")
        password = request.form.get("password")
        access_token = request.form.get("access_token")
        cookies = request.form.get("cookies")
        scan_type = request.form["scan_type"]
        environment = request.form["environment"]

        #new_scan = Scan(scan_name=scan_name, target_url=target_url, scan_type=scan_type, environment=environment, user_id=current_user.id)
        # 🔹 FIX: Pass all form data to the new Scan object
        new_scan = Scan(
            scan_name=scan_name, 
            target_url=target_url, 
            scan_type=scan_type, 
            environment=environment, 
            auth_type=auth_type,
            username=username,
            password=password,
            token=access_token, # Note: using `token` field for access_token
            cookies=cookies,
            user_id=current_user.id
        )
        db.session.add(new_scan)
        db.session.commit()
        #print("debug_3")
        start_scan_async(new_scan.id)

        return redirect(url_for("main.scan", scan_id=new_scan.id))

    # 🔹 Added logic to show all scans to admins, but only their own to regular users
    if current_user.is_admin:
        scans = Scan.query.order_by(Scan.created_at.desc()).all()
    else:
        scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).all()

    return render_template("startscan.html", scans=scans)

    #scans = Scan.query.filter_by(user_id=current_user.id).all() if current_user.is_authenticated else []
    #return render_template("startscan.html", scans=scans)




@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid username or password.", "error")
    return render_template("login.html")



@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))


"""@bp.route("/scan/<int:scan_id>")
@login_required
def scan(scan_id):
    scan = Scan.query.get_or_404(scan_id)
    if scan.user_id != current_user.id:
        return redirect(url_for("main.start_scan"))
    scans = Scan.query.filter_by(user_id=current_user.id).all()
    return render_template("scan.html", scan=scan, scans=scans)"""

@bp.route("/scan/<int:scan_id>")
@login_required
def scan(scan_id):
    scan = Scan.query.get_or_404(scan_id)
    # 🔹 Authorization check: Allow admin to view any scan
    if scan.user_id != current_user.id and not current_user.is_admin:
        flash("You do not have permission to view this scan.", "danger")
        return redirect(url_for("main.history"))
    
    # 🔹 Added logic to fetch all scans for admin and own scans for users
    if current_user.is_admin:
        scans = Scan.query.order_by(Scan.created_at.desc()).all()
    else:
        scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).all()
    
    return render_template("scan.html", scan=scan, scans=scans)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if email or username already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already registered.', 'error')
            return render_template('register.html')

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_pw, is_admin=False)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('main.login'))
        
    return render_template('register.html')





"""@bp.route("/history")
@login_required
def history():
    scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).all()
    return render_template("history.html", scans=scans)"""

@bp.route("/history")
@login_required
def history():
    # 🔹 New logic: Admins see all scans, regular users see their own
    if current_user.is_admin:
        #scans = Scan.query.order_by(Scan.created_at.desc()).all()
        scans = Scan.query.join(User).order_by(Scan.created_at.desc()).all()
    else:
        scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).all()

    return render_template("history.html", scans=scans)



"""@bp.route("/delete_scan/<int:scan_id>", methods=["POST"])
@login_required
def delete_scan(scan_id):
    scan = Scan.query.get_or_404(scan_id)
    if scan.user_id != current_user.id:
        return redirect(url_for("main.history"))

    db.session.delete(scan)
    db.session.commit()
    return redirect(url_for("main.history"))"""

@bp.route("/delete_scan/<int:scan_id>", methods=["POST"])
@login_required
def delete_scan(scan_id):
    scan = Scan.query.get_or_404(scan_id)
    # 🔹 Authorization check: Allow admin to delete any scan
    if scan.user_id != current_user.id and not current_user.is_admin:
        flash("You do not have permission to delete this scan.", "danger")
        return redirect(url_for("main.history"))

    db.session.delete(scan)
    db.session.commit()
    return redirect(url_for("main.history"))


@bp.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for("main.start_scan"))

    users = User.query.filter(User.username != "admin").all()

    # Group scans by username
    user_scans = {}
    for user in users:
        scans = Scan.query.filter_by(user_id=user.id).all()
        user_scans[user.username] = scans

    return render_template("admin_dashboard.html", users=users, user_scans=user_scans)
    





@bp.route("/delete_user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for("main.start_scan"))

    user = User.query.get_or_404(user_id)
    if user.username == "admin":
        return redirect(url_for("main.admin_dashboard"))  # prevent admin deletion

    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("main.admin_dashboard"))


@bp.route("/api/start_scan", methods=["POST"])
@login_required
def api_start_scan():
    data = request.get_json()

    try:
        environment = data.get("environment", "dev")
        scan = Scan(
            user_id=current_user.id,
            scan_name=data["scan_name"],
            target_url=data["target_url"],
            scan_type=data["scan_type"],
            status="In Progress",
            cookies=data.get("cookies", ""),
            auth_type=data.get("auth_type", "none"),
            username=data.get("username", ""),
            password=data.get("password", "")
        )
        db.session.add(scan)
        db.session.commit()
        #print("debug_2")
        start_scan_async(scan.id)  # Begin scanning in background thread

        return jsonify({"success": True, "scan_id": scan.id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/validate_target")
@login_required
def validate_target():
    import requests

    url = request.args.get("url")
    reachable = False

    try:
        # Try GET with redirect following
        response = requests.get(url, timeout=5, stream=True, allow_redirects=True)
        reachable = response.status_code < 400
    except requests.exceptions.RequestException as e_get:
        print(f"[GET] Validation failed for {url}: {e_get}")

        # Try POST as fallback
        try:
            response = requests.post(url, timeout=5, stream=True, allow_redirects=True)
            reachable = response.status_code < 400
        except requests.exceptions.RequestException as e_post:
            print(f"[POST fallback] Validation also failed for {url}: {e_post}")
            reachable = False

    return jsonify({"reachable": reachable})


@bp.route("/", methods=["GET"])
def home():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("home.html")  # Shows "Please log in to continue"

# Dashboard Route
"""@bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    total_scans = Scan.query.count()
    critical_vulns = Scan.query.filter(Scan.result.ilike('%critical%')).count()
    total_assets = db.session.query(Scan.target_url).distinct().count()

    recent_scan = Scan.query.order_by(Scan.created_at.desc()).first()
    recent_status = recent_scan.status if recent_scan else "N/A"

    chart_data = {
        "labels": ["Critical", "High", "Medium", "Low", "Info"],
        "counts": [5, 12, 8, 3, 1]
    }

    owasp_data = {
        "labels": [
            "Injection", "Broken Auth", "Sensitive Data", "XML External Entities",
            "Broken Access Control", "Security Misconfig", "XSS", "Insecure Deserialization",
            "Using Components w/ Known Vulns", "Insufficient Logging"
        ],
        "counts": [15, 8, 5, 2, 10, 6, 12, 3, 4, 1]
    }

    recent_scans = Scan.query.order_by(Scan.created_at.desc()).limit(5).all()

    return render_template("dashboard.html",
        stats={
            "total_scans": total_scans,
            "critical_vulns": critical_vulns,
            "total_assets": total_assets,
            "recent_status": recent_status
        },
        chart_data=chart_data,
        owasp_data=owasp_data,
        recent_scans=recent_scans
    )"""
@bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    # 🔹 FIX: Conditional logic to display global or user-specific data
    if current_user.is_admin:
        # Admin view: fetch all data
        total_scans = Scan.query.count()
        critical_vulns = Scan.query.filter(Scan.result.ilike('%critical%')).count()
        total_assets = db.session.query(Scan.target_url).distinct().count()
        recent_scan = Scan.query.order_by(Scan.created_at.desc()).first()
        recent_scans = Scan.query.order_by(Scan.created_at.desc()).limit(5).all()
        # You'll need to update your models to have a 'result' column for this to work
        # properly. I've left it as is for now.

    else:
        # Regular user view: filter by current_user.id
        total_scans = Scan.query.filter_by(user_id=current_user.id).count()
        critical_vulns = Scan.query.filter_by(user_id=current_user.id).filter(Scan.result.ilike('%critical%')).count()
        total_assets = db.session.query(Scan.target_url).filter_by(user_id=current_user.id).distinct().count()
        recent_scan = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).first()
        recent_scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.created_at.desc()).limit(5).all()

    recent_status = recent_scan.status if recent_scan else "N/A"

    chart_data = {
        "labels": ["Critical", "High", "Medium", "Low", "Info"],
        "counts": [5, 12, 8, 3, 1]
    }

    owasp_data = {
        "labels": [
            "Injection", "Broken Auth", "Sensitive Data", "XML External Entities",
            "Broken Access Control", "Security Misconfig", "XSS", "Insecure Deserialization",
            "Using Components w/ Known Vulns", "Insufficient Logging"
        ],
        "counts": [15, 8, 5, 2, 10, 6, 12, 3, 4, 1]
    }

    return render_template("dashboard.html",
        stats={
            "total_scans": total_scans,
            "critical_vulns": critical_vulns,
            "total_assets": total_assets,
            "recent_status": recent_status
        },
        chart_data=chart_data,
        owasp_data=owasp_data,
        recent_scans=recent_scans
    )


user_decisions = {}

@bp.route('/api/socket/prompt', methods=['POST'])
def emit_user_prompt():
    data = request.json
    scan_id = data.get("scan_id")
    step = data.get("step")
    command = data.get("command")

    command_id = str(uuid.uuid4())
    user_decisions[command_id] = None
    # ✅ Inject command_id directly into the command object
    if isinstance(command, dict):  # safety check
        command["command_id"] = command_id
    else:
        print("[Error] command is not a dict:", command)

    socketio.emit(f"user_prompt_{scan_id}", {
        "step": step,
        "command": command_text,
        "command_id": command_id
    }, namespace="/scan")

    return jsonify({"command_id": command_id}), 200

@bp.route('/api/command/respond/<command_id>', methods=['POST'])
def receive_user_response(command_id):
    action = request.json.get("action")
    user_decisions[command_id] = action
    return jsonify({"status": "received"}), 200

@bp.route('/api/command/decision/<command_id>')
def get_user_decision(command_id):
    decision = user_decisions.get(command_id)
    return jsonify({"decision": decision}), 200

@bp.route('/api/command/wait', methods=['POST'])
def create_user_prompt():
    data = request.json
    scan_id = data.get("scan_id")
    step = data.get("step")
    command_text = data.get("command")

    command_id = str(uuid.uuid4())
    user_decisions[command_id] = None

    socketio.emit(f"user_prompt_{scan_id}", {
        "step": step,
        "command": command_text,
        "command_id": command_id
    }, namespace="/scan")

    # Return the command_id to the client (main.py)
    return jsonify({"command_id": command_id}), 200


# 🔹 NEW: Route to toggle scan pause/resume
@bp.route("/scan/<int:scan_id>/toggle_pause", methods=["POST"])
@login_required
def toggle_scan_pause(scan_id):
    scan = Scan.query.get_or_404(scan_id)

    # Authorization check: only the owner or an admin can toggle pause
    if scan.user_id != current_user.id and not current_user.is_admin:
        flash("You do not have permission to control this scan.", "danger")
        return jsonify({"success": False, "message": "Permission denied"}), 403

    # Toggle the paused status
    scan.is_paused = not scan.is_paused
    db.session.commit()

    action = "paused" if scan.is_paused else "resumed"
    flash(f"Scan '{scan.scan_name}' has been {action}.", "info")
    
    # Emit a Socket.IO event to update the UI immediately
    socketio.emit(
        f"scan_update_{scan_id}",
        {"message": f"[ℹ️] Scan {action}.", "status": scan.status, "is_paused": scan.is_paused},
        namespace="/scan"
    )

    return jsonify({"success": True, "is_paused": scan.is_paused})



