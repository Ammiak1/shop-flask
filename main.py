from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super secret key'
db = SQLAlchemy(app)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    isActive = db.Column(db.Boolean, default=True)
    text = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return self.title


@app.route("/api/items")
def api_get_items():
    items = Item.query.all()
    items_list = []
    for item in items:
        item_data = {
            'id': item.id,
            'title': item.title,
            'price': item.price,
            'isActive': item.isActive,
            'text': item.text
        }
        items_list.append(item_data)
    return jsonify(items_list)


@app.route("/api/item/<int:id>")
def api_get_item(id):
    item = Item.query.get(id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    item_data = {
        'id': item.id,
        'title': item.title,
        'price': item.price,
        'isActive': item.isActive,
        'text': item.text
    }
    return jsonify(item_data)


@app.route("/api/add_item", methods=["POST"])
def api_add_item():
    data = request.get_json()
    title = data.get('title')
    price = data.get('price')
    text = data.get('text')

    if not title or not price or not text:
        return jsonify({'error': 'Неправильно заполнены поля'}), 400

    new_item = Item(title=title, price=price, text=text)
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'message': 'Товар добавлен'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route("/api/delete_item/<int:id>", methods=["POST", "GET"])
def api_delete_item(id):
    item = Item.query.get(id)
    if not item:
        return jsonify({'error': 'Нет такого товара'}), 404

    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': 'Удалено'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route("/")
def index():
    items = Item.query.order_by(Item.price).all()
    cart = session.get('cart', [])
    return render_template("index.html", data=items, cart=cart)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        title = request.form["title"]
        price = request.form["price"]
        text = request.form["text"]
        item = Item(title=title, price=price, text=text)
        try:
            db.session.add(item)
            db.session.commit()
            return redirect("/")
        except Exception as er:
            return "Error"
    else:
        return render_template("create.html")


@app.route("/edit_items")
def edit_items():
    items = Item.query.order_by(Item.price).all()
    return render_template("edit_items.html", data=items)


@app.route("/delete_item/<int:id>", methods=["GET", "POST"])
def delete_item(id):
  if request.method == "GET":
    item = Item.query.get(id)
    if item:
      return render_template("delete_item.html", item=item)
    else:
      return "Такого товара нет."
  else:
    item = Item.query.get(id)
    if item:
      db.session.delete(item)
      db.session.commit()
      return redirect("/")
    else:
      return "Ошибка удаления товара."


@app.route("/edit_item/<int:id>", methods=["GET", "POST"])
def edit_item(id):
    item = Item.query.get_or_404(id)
    if request.method == "POST":
        item.title = request.form["title"]
        item.price = request.form["price"]
        item.text = request.form["text"]
        try:
            db.session.commit()
            return redirect("/")
        except Exception as e:
            return "Ошибка при редактировании товара."
    else:
        return render_template("edit_item.html", item=item)


@app.route("/cart")
def cart():
    cart = session.get('cart', [])
    return render_template("cart.html", cart=cart, Item=Item)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if request.method == "GET":
        total_price = 0
        for item in session.get('cart', []):
            total_price += item['quantity'] * Item.query.get(item['id']).price
        return render_template("checkout.html", total_price=total_price)
    else:
        session.pop('cart', None)
        return redirect("/")


@app.route("/update_cart/<int:id>", methods=["POST"])
def update_cart(id):
    cart = session.get('cart', [])
    item_index = None

    for i, item in enumerate(cart):
        if item['id'] == id:
            item_index = i
            break

    if item_index is None or int(request.form['quantity']) <= 0:
        return "Ошибка обновления количества."

    cart[item_index]['quantity'] = int(request.form['quantity'])
    session['cart'] = cart
    return redirect("/cart")


@app.route("/remove_from_cart/<int:id>")
def remove_from_cart(id):
    cart = session.get('cart', [])
    new_cart = [item for item in cart if item['id'] != id]
    session['cart'] = new_cart
    return redirect("/cart")


@app.route("/add_to_cart/<int:id>", methods=["POST", "GET"])
def add_to_cart(id):
    cart = session.get('cart', [])
    item = Item.query.get(id)

    if item and any(existing_item['id'] == item.id for existing_item in cart):
        for existing_item in cart:
            if existing_item['id'] == item.id:
                existing_item['quantity'] += 1
                break
    else:
        cart.append({'id': item.id, 'quantity': 1})

    session['cart'] = cart
    return redirect("/cart")


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


if __name__ == "__main__":
    app.run()
