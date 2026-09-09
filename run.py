from flask import Flask
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    return 'Hello, World!'

# 导入蓝图 (修改为从模块导入)
from app.robot.routes import robot_bp
from app.vision.routes import vision_bp

# 注册蓝图 (添加了静态文件处理)
app.register_blueprint(
    robot_bp,
    url_prefix='/robot',
    # static_folder='static',  # 可选的静态文件配置
    # template_folder='templates'
)

app.register_blueprint(
    vision_bp,
    url_prefix='/vision',
    # static_folder='static',  # 可选的静态文件配置
    # template_folder='templates'
)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)