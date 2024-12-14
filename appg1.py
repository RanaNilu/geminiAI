from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Database Configuration (Use SQLite for simplicity in this example)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ai_professor.db'  # Use an absolute path in production
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress warning
db = SQLAlchemy(app)

# Models
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)  # Store course content (consider file storage for large files)

    def to_dict(self):  # Helper function to convert object to dictionary
        return {'id': self.id, 'title': self.title, 'description': self.description, 'content': self.content}

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    message = db.Column(db.Text)
    is_student = db.Column(db.Boolean)  # True if student, False if professor (AI)

class UsefulLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    url = db.Column(db.String(255))
    link_type = db.Column(db.String(50)) #e.g., 'video', 'audio', 'image', 'text'
    description = db.Column(db.Text)

# Create database tables if they don't exist (important for first run)
with app.app_context():
    db.create_all()

# Course Management Routes (CRUD)
@app.route('/courses', methods=['GET', 'POST'])
def manage_courses():
    if request.method == 'GET':
        courses = Course.query.all()
        return jsonify([course.to_dict() for course in courses])
    elif request.method == 'POST':
        data = request.get_json()
        new_course = Course(title=data['title'], description=data['description'], content=data['content'])
        db.session.add(new_course)
        db.session.commit()
        return jsonify({'message': 'Course created', 'course_id': new_course.id}), 201

@app.route('/courses/<int:course_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_course(course_id):
    course = Course.query.get_or_404(course_id)
    if request.method == 'GET':
        return jsonify(course.to_dict())
    elif request.method == 'PUT':
        data = request.get_json()
        course.title = data.get('title', course.title)
        course.description = data.get('description', course.description)
        course.content = data.get('content', course.content)
        db.session.commit()
        return jsonify({'message': 'Course updated'})
    elif request.method == 'DELETE':
        db.session.delete(course)
        db.session.commit()
        return jsonify({'message': 'Course deleted'})

# Student Chat Route
@app.route('/courses/<int:course_id>/chat', methods=['POST', 'GET'])
def course_chat(course_id):
    if request.method == 'POST':
      data = request.get_json()
      message = data.get('message')
      is_student = data.get('is_student') #get if the message is from student or AI
      new_message = ChatMessage(course_id=course_id, message=message, is_student=is_student)
      db.session.add(new_message)
      db.session.commit()
      return jsonify({'message': 'Message sent'}), 201
    elif request.method == 'GET': #get all the chat history of a course
        messages = ChatMessage.query.filter_by(course_id=course_id).all()
        messages_list = []
        for msg in messages:
            messages_list.append({'message':msg.message, 'is_student': msg.is_student})
        return jsonify(messages_list)


# Useful Links Route
@app.route('/courses/<int:course_id>/links', methods=['POST', 'GET'])
def course_links(course_id):
    if request.method == 'POST':
        data = request.get_json()
        new_link = UsefulLink(course_id=course_id, url=data['url'], link_type=data['link_type'], description=data.get('description',None))
        db.session.add(new_link)
        db.session.commit()
        return jsonify({'message': 'Link added'}), 201
    elif request.method == 'GET':
        links = UsefulLink.query.filter_by(course_id=course_id).all()
        link_list = []
        for link in links:
            link_list.append({'url': link.url, 'link_type': link.link_type, 'description': link.description})
        return jsonify(link_list)

if __name__ == '__main__':
    app.run(debug=True)