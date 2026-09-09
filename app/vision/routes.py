from flask import Blueprint, render_template

vision_bp = Blueprint('vision', __name__)

@vision_bp.route('/')
def index():
    return 'vision'

@vision_bp.route('/post/<int:post_id>')
def post(post_id):
    return render_template('blog/post.html', post_id=post_id)