from flask import Flask, render_template, request, redirect, session, flash, url_for
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
from notifications import send_alert # Ensure notifications.py uses Port 465

# 1. Initialize Flask App
app = Flask(__name__)
app.secret_key = "free_project_viva_safe_key"

# 2. ---------------- FIREBASE CONFIGURATION ----------------
firebase_json_env = os.environ.get('FIREBASE_JSON')

if firebase_json_env:
    try:
        service_account_info = json.loads(firebase_json_env)
        cred = credentials.Certificate(service_account_info)
    except Exception as e:
        print(f"Error parsing FIREBASE_JSON: {e}")
else:
    cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred)
db = firestore.client()

# ---------------- AUTHENTICATION ----------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/user_register/<type>", methods=["GET", "POST"])
def user_register(type):
    if request.method == "POST":
        try:
            data = {
                "name": request.form["name"],
                "email": request.form["email"],
                "phone": request.form["phone"],
                "password": request.form["password"],
                "type": type
            }
            db.collection("users").add(data)
            return redirect(url_for('user_login', type=type))
        except Exception as e:
            flash("Registration failed. Connection issue.")
    return render_template(f"{type}_user_register.html")

@app.route("/donor_register/<type>", methods=["GET", "POST"])
def donor_register(type):
    if request.method == "POST":
        try:
            f = request.form
            data = {
                "name": f["name"],
                "email": f["email"],
                "phone": f["phone"],
                "password": f["password"],
                "donor_type": type,
                "blood_group": f.get("blood_group", "").upper(),
                "hla1": f.get("hla1", ""), "hla2": f.get("hla2", ""), "hla3": f.get("hla3", ""),
                "hla4": f.get("hla4", ""), "hla5": f.get("hla5", ""), "hla6": f.get("hla6", ""),
                "hb": float(f.get("hb", 0)),
                "available": 1
            }
            db.collection("donors").add(data)
            return redirect(url_for('donor_login', type=type))
        except Exception as e:
            flash("Donor registration failed.")
    return render_template(f"{type}_donor_register.html")

@app.route("/user_login/<type>", methods=["GET", "POST"])
def user_login(type):
    if request.method == "POST":
        try:
            users_ref = db.collection("users")
            query = users_ref.where("email", "==", request.form["email"])\
                             .where("password", "==", request.form["password"])\
                             .where("type", "==", type).limit(1).get()
            if query:
                user = query[0]
                session.clear()
                session["user_id"] = user.id 
                session["user_type"] = type
                return redirect(url_for(f'{type}_user_dashboard'))
            flash("Invalid Credentials")
        except Exception as e:
            flash("Login service unavailable.")
    return render_template(f"{type}_user_login.html")

@app.route("/donor_login/<type>", methods=["GET", "POST"])
def donor_login(type):
    if request.method == "POST":
        try:
            donors_ref = db.collection("donors")
            query = donors_ref.where("email", "==", request.form["email"])\
                              .where("password", "==", request.form["password"])\
                              .where("donor_type", "==", type).limit(1).get()
            if query:
                donor = query[0]
                session.clear()
                session["donor_id"] = donor.id
                session["donor_type"] = type
                return redirect(url_for('donor_dashboard'))
            flash("Invalid Credentials")
        except Exception as e:
            flash("Donor login service unavailable.")
    return render_template(f"{type}_donor_login.html")

# ---------------- SAFE DASHBOARDS (FIXES TIMEOUTS) ----------------

@app.route("/blood_user_dashboard", methods=["GET", "POST"])
def blood_user_dashboard():
    if "user_id" not in session: return redirect("/")
    
    if request.method == "POST":
        f = request.form
        blood_grp = f["blood_group"].strip().upper()
        
        try:
            # 1. Save Request to Firestore First
            db.collection("requests").add({
                "user_id": session["user_id"],
                "type": "blood",
                "blood_group": blood_grp,
                "urgency": f["urgency"],
                "hospital": f["hospital"],
                "amount": f["amount"],
                "req_date": f["req_date"],
                "status": "Pending"
            })

            # 2. Attempt Email Alerts in a separate Safe Block
            try:
                donors_ref = db.collection("donors").where("donor_type", "==", "blood")\
                                                    .where("blood_group", "==", blood_grp)\
                                                    .where("available", "==", 1).get()
                for d_doc in donors_ref:
                    donor = d_doc.to_dict()
                    subj = f"URGENT: {blood_grp} Blood Necessity"
                    body = f"Hello {donor['name']}, urgent blood needed at {f['hospital']}."
                    send_alert(donor['email'], subj, body) # Might be slow, but caught by 'except'
            except Exception as email_err:
                print(f"Email alert skipped due to timeout/port block: {email_err}")

            flash("Request submitted successfully!")
        except Exception as e:
            print(f"DB Error: {e}")
            flash("Could not submit request. Try again.")
    
    # Fetching accepted donors safely
    accepted_list = []
    try:
        responses = db.collection("donor_responses").where("response", "==", "Accepted").get()
        for resp in responses:
            r_data = resp.to_dict()
            req_doc = db.collection("requests").document(r_data["request_id"]).get()
            if req_doc.exists and req_doc.to_dict().get("user_id") == session["user_id"]:
                d_doc = db.collection("donors").document(r_data["donor_id"]).get()
                if d_doc.exists:
                    accepted_list.append(d_doc.to_dict())
    except: pass
                
    return render_template("blood_user_dashboard.html", donors=accepted_list)

