from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean
import random
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)

# CREATE DB
class Base(declarative_base()):
    pass

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Cafe TABLE Configuration
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        dictionary = {}
        for column in self.__table__.columns:
            dictionary[column.name] = getattr(self, column.name)
        return dictionary

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

# HTTP GET - Read Record
@app.route("/random", methods=["GET"])
def get_random_cafe():
    try:
        cafes = db.session.execute(db.select(Cafe)).scalars().all()
        if not cafes:
            raise IndexError("No cafes found.")
        random_cafe = random.choice(cafes)
        return jsonify(cafe=random_cafe.to_dict())
    except IndexError as e:
        return jsonify(error=str(e)), 404
    except SQLAlchemyError as e:
        return jsonify(error="Database error occurred"), 500

@app.route("/all", methods=["GET"])
def all_cafe():
    try:
        cafes = db.session.execute(db.select(Cafe)).scalars().all()
        return jsonify(cafes=[cafe.to_dict() for cafe in cafes])
    except SQLAlchemyError as e:
        return jsonify(error="Database error occurred"), 500

@app.route("/search", methods=["GET"])
def get_cafe_at_location():
    query_location = request.args.get("loc")
    try:
        cafes = db.session.execute(db.select(Cafe).where(Cafe.location == query_location)).scalars().all()
        if cafes:
            return jsonify(cafes=[cafe.to_dict() for cafe in cafes])
        else:
            return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."}), 404
    except SQLAlchemyError as e:
        return jsonify(error="Database error occurred"), 500

# HTTP POST - Create Record
@app.route("/add", methods=["POST"])
def post_new_cafe():
    try:
        new_cafe = Cafe(
            name=request.form.get("name"),
            map_url=request.form.get("map_url"),
            img_url=request.form.get("img_url"),
            location=request.form.get("loc"),
            has_sockets=bool(request.form.get("sockets")),
            has_toilet=bool(request.form.get("toilet")),
            has_wifi=bool(request.form.get("wifi")),
            can_take_calls=bool(request.form.get("calls")),
            seats=request.form.get("seats"),
            coffee_price=request.form.get("coffee_price"),
        )
        db.session.add(new_cafe)
        db.session.commit()
        return jsonify(response="Successfully added the new cafe.")
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify(error="Database error occurred"), 500

# HTTP PUT/PATCH - Update Record
@app.route("/update-price/<int:cafe_id>", methods=["PATCH"])
def patch_new_price(cafe_id):
    new_price = request.args.get("new_price")
    try:
        cafe = db.get_or_404(Cafe, cafe_id)
        cafe.coffee_price = new_price
        db.session.commit()
        return jsonify(response={"success": "Successfully updated"})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify(error="Database error occurred"), 500
    except Exception as e:
        return jsonify(error=str(e)), 404

# HTTP DELETE - Delete Record - new text
@app.route("/report-closed/<int:cafe_id>", methods=["DELETE"])
def delete_cafe(cafe_id):
    api_key = request.args.get("api-key")
    try:
        if api_key == "TopSecretAPIKey":
            cafe = db.get_or_404(Cafe, cafe_id)
            db.session.delete(cafe)
            db.session.commit()
            return jsonify(response={"success": "Successfully deleted"}), 200
        else:
            return jsonify(error={"Forbidden": "Sorry, that's not allowed. Make sure you have the correct api_key."}), 403
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify(error="Database error occurred"), 500
    except Exception as e:
        return jsonify(error=str(e)), 404

if __name__ == '__main__':
    app.run(debug=True)
