from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from models.ad import Ad
from database import db
from werkzeug.utils import secure_filename
import os

ads = Blueprint("ads", __name__)

def is_admin():
    return session.get("username") == ADMIN_USERNAME

@ads.route("/ads")
def list_ads():
    all_ads = Ad.query.order_by(Ad.created_at.desc()).all()
    return render_template("ads/list_ads.html", ads=all_ads, is_admin=is_admin())

@ads.route("/ads/add", methods=["GET", "POST"])
def add_ad():
    if not is_admin():
        abort(403)
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        image_file = request.files["image"]

        filename = None
        if image_file:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join("static/uploads", filename)
            image_file.save(image_path)

        new_ad = Ad(title=title, description=description, image=filename)
        db.session.add(new_ad)
        db.session.commit()
        return redirect(url_for("ads.list_ads"))

    return render_template("ads/add_ad.html")

@ads.route("/ads/edit/<int:ad_id>", methods=["GET", "POST"])
def edit_ad(ad_id):
    if not is_admin():
        abort(403)
    ad = Ad.query.get_or_404(ad_id)
    if request.method == "POST":
        ad.title = request.form["title"]
        ad.description = request.form["description"]
        image_file = request.files["image"]

        if image_file:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join("static/uploads", filename)
            image_file.save(image_path)
            ad.image = filename

        db.session.commit()
        return redirect(url_for("ads.list_ads"))

    return render_template("ads/edit_ad.html", ad=ad)

@ads.route("/ads/delete/<int:ad_id>", methods=["POST"])
def delete_ad(ad_id):
    if not is_admin():
        abort(403)
    ad = Ad.query.get_or_404(ad_id)
    db.session.delete(ad)
    db.session.commit()
    return redirect(url_for("ads.list_ads"))