@app.route("/marrow_user_dashboard", methods=["GET", "POST"])
def marrow_user_dashboard():
    if "user_id" not in session: return redirect("/")
    
    if request.method == "POST":
        f = request.form
        try:
            db.collection("requests").add({
                "user_id": session["user_id"], "type": "marrow",
                "hla1": f["hla1"], "hla2": f["hla2"], "hla3": f["hla3"],
                "hla4": f["hla4"], "hla5": f["hla5"], "hla6": f["hla6"],
                "urgency": f["urgency"], "hospital": f["hospital"],
                "amount": f["amount"], "req_date": f["req_date"], "status": "Pending"
            })
            flash("Marrow registry request initiated.")
        except:
            flash("Connection error.")

    accepted_list = []
    try:
        responses = db.collection("donor_responses").where("response", "==", "Accepted").get()
        for resp in responses:
            r_data = resp.to_dict()
            req_doc = db.collection("requests").document(r_data["request_id"]).get()
            if req_doc.exists and req_doc.to_dict().get("user_id") == session["user_id"]:
                d_doc = db.collection("donors").document(r_data["donor_id"]).get()
                if d_doc.exists:
                    accepted_list.append(d_doc.to_dict())
    except: pass

    return render_template("marrow_user_dashboard.html", donors=accepted_list)

# ---------------- DONOR MANAGEMENT ----------------

@app.route("/donor_dashboard", methods=["GET", "POST"])
def donor_dashboard():
    if "donor_id" not in session: return redirect("/")
    
    try:
        donor_ref = db.collection("donors").document(session["donor_id"])
        if request.method == "POST":
            donor_ref.update({
                "available": int(request.form["available"]),
                "hb": float(request.form["hb"]),
                "phone": request.form["phone"]
            })
            flash("Profile Updated.")

        donor = donor_ref.get().to_dict()
        eligible = []
        
        if int(donor.get("available", 0)) == 1 and float(donor.get("hb", 0)) >= 12.5:
            pending_reqs = db.collection("requests").where("status", "==", "Pending")\
                                                   .where("type", "==", donor["donor_type"]).limit(10).get()
            for r_doc in pending_reqs:
                r = r_doc.to_dict()
                r['id'] = r_doc.id
                if donor["donor_type"] == "blood":
                    if r["blood_group"].upper() == donor["blood_group"].upper():
                        eligible.append({"request": r, "score": None})
                else:
                    d_hla = [donor.get(f'hla{i}') for i in range(1,7)]
                    r_hla = [r.get(f'hla{i}') for i in range(1,7)]
                    score = sum(1 for d_v, r_v in zip(d_hla, r_hla) if d_v and r_v and d_v.strip().lower() == r_v.strip().lower())
                    if score >= 4:
                        eligible.append({"request": r, "score": score})

        return render_template("donor_dashboard.html", requests=eligible, donor=donor)
    except Exception as e:
        print(f"Dashboard Error: {e}")
        return "Critical Database Timeout. Please refresh."

@app.route("/accept/<rid>")
def accept(rid):
    if "donor_id" not in session: return redirect("/")
    
    try:
        donor_doc = db.collection("donors").document(session["donor_id"]).get()
        req_doc = db.collection("requests").document(rid).get()
        
        if not req_doc.exists: return redirect(url_for('donor_dashboard'))
        
        req = req_doc.to_dict()
        donor = donor_doc.to_dict()
        user_snap = db.collection("users").document(req["user_id"]).get()
        user = user_snap.to_dict()

        # Database Update
        db.collection("donor_responses").add({
            "request_id": rid, "donor_id": session["donor_id"], "response": "Accepted"
        })
        db.collection("requests").document(rid).update({"status": "Accepted"})

        # Safe Email Alerts
        try:
            send_alert(user['email'], "Match Found!", f"Donor {donor['name']} accepted. Phone: {donor['phone']}")
            send_alert(donor['email'], "Confirmed", "You accepted a donation request.")
        except: pass

        flash("Accepted! Notification attempt complete.")
    except:
        flash("Action failed due to timeout.")
        
    return redirect(url_for('donor_dashboard'))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
