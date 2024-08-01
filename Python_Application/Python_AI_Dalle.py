from flask import Flask, render_template_string, request, redirect, url_for
import requests
import json

app = Flask(__name__)

HTML_TEMPLATE = '''
<!doctype html>
<html>
<head>
    <title>Image Generator</title>
    <style>
        textarea, input[type="submit"] {
            vertical-align: middle; /* 对齐方式 */
            padding: 10px;
            margin: 10px 0;
            box-sizing: border-box;
        }
        textarea {
        width: 600px; /* 初始宽度 */
        max-width: 100%; /* 最大宽度 */
        min-height: 100px; /* 最小高度 */
        padding: 10px;
        margin: 10px 0;
        box-sizing: border-box;
        resize: both; /* 允许用户调整大小 */
        overflow-x: hidden; /* 隐藏水平滚动条 */
        font-size: 16px; /* 设置字体大小 */
        }
        input[type="submit"] {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        margin: 10px 0;
        width: 150px; /* 设置按钮的固定宽度 */
        vertical-align: left; /* 对齐方式 */
        }
            img {
            max-width: 100%;
            height: auto;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h1>Image Generator</h1>
    <form method="post" action="/">
        Enter a description for the image:<br>
        <textarea name="prompt" placeholder="e.g., a futuristic city skyline">{{ prompt }}</textarea><br>
        <input type="submit" value="Generate Image">
    </form>
    {% if image_src %}
        <h2>Generated Image:</h2>
        <!-- 显示缩略图 -->
        <!-- 
        <img src="{{ image_src }}" alt="Generated Image" onclick="window.open(this.src, '_blank');" style="width: 300px;">  -->
        <!-- 显示原图 -->
        <img src="{{ image_src }}" alt="Generated Image" onclick="window.open(this.src, '_blank');">
    {% else %}
        <p>No image to display.</p>
    {% endif %}
</body>
</html>
'''


@app.route('/', methods=['GET', 'POST'])
def index():
    prompt = ''
    image_src = None
    if request.method == 'POST':
        prompt = request.form.get('prompt', '')
        url = "https://burn.hair/v1/images/generations"
        headers = {
            "Authorization": "Bearer sk-ySOZXKC68tIwP6e8Bb3689Cb914044Bc90B51c8a321e6c15"
        }
        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            response_data = json.loads(response.content)
            image_src = response_data['data'][0]['url']
        else:
            print(f"Failed to fetch image, status code: {response.status_code}")
    return render_template_string(HTML_TEMPLATE, prompt=prompt, image_src=image_src)


if __name__ == '__main__':
    app.run(debug=True)
