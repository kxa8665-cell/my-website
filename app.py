import os
import io
import PyPDF2
import requests
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from queue import Queue
import json
import tempfile
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# 配置Tesseract OCR路径
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 初始化Flask应用
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
CORS(app)

import pdfkit

# 尝试自动配置pdfkit
try:
    # 直接设置正确的路径，不依赖环境变量
    wkhtmltopdf_path = 'D:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe'
    app.logger.info(f'尝试使用wkhtmltopdf路径: {wkhtmltopdf_path}')
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
    # 测试配置是否有效
    pdfkit.from_string('测试', 'test.pdf', configuration=config)
    os.remove('test.pdf')
    app.logger.info('成功配置wkhtmltopdf。')
except (OSError, IOError) as e:
    app.logger.warning(f'配置失败: {str(e)}')
    # 尝试从PATH中查找
    try:
        app.logger.info('尝试从PATH中查找wkhtmltopdf...')
        config = pdfkit.configuration()
        pdfkit.from_string('测试', 'test.pdf', configuration=config)
        os.remove('test.pdf')
        app.logger.info('成功从PATH中找到并配置wkhtmltopdf。')
    except (OSError, IOError) as e2:
        # 如果所有尝试都失败，使用空配置
        config = None
        app.logger.error(f'无法找到wkhtmltopdf可执行文件: {str(e2)}')
        app.logger.warning('请按照以下步骤配置wkhtmltopdf:')
        app.logger.warning('1. 确保已安装wkhtmltopdf (可从https://wkhtmltopdf.org/downloads.html下载)')
        app.logger.warning('2. 安装完成后，将其安装路径添加到系统PATH环境变量中')
        app.logger.warning('3. 或者，设置环境变量WKHTMLTOPDF_PATH指向可执行文件')
        app.logger.warning('4. 或者，直接在代码中修改wkhtmltopdf_path变量为正确的安装路径')

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
PARSED_FOLDER = 'parsed_texts'
REPORT_FOLDER = 'reports'
for folder in [UPLOAD_FOLDER, PARSED_FOLDER, REPORT_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# 检查上传目录权限
if not os.access(UPLOAD_FOLDER, os.W_OK):
    app.logger.error(f'上传目录 {UPLOAD_FOLDER} 没有写入权限')

# 检查解析文本保存目录权限
if not os.access(PARSED_FOLDER, os.W_OK):
    app.logger.error(f'解析文本保存目录 {PARSED_FOLDER} 没有写入权限')

# 任务队列和结果存储
task_queue = Queue()
results = {}

# PDF解析函数
# PDF解析函数
def parse_pdf(file_path):
    try:
        app.logger.info(f'开始解析PDF文件: {file_path}')
        # 检查文件是否存在
        if not os.path.exists(file_path):
            error_msg = f'文件不存在: {file_path}'
            app.logger.error(error_msg)
            return None, error_msg
        # 检查文件大小是否为0
        if os.path.getsize(file_path) == 0:
            error_msg = f'文件为空: {file_path}'
            app.logger.error(error_msg)
            return None, error_msg
        
        # 首先尝试使用PyPDF2提取文本
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            total_pages = len(reader.pages)
            app.logger.info(f'PDF文件共有{total_pages}页')
            for page_num in range(total_pages):
                page = reader.pages[page_num]
                page_text = page.extract_text() or ''
                text += page_text
                app.logger.info(f'已解析第{page_num + 1}页，获取{len(page_text)}个字符')
            app.logger.info(f'PDF文件解析完成，共{len(text)}个字符')
            
            # 如果成功提取到文本，直接返回
            if text.strip():
                return text, None
            
            # 如果没有提取到文本，尝试OCR
            app.logger.warning(f'PDF文件未提取到文本内容，尝试OCR: {file_path}')
            
        # 使用PyMuPDF和pytesseract进行OCR
        ocr_text = ''
        doc = None
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                page_text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                ocr_text += page_text
                app.logger.info(f'OCR处理第{page_num + 1}页，获取{len(page_text)}个字符')
        except Exception as e:
            error_msg = f'OCR处理失败: {str(e)}'
            app.logger.error(f'{error_msg}，文件路径: {file_path}')
            return None, error_msg
        finally:
            if doc is not None:
                doc.close()
        
        if ocr_text.strip():
            app.logger.info(f'OCR完成，共{len(ocr_text)}个字符')
            return ocr_text, None
        else:
            error_msg = 'PDF文件解析成功，但未提取到任何文本内容'
            app.logger.warning(f'{error_msg}: {file_path}')
            return None, error_msg
            
    except PyPDF2.errors.PdfReadError as e:
        error_msg = f'PDF文件格式错误或损坏: {str(e)}'
        app.logger.error(f'{error_msg}，文件路径: {file_path}')
        return None, error_msg
    except PyPDF2.errors.PermissionError as e:
        error_msg = f'PDF文件已加密，无法解析: {str(e)}'
        app.logger.error(f'{error_msg}，文件路径: {file_path}')
        return None, error_msg
    except Exception as e:
        error_msg = f'PDF解析错误: {str(e)}'
        app.logger.error(f'{error_msg}，文件路径: {file_path}')
        app.logger.error(f'异常类型: {type(e).__name__}')
        app.logger.exception(f'解析文件 {file_path} 时发生异常')
        return None, error_msg

# DeepSeek API调用函数
def call_deepseek_api(api_key, prompt, file_contents=None):
    base_url = 'https://api.deepseek.com'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # 构建消息内容
    messages = [{'role': 'user', 'content': prompt}]
    
    # 如果有文件内容，添加到消息中
    if file_contents:
        for filename, content in file_contents.items():
            messages.append({
                'role': 'user', 
                'content': f'文件内容 ({filename}):\n{content[:10000]}...'  # 限制内容长度
            })
    
    data = {
        'model': 'deepseek-reasoner',
        'messages': messages,
        'stream': True
    }
    
    try:
        response = requests.post(f'{base_url}/chat/completions', headers=headers, json=data, stream=True)
        response.raise_for_status()
        return response.iter_lines()
    except Exception as e:
        app.logger.error(f'DeepSeek API调用错误: {str(e)}')
        return [f'错误: {str(e)}']

# 创建线程池，最大工作线程数为5
executor = ThreadPoolExecutor(max_workers=5)

# 提交任务处理函数到线程池
def submit_task_to_pool():
    while True:
        task = task_queue.get()
        if task is None:
            break
        executor.submit(process_single_task, *task)
        task_queue.task_done()

# 启动任务提交线程
Thread(target=submit_task_to_pool, daemon=True).start()

# 单个任务处理函数
def process_single_task(task_id, api_key, prompt, file_contents):
    results[task_id] = {'status': 'processing', 'content': []}
    
    try:
        # 调用DeepSeek API
        for line in call_deepseek_api(api_key, prompt, file_contents):
            if line:
                line = line if isinstance(line, str) else line.decode('utf-8')
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if 'choices' in data and len(data['choices']) > 0:
                            content = data['choices'][0].get('delta', {}).get('content', '')
                            if content:
                                results[task_id]['content'].append(content)
                    except json.JSONDecodeError:
                        continue
        results[task_id]['status'] = 'completed'
    except Exception as e:
        results[task_id]['status'] = 'error'
        results[task_id]['content'].append(f'处理错误: {str(e)}')

# 路由定义
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    app.logger.info('收到文件上传请求')
    if 'file' not in request.files:
        app.logger.error('请求中没有文件部分')
        return jsonify({'error': '没有文件部分'}), 400
    
    files = request.files.getlist('file')
    total_files = len(files)
    app.logger.info(f'收到{total_files}个文件，将按顺序依次解析')
    uploaded_files = []
    
    for i, file in enumerate(files, 1):
        app.logger.info(f'开始处理第{i}/{total_files}个文件')
        if file.filename == '':
            app.logger.warning(f'第{i}/{total_files}个文件为空文件名，跳过')
            continue
        if file and file.filename.lower().endswith('.pdf'):
            app.logger.info(f'处理PDF文件 {i}/{total_files}: {file.filename}')
            filename = str(uuid.uuid4()) + '.pdf'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                file.save(filepath)
                app.logger.info(f'文件 {i}/{total_files} 保存成功: {filepath}')
            except Exception as e:
                app.logger.error(f'文件 {i}/{total_files} 保存失败: {str(e)}')
                uploaded_files.append({
                    'original_name': file.filename,
                    'saved_name': filename,
                    'text_filename': None,
                    'size': 0,
                    'upload_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'error': f'文件保存失败: {str(e)}',
                    'processing_order': i
                })
                continue
            
            # 解析PDF (按顺序同步解析)
            app.logger.info(f'开始解析文件 {i}/{total_files}: {file.filename}')
            # 添加延迟
            time.sleep(1)
            parsed_text, parse_error = parse_pdf(filepath)
            app.logger.info(f'解析文件 {i}/{total_files} 后的错误信息: {parse_error}')  # 添加调试日志
            # 检查parse_error是否为空
            if parse_error is None:
                app.logger.warning(f'parse_error为空，使用默认错误信息')
                error_message = 'PDF解析失败'
            else:
                app.logger.info(f'parse_error不为空，详细错误信息: {parse_error}')
                error_message = parse_error
                # 确保错误信息被正确使用
                app.logger.info(f'准备返回的错误信息: {error_message}')

            if parsed_text:
                text_filename = filename.replace('.pdf', '.txt')
                text_path = os.path.join(PARSED_FOLDER, text_filename)
                try:
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(parsed_text)
                    app.logger.info(f'文件 {i}/{total_files} 文本解析成功并保存: {text_path}')
                except Exception as e:
                    app.logger.error(f'文件 {i}/{total_files} 文本保存失败: {str(e)}')
                    app.logger.exception(f'保存文件 {i}/{total_files} 时发生异常')
                    continue
                
                uploaded_files.append({
                    'original_name': file.filename,
                    'saved_name': filename,
                    'text_filename': text_filename,
                    'size': os.path.getsize(filepath),
                    'upload_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'processing_order': i
                })
            else:
                # 使用解析函数返回的错误信息，如果没有则使用默认信息
                error_message = parse_error if parse_error else 'PDF解析失败'
                app.logger.error(f'文件 {i}/{total_files} PDF解析失败，文件路径: {filepath}, 详细错误: {error_message}')
                uploaded_files.append({
                    'original_name': file.filename,
                    'saved_name': filename,
                    'text_filename': None,
                    'size': os.path.getsize(filepath),
                    'upload_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'error': error_message,
                    'processing_order': i
                })
        else:
            app.logger.warning(f'跳过非PDF文件 {i}/{total_files}: {file.filename}')
            # 对于非PDF文件，也可以返回信息
            uploaded_files.append({
                'original_name': file.filename,
                'error': '非PDF文件，已跳过',
                'processing_order': i
            })
        app.logger.info(f'完成处理第{i}/{total_files}个文件')
    
    # 过滤掉没有text_filename的文件
    valid_files = [f for f in uploaded_files if f.get('text_filename')]
    app.logger.info(f'成功解析并可使用的文件数量: {len(valid_files)}/{total_files}')
    
    return jsonify({
        'files': uploaded_files,
        'total_files': total_files,
        'valid_files_count': len(valid_files)
    })

@app.route('/get_parsed_text/<text_filename>')
def get_parsed_text(text_filename):
    text_path = os.path.join(PARSED_FOLDER, text_filename)
    if os.path.exists(text_path):
        with open(text_path, 'r', encoding='utf-8') as f:
            return jsonify({'content': f.read()})
    return jsonify({'error': '文件不存在'}), 404

@app.route('/check_parsing_status/<text_filename>')
def check_parsing_status(text_filename):
    text_path = os.path.join(PARSED_FOLDER, text_filename)
    if os.path.exists(text_path):
        return jsonify({'status': 'completed'})
    # 检查对应的PDF文件是否存在
    pdf_filename = text_filename.replace('.txt', '.pdf')
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
    if not os.path.exists(pdf_path):
        return jsonify({'status': 'error', 'message': '文件不存在'})
    # 如果PDF存在但文本文件不存在，则认为正在解析中
    return jsonify({'status': 'processing'})

@app.route('/get_result/<task_id>')
def get_result(task_id):
    if task_id not in results:
        return jsonify({'status': 'not_found'})
    
    return jsonify({
        'status': results[task_id]['status'],
        'content': ''.join(results[task_id]['content'])
    })

@app.route('/submit_task', methods=['POST'])
def submit_task():
    data = request.json
    api_key = data.get('api_key')
    prompt = data.get('prompt')
    file_contents = data.get('file_contents', {})
    
    if not api_key or not prompt:
        return jsonify({'error': 'API密钥和提示词不能为空'}), 400
    
    task_id = str(uuid.uuid4())
    task_queue.put((task_id, api_key, prompt, file_contents))
    
    return jsonify({'task_id': task_id})

@app.route('/generate_report', methods=['POST'])
def generate_report():
    data = request.json
    report_content = data.get('content', '')
    
    if not report_content:
        return jsonify({'error': '报告内容不能为空'}), 400
    
    # 确保我们有markdown库来转换内容
    try:
        import markdown
        has_markdown = True
    except ImportError:
        has_markdown = False
        app.logger.warning('未安装markdown库，无法将Markdown转换为HTML')
    
    # 如果内容是Markdown格式，转换为HTML
    if has_markdown and report_content.startswith('#'):
        html_content = markdown.markdown(report_content)
    else:
        html_content = report_content
    
    # 使用pdfkit生成PDF
    temp_html = tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8')
    temp_html.write('''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>专利审查报告</title>
    <style>
        body { font-family: SimSun, "Microsoft YaHei", serif; line-height: 1.6; padding: 20px; }
        h1, h2, h3 { color: #333; margin-top: 1.5em; }
        p { margin-bottom: 1em; }
        ul, ol { margin-left: 2em; margin-bottom: 1em; }
        pre { background-color: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }
        code { font-family: "Courier New", monospace; }
        .container { max-width: 800px; margin: 0 auto; }
    </style>
</head>
<body>
    <div class="container">''')
    temp_html.write(html_content)

    temp_html.write('''    </div>
</body>
</html>''')
    temp_html.close()
    
    report_filename = f'report_{time.strftime("%Y%m%d%H%M%S")}.pdf'
    report_path = os.path.join(REPORT_FOLDER, report_filename)
    
    try:
        # 配置pdfkit选项以确保良好的渲染效果
        options = {
            'page-size': 'A4',
            'margin-top': '20mm',
            'margin-right': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'encoding': "UTF-8",
            'no-outline': None,
            'quiet': ''
        }
        
        # 根据配置是否存在来决定是否传入configuration参数
        if config:
            pdfkit.from_file(temp_html.name, report_path, configuration=config, options=options)
        else:
            pdfkit.from_file(temp_html.name, report_path, options=options)
        
        os.unlink(temp_html.name)
        return jsonify({'report_url': f'/download_report/{report_filename}'})
    except Exception as e:
        app.logger.error(f'生成PDF失败: {str(e)}')
        return jsonify({'error': f'生成PDF失败: {str(e)}'}), 500

@app.route('/download_report/<report_filename>')
def download_report(report_filename):
    report_path = os.path.join(REPORT_FOLDER, report_filename)
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True)
    return jsonify({'error': '报告不存在'}), 404

if __name__ == '__main__':
    app.run(debug=True)