

from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import pika

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db?check_same_thread=False'
db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    text = db.Column(db.Text, nullable=False)

@app.route('/')
@app.route('/api/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route("/orders")
def orders():
    orders = Post.query.all()
    return render_template('orders.html', orders=orders)

@app.route('/create', methods=['POST', 'GET'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        text = request.form['text']
        post = Post(title=title, text=text)

        try:
            db.session.add(post)
            db.session.commit()

            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            channel.queue_declare(queue='orders')
            channel.basic_publish(exchange='', routing_key='orders', body=f"{title}: {text}")
            connection.close()

            return redirect('/create')
        except Exception as e:
            return f'Eror from safe: {e}'
    else:
        return render_template('create.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
