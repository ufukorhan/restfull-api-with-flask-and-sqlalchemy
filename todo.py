from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import uuid

app = Flask(__name__)
db = SQLAlchemy(app)

app.config['SECRET_KEY'] = 'secret' # It’s used by some middleware (extensions) that have to do with security (for now we have none)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://///home/ufuk/Desktop/restfull-api/todo.db' # which is the database curl for our app


class User(db.Model):
	id = db.Column(db.Integer, primary_key=True, index=True)
	name = db.Column(db.String(20), nullable=False)
	email = db.Column(db.String(28), nullable=False, unique=True)
	public_id = db.Column(db.String, nullable=False)
	is_admin = db.Column(db.Boolean, default=False)
	todos=db.relationship('Todo', backref='owner', lazy='dynamic')

	def __repr__(self):
		return f'User <{self.email}>'

class Todo(db.Model):
	id = db.Column(db.Integer, primary_key=True, index=True)
	name = db.Column(db.String(20), nullable=False)
	is_completed = db.Column(db.Boolean, default=False)
	public_id = db.Column(db.String, nullable=False)
	user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

	def __repr__(self):
		return f'Todo: <{self.name}>'


@app.route('/')
def home():
	return {
		'message': 'Welcome to building RESTful APIs with Flask and SQLAlchemy'
	}


@app.route('/users/')
def get_users():
	return jsonify([
		{
			'id': user.public_id, 'name': user.name, 'email': user.email,
			'is admin': user.is_admin
			} for user in User.query.all()
	])

@app.route('/users/<id>/')
def get_user(id):
	print(id)
	user = User.query.filter_by(public_id=id).first_or_404()
	return {
		'id': user.public_id, 'name': user.name, 
		'email': user.email, 'is admin': user.is_admin
		}

@app.route('/users/', methods=['POST'])
def create_user():
	data = request.get_json()
	if not 'name' in data or not 'email' in data:
		return jsonify({
			'error': 'Bad Request',
			'message': 'Name or email not given'
		}), 400
	if len(data['name']) < 4 or len(data['email']) < 6:
		return jsonify({
			'error': 'Bad Request',
			'message': 'Name and email must be contain minimum of 4 letters'
		}), 400
	u = User(
			name=data['name'], 
			email=data['email'],
			is_admin=data.get('is admin', False),
			public_id=str(uuid.uuid4())
		)
	db.session.add(u)
	db.session.commit()
	return {
		'id': u.public_id, 'name': u.name, 
		'email': u.email, 'is admin': u.is_admin 
	}, 201

@app.route('/users/<string:id>/', methods=['PUT'])
def update_user(id):
	data = request.get_json()
	if 'name' not in data:
		return {
			'error': 'Bad Request',
			'message': 'Name field needs to be present'
		}, 400
	user = User.query.filter_by(public_id=id).first_or_404()
	user.name=data['name']
	if 'is admin' in data:
		user.is_admin=data['admin']
	db.session.commit()
	return jsonify({
		'id': user.public_id, 
		'name': user.name, 'is admin': user.is_admin,
		'email': user.email
		})

@app.route('/users/<id>/', methods=['DELETE'])
def delete_user(id):
	user = User.query.filter_by(public_id=id).first_or_404()
	db.session.delete(user)
	db.session.commit()
	return {
		'success': 'Data deleted successfully'
	}


if __name__ == '__main__':
	app.run()