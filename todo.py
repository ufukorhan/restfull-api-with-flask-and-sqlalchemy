from crypt import methods
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import uuid
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
db = SQLAlchemy(app)

app.config['SECRET_KEY'] = 'secret' # It’s used by some middleware (extensions) that have to do with security (for now we have none)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("database_path") # which is the database curl for my app


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
		user.is_admin=data['is admin']
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

# Above part includes user endpoints
# ----------------------------------
# Upper part includes todo endpoints

@app.route('/todos/')
def get_todos():
	return jsonify([
		{ 
			'id': todo.public_id, 'name': todo.name,
			'owner': {
				'name': todo.owner.name,
				'email': todo.owner.email,
				'public_id': todo.owner.public_id
			}
		} for todo in Todo.query.all()
	])

@app.route('/todos/<id>')
def get_todo(id):
	todo = Todo.query.filter_by(public_id=id).first_or_404()
	return jsonify({ 
			'id': todo.public_id, 'name': todo.name,
			'owner': {
				'name': todo.owner.name,
				'email': todo.owner.email,
				'public_id': todo.owner.public_id
			}
		})

@app.route('/todos/', methods=['POST'])
def create_todo():
	data = request.get_json()
	if not 'name' in data or not 'email' in data:
		return jsonify({
			'error': 'Bad Request',
			'message': 'Name of todo or email of creator not given'
		}), 400
	if len(data['name']) < 4:
		return jsonify({
			'error': 'Bad Request',
			'message': 'Name of todo contain minimum of 4 letters'
		}), 400

	user=User.query.filter_by(email=data['email']).first()
	if not user:
		return {
			'error': 'Bad request',
			'message': 'Invalid email, no user with that email'
		}
	is_completed = data.get('is completed', False)
	todo = Todo(
		name=data['name'], user_id=user.id,
		is_completed=is_completed, public_id=str(uuid.uuid4())
	)
	db.session.add(todo)
	db.session.commit()
	return {
		'id': todo.public_id, 'name': todo.name, 
		'completed': todo.is_completed,
		'owner': {
			'name': todo.owner.name,
			'email': todo.owner.email,
			'is admin': todo.owner.is_admin 
		} 
	}, 201

@app.route('/todos/<id>/', methods=['PUT'])
def update_todo(id):
	data = request.get_json()

	if not 'name' in data or not 'completed' in data:
		return {
			'error': 'Bad Request',
			'message': 'Name or completed fields need to be present'
		}, 400
	todo = Todo.query.filter_by(public_id=id).first_or_404()
	todo.name=data.get('name', todo.name)
	if 'completed' in data:
		todo.is_completed=data['completed']
	db.session.commit()
	return {
		'id': todo.public_id, 'name': todo.name, 
		'is completed': todo.is_completed,
		'owner': {
			'name': todo.owner.name, 'email': todo.owner.email,
			'is admin': todo.owner.is_admin 
		} 
	}, 201

@app.route('/todos/<id>/', methods=['DELETE'] )
def delete_todo(id):
	todo = Todo.query.filter_by(public_id=id).first_or_404()
	db.session.delete(todo)
	db.session.commit()
	return {
		'success': 'Data deleted successfully'
	}


if __name__ == '__main__':
	app.run()