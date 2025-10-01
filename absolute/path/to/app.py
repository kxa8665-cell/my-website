
def parse_pdf(file_paths):
    results = []
    for file_path in file_paths:
        try:
            if not os.path.exists(file_path):
                error_msg = f'文件不存在: {file_path}'
                app.logger.error(error_msg)
                results.append((None, error_msg))
                continue
            if not os.path.isfile(file_path):
                error_msg = f'路径不是文件: {file_path}'
                app.logger.error(error_msg)
                results.append((None, error_msg))
                continue
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ''
                total_pages = len(reader.pages)
                app.logger.info(f'PDF文件 {os.path.basename(file_path)} 共有{total_pages}页')
                for page_num in range(total_pages):
                    page = reader.pages[page_num]
                    page_text = page.extract_text() or ''
                    text += page_text
                    app.logger.info(f'已解析 {os.path.basename(file_path)} 第{page_num + 1}页，获取{len(page_text)}个字符')
                app.logger.info(f'PDF文件 {os.path.basename(file_path)} 解析完成，共{len(text)}个字符')
                if not text.strip():
                    error_msg = f'PDF文件 {os.path.basename(file_path)} 解析成功，但未提取到任何文本内容'
                    app.logger.warning(error_msg)
                    results.append((None, error_msg))
                else:
                    results.append((text, None))
        except PyPDF2.errors.PdfReadError as e:
            error_msg = f'PDF文件 {os.path.basename(file_path)} 格式错误或损坏: {str(e)}'
            app.logger.error(f'{error_msg}，文件路径: {file_path}')
            results.append((None, error_msg))
        except PyPDF2.errors.PermissionError as e:
            error_msg = f'PDF文件 {os.path.basename(file_path)} 已加密，无法解析: {str(e)}'
            app.logger.error(f'{error_msg}，文件路径: {file_path}')
            results.append((None, error_msg))
        except Exception as e:
            error_msg = f'PDF文件 {os.path.basename(file_path)} 解析错误: {str(e)}'
            app.logger.error(f'{error_msg}，文件路径: {file_path}')
            app.logger.error(f'异常类型: {type(e).__name__}')
            results.append((None, error_msg))
    return results


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
    
    # 转换为HTML
    if has_markdown:
        # 使用更丰富的Markdown扩展
        md = markdown.Markdown(extensions=[
            'extra',          # 支持表格、代码块等扩展语法
            'toc',            # 生成目录
            'smarty',         # 替换引号、破折号等
            'wikilinks',      # 支持维基链接
            'mdx_math'        # 支持数学公式
        ])
        html_content = md.convert(report_content)
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
        body { font-family: SimSun, "Microsoft YaHei", serif; line-height: 1.8; padding: 20px; }
        h1, h2, h3, h4, h5, h6 { color: #2c3e50; margin-top: 1.5em; margin-bottom: 0.8em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
        h1 { font-size: 24px; }
        h2 { font-size: 20px; }
        h3 { font-size: 18px; }
        p { margin-bottom: 1.2em; text-align: justify; }
        ul, ol { margin-left: 2em; margin-bottom: 1.2em; }
        li { margin-bottom: 0.5em; }
        pre { background-color: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; margin-bottom: 1.2em; }
        code { font-family: "Courier New", monospace; font-size: 14px; }
        .container { max-width: 850px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #3498db; }
        .footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #7f8c8d; font-size: 14px; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 1.5em; }
        th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
        th { background-color: #f2f2f2; font-weight: bold; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        blockquote { border-left: 4px solid #3498db; padding-left: 15px; margin-left: 0; color: #7f8c8d; font-style: italic; }
    </style>
</head>
<body>
    <div class=
