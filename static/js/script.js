document.addEventListener('DOMContentLoaded', function() {
    // 预设提示词管理

    // 修改后
    let savedPrompts = JSON.parse(localStorage.getItem('customPrompts'));
    let prompts = savedPrompts && savedPrompts.length > 0 ? savedPrompts : [
        { id: 1, title: '第一部分', content: '第一部分预设提示内容' },
        { id: 2, title: '第二部分', content: '第二部分预设提示内容' },
        { id: 3, title: '第三部分', content: '第三部分预设提示内容' },
        { id: 4, title: '第四部分', content: '第四部分预设提示内容' },
        { id: 5, title: '第五部分', content: '第五部分预设提示内容' },
        { id: 6, title: '第六部分', content: '第六部分预设提示内容' },
        { id: 7, title: '第七部分', content: '第七部分预设提示内容' }
    ];

    // 保存提示词到本地存储
    function savePrompts() {
        localStorage.setItem('customPrompts', JSON.stringify(prompts));
        renderPromptButtons();
        renderPromptsTable();
    }

    // 渲染提示词按钮
    function renderPromptButtons() {
        const container = document.getElementById('prompt-buttons-container');
        container.innerHTML = '';

        prompts.forEach(prompt => {
            const button = document.createElement('button');
            button.className = 'prompt-btn';
            button.setAttribute('data-prompt', prompt.content);
            button.textContent = prompt.title;
            button.addEventListener('click', function() {
                document.getElementById('prompt-input').value = this.getAttribute('data-prompt');
            });
            container.appendChild(button);
        });

        // 添加"添加提示词"按钮
        const addButton = document.createElement('button');
        addButton.className = 'prompt-btn';
        addButton.textContent = '+ 添加';
        addButton.addEventListener('click', function() {
            document.getElementById('prompt-id').value = '';
            document.getElementById('prompt-title').value = '';
            document.getElementById('prompt-content').value = '';
            new bootstrap.Modal(document.getElementById('promptManagerModal')).show();
        });
        container.appendChild(addButton);
    }

    // 渲染提示词表格
    function renderPromptsTable() {
        const tableBody = document.getElementById('prompts-table-body');
        tableBody.innerHTML = '';

        prompts.forEach(prompt => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${prompt.title}</td>
                <td>
                    <button class="btn btn-sm btn-primary edit-prompt" data-id="${prompt.id}">编辑</button>
                    <button class="btn btn-sm btn-danger delete-prompt" data-id="${prompt.id}">删除</button>
                </td>
            `;
            tableBody.appendChild(row);
        });

        // 绑定编辑和删除事件
        document.querySelectorAll('.edit-prompt').forEach(btn => {
            btn.addEventListener('click', function() {
                const id = parseInt(this.getAttribute('data-id'));
                const prompt = prompts.find(p => p.id === id);
                if (prompt) {
                    document.getElementById('prompt-id').value = prompt.id;
                    document.getElementById('prompt-title').value = prompt.title;
                    document.getElementById('prompt-content').value = prompt.content;
                    new bootstrap.Modal(document.getElementById('promptManagerModal')).show();
                }
            });
        });

        document.querySelectorAll('.delete-prompt').forEach(btn => {
            btn.addEventListener('click', function() {
                const id = parseInt(this.getAttribute('data-id'));
                if (confirm('确定要删除这个提示词吗？')) {
                    prompts = prompts.filter(p => p.id !== id);
                    savePrompts();
                }
            });
        });
    }

    // 绑定保存提示词按钮事件
    document.getElementById('save-prompt-btn').addEventListener('click', function() {
        const id = document.getElementById('prompt-id').value;
        const title = document.getElementById('prompt-title').value.trim();
        const content = document.getElementById('prompt-content').value.trim();

        if (!title || !content) {
            alert('提示词标题和内容不能为空');
            return;
        }

        if (id) {
            // 编辑现有提示词
            const index = prompts.findIndex(p => p.id === parseInt(id));
            if (index !== -1) {
                prompts[index] = { ...prompts[index], title, content };
            }
        } else {
            // 添加新提示词
            const newId = prompts.length > 0 ? Math.max(...prompts.map(p => p.id)) + 1 : 1;
            prompts.push({ id: newId, title, content });
        }

        savePrompts();
        new bootstrap.Modal(document.getElementById('promptManagerModal')).hide();
    });

    // DOM元素引用
    const promptButtons = document.querySelectorAll('.prompt-btn');
    const promptInput = document.getElementById('prompt-input');
    const executeBtn = document.getElementById('execute-btn');
    const uploadBtn = document.getElementById('upload-btn');
    const fileUpload = document.getElementById('file-upload');
    const uploadedFiles = document.getElementById('uploaded-files');
    const resultsContainer = document.getElementById('results-container');
    const apiSettings = document.getElementById('api-settings');
    const settingsToggle = document.getElementById('settings-toggle');
    const settingsContent = document.getElementById('settings-content');
    const apiKeyInput = document.getElementById('api-key');
    const saveApiSettingsBtn = document.getElementById('save-api-settings');
    const generateReportBtn = document.getElementById('generate-report-btn');
    const reportPreview = document.getElementById('report-preview');
    const formatTabs = document.querySelectorAll('.format-tab');
    const inferenceBtn = document.getElementById('inference-btn');
    const networkBtn = document.getElementById('network-btn');

    // 全局变量
    let uploadedFileList = []; // 存储上传的文件信息
    let currentFormat = 'text'; // 默认格式

    // 从localStorage加载API密钥
    const savedApiKey = localStorage.getItem('deepseekApiKey');
    if (savedApiKey) {
        apiKeyInput.value = savedApiKey;
    }

    // 切换API设置面板
    settingsToggle.addEventListener('click', function() {
        const isVisible = settingsContent.style.display !== 'none';
        settingsContent.style.display = isVisible ? 'none' : 'block';
        settingsToggle.querySelector('i').classList.toggle('fa-chevron-down', isVisible);
        settingsToggle.querySelector('i').classList.toggle('fa-chevron-up', !isVisible);
    });

    // 保存API设置
    saveApiSettingsBtn.addEventListener('click', function() {
        const apiKey = apiKeyInput.value.trim();
        if (apiKey) {
            localStorage.setItem('deepseekApiKey', apiKey);
            alert('API密钥已保存');
        } else {
            alert('请输入API密钥');
        }
    });

    // 选择预设提示词
    promptButtons.forEach(button => {
        button.addEventListener('click', function() {
            const promptText = this.getAttribute('data-prompt');
            if (promptText === '+ 添加') {
                const newPrompt = prompt('请输入新的提示词:');
                if (newPrompt && newPrompt.trim()) {
                    const newButton = document.createElement('button');
                    newButton.className = 'prompt-btn';
                    newButton.setAttribute('data-prompt', newPrompt.trim());
                    newButton.textContent = newPrompt.trim().substring(0, 15) + '...';
                    newButton.addEventListener('click', function() {
                        promptInput.value = this.getAttribute('data-prompt');
                    });
                    this.parentNode.insertBefore(newButton, this);
                }
            } else {
                promptInput.value = promptText;
            }
        });
    });

    // 文件上传按钮点击
    uploadBtn.addEventListener('click', function() {
        fileUpload.click();
    });

    // 文件选择处理
    fileUpload.addEventListener('change', function(e) {
        console.log('文件选择变化，文件数量:', e.target.files.length);
        const files = e.target.files;
        if (files.length > 0) {
            uploadFiles(files);
            this.value = ''; // 重置以允许重新选择相同文件
        }
    });

    // 上传文件到服务器
    function uploadFiles(files) {
        console.log('开始上传文件，数量:', files.length);
        
        const formData = new FormData();
        const fileArray = Array.from(files);
        const tempFileObjs = [];
        
        // 添加所有文件到FormData并创建临时列表项
        fileArray.forEach(file => {
            formData.append('file', file);
            const tempFileObj = {original_name: file.name, text_filename: 'temp_' + Date.now() + '_' + file.name.replace(/\.pdf$/i, '.txt')};
            tempFileObjs.push(tempFileObj);
            addFileToUploadedList(tempFileObj);
        });
        
        // 获取所有临时文件项
        const fileItems = tempFileObjs.map(obj => 
            document.querySelector(`.file-item[data-text-filename="${obj.text_filename}"]`)
        );
        
        // 设置所有文件状态为上传中
        fileItems.forEach(item => {
            const statusElement = item.querySelector('.file-status');
            statusElement.innerHTML = '<i class="fa fa-upload"></i> 等待上传';
        });
        
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/upload', true);
        
        // 总体进度处理
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                fileItems.forEach(item => {
                    const progressFill = item.querySelector('.progress-fill');
                    const statusElement = item.querySelector('.file-status');
                    progressFill.style.width = `${percent}%`;
                    statusElement.innerHTML = `<i class="fa fa-upload"></i> 上传中: ${Math.round(percent)}%`;
                });
            }
        });
        
        xhr.addEventListener('load', function() {
            console.log('上传请求完成，状态码:', xhr.status);
            console.log('响应内容:', xhr.responseText);
            
            if (xhr.status === 200) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    console.log('解析后的响应:', response);
                    
                    if (response.error) {
                        // 显示全局错误
                        fileItems.forEach(item => {
                            const statusElement = item.querySelector('.file-status');
                            statusElement.innerHTML = `<i class="fa fa-exclamation-circle"></i> 上传失败: ${response.error}`;
                            statusElement.style.color = '#c62828';
                        });
                    } else if (response.files && response.files.length > 0) {
                        // 清除现有上传文件列表
                        uploadedFileList = [];
                        
                        // 更新每个文件状态
                        response.files.forEach((uploadedFile, index) => {
                            const fileItem = fileItems[index];
                            if (fileItem) {
                                // 更新文件项的data属性
                                fileItem.setAttribute('data-text-filename', uploadedFile.text_filename);
                                const removeBtn = fileItem.querySelector('.file-remove');
                                if (removeBtn) removeBtn.setAttribute('data-text-filename', uploadedFile.text_filename);
                                
                                // 添加到上传文件列表
                                uploadedFileList.push(uploadedFile);
                                
                                // 更新状态
                                const statusElement = fileItem.querySelector('.file-status');
                                const progressFill = fileItem.querySelector('.progress-fill');
                                
                                if (uploadedFile.error) {
                                    // 直接显示后端返回的详细错误信息
                                    statusElement.innerHTML = `<i class="fa fa-exclamation-circle"></i> 处理失败: ${uploadedFile.error}`;
                                    statusElement.style.color = '#c62828';
                                    console.log('文件处理错误详情:', uploadedFile.error); // 添加调试日志
                                } else {
                                    statusElement.innerHTML = '<i class="fa fa-check"></i> 已上传';
                                    statusElement.style.color = '#2e7d32';
                                }

                                progressFill.style.width = '100%';
                            }
                        });
                    } else {
                        // 服务器返回空文件列表
                        fileItems.forEach(item => {
                            const statusElement = item.querySelector('.file-status');
                            statusElement.innerHTML = '<i class="fa fa-exclamation-circle"></i> 上传失败: 未返回文件信息';
                            statusElement.style.color = '#c62828';
                        });
                    }
                } catch (e) {
                    console.error('解析响应失败:', e);
                    fileItems.forEach(item => {
                        const statusElement = item.querySelector('.file-status');
                        statusElement.innerHTML = '<i class="fa fa-exclamation-circle"></i> 响应解析失败';
                        statusElement.style.color = '#c62828';
                    });
                }
            } else {
                fileItems.forEach(item => {
                    const statusElement = item.querySelector('.file-status');
                    statusElement.innerHTML = `<i class="fa fa-exclamation-circle"></i> 上传失败: HTTP ${xhr.status}`;
                    statusElement.style.color = '#c62828';
                });
            }
        });

        
        xhr.addEventListener('error', function() {
            console.error('上传发生错误');
            fileItems.forEach(item => {
                const statusElement = item.querySelector('.file-status');
                statusElement.innerHTML = '<i class="fa fa-exclamation-circle"></i> 网络错误';
                statusElement.style.color = '#c62828';
            });
        });
        
        xhr.send(formData);
    }

    // 添加文件到上传列表
    function addFileToUploadedList(file) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.setAttribute('data-text-filename', file.text_filename);
        fileItem.innerHTML = `
            <span title="${file.original_name}">${truncateText(file.original_name, 20)}</span>
            <span class="file-status"><i class="fa fa-upload"></i> 等待上传</span>
            <span class="file-remove" data-text-filename="${file.text_filename}"><i class="fa fa-times"></i></span>
            <div class="progress-bar"><div class="progress-fill" style="width: 0%"></div></div>
        `;
        uploadedFiles.appendChild(fileItem);
    
        // 删除文件事件
        fileItem.querySelector('.file-remove').addEventListener('click', function() {
            const textFilename = this.getAttribute('data-text-filename');
            uploadedFileList = uploadedFileList.filter(f => f.text_filename !== textFilename);
            fileItem.remove();
        });
    }

    // 截断文本辅助函数
    function truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    // 更新报告预览
    function updateReportPreview() {
        const resultCards = Array.from(document.querySelectorAll('.result-card'));
        let content = '';

        resultCards.forEach(card => {
            const cardContent = card.querySelector('.result-content').innerHTML;
            content += `${cardContent}\n\n`;
        });

        if (currentFormat === 'markdown') {
            reportPreview.textContent = content;
        } else if (currentFormat === 'html') {
            reportPreview.innerHTML = marked.parse(content);
        } else {
            // 纯文本格式
            reportPreview.textContent = marked.parse(content).replace(/<[^>]*>?/gm, '');
        }
    }

    // 创建结果卡片
    function createResultCard(taskId, title) {
        const card = document.createElement('div');
        card.className = 'result-card';
        card.setAttribute('data-task-id', taskId);
        card.innerHTML = `
            <div class="result-header">
                <div class="result-title">${truncateText(title, 50)}</div>
                <div class="result-status">处理中</div>
            </div>
            <div class="result-content"><div class="loading-indicator"></div> 等待结果...</div>
        `;
        return card;
    }

    // 轮询获取结果
    function pollResult(taskId, resultCard) {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/get_result/${taskId}`);
                const data = await response.json();

                if (data.status === 'completed') {
                    clearInterval(pollInterval);
                    updateResultContent(resultCard, data.content);
                    updateResultStatus(resultCard, 'completed');
                    updateReportPreview();
                } else if (data.status === 'error') {
                    clearInterval(pollInterval);
                    updateResultContent(resultCard, data.content);
                    updateResultStatus(resultCard, 'error');
                } else if (data.status === 'processing') {
                    updateResultContent(resultCard, data.content);
                } else if (data.status === 'not_found') {
                    clearInterval(pollInterval);
                    updateResultContent(resultCard, '任务未找到');
                    updateResultStatus(resultCard, 'error');
                }
            } catch (error) {
                clearInterval(pollInterval);
                updateResultContent(resultCard, `获取结果失败: ${error.message}`);
                updateResultStatus(resultCard, 'error');
            }
        }, 1000);
    }

    // 更新结果内容
    function updateResultContent(resultCard, content) {
        const contentElement = resultCard.querySelector('.result-content');
        if (currentFormat === 'html') {
            contentElement.innerHTML = marked.parse(content);
        } else {
            contentElement.textContent = content;
        }
    }

    // 更新结果状态
    function updateResultStatus(resultCard, status) {
        const statusElement = resultCard.querySelector('.result-status');
        statusElement.textContent = {
            'processing': '处理中',
            'completed': '已完成',
            'error': '错误'
        }[status] || status;

        // 更新状态颜色
        statusElement.style.backgroundColor = {
            'processing': '#e3f2fd',
            'completed': '#e8f5e9',
            'error': '#ffebee'
        }[status] || '#e3f2fd';

        statusElement.style.color = {
            'processing': '#1976d2',
            'completed': '#2e7d32',
            'error': '#c62828'
        }[status] || '#1976d2';
    }

    // 假设 generateUUID 函数已定义
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    // 渲染提示词按钮
    renderPromptButtons();
    // 渲染提示词表格
    renderPromptsTable();

    // 执行按钮点击事件
    executeBtn.addEventListener('click', async () => {
        const apiKey = apiKeyInput.value.trim();
        const prompt = promptInput.value.trim();

        if (!apiKey || !prompt) {
            alert('请输入API密钥和提示词');
            return;
        }

        const fileContents = {};
        for (const file of uploadedFileList) {
            if (file.text_filename) {
                try {
                    const response = await fetch(`/get_parsed_text/${file.text_filename}`);
                    const data = await response.json();
                    if (data.content) {
                        fileContents[file.original_name] = data.content;
                    }
                } catch (error) {
                    console.error(`获取文件内容失败: ${file.original_name}`, error);
                }
            }
        }

        const taskId = generateUUID();
        const resultCard = createResultCard(taskId, prompt);
        resultsContainer.appendChild(resultCard);

        try {
            const response = await fetch('/submit_task', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    api_key: apiKey,
                    prompt: prompt,
                    file_contents: fileContents
                })
            });

            const data = await response.json();
            if (data.task_id) {
                pollResult(data.task_id, resultCard);
            } else {
                updateResultContent(resultCard, `提交任务失败: ${data.error}`);
                updateResultStatus(resultCard, 'error');
            }
        } catch (error) {
            updateResultContent(resultCard, `提交任务失败: ${error.message}`);
            updateResultStatus(resultCard, 'error');
        }
    });

    // 生成报告按钮点击事件
    generateReportBtn.addEventListener('click', async () => {
        const resultCards = Array.from(document.querySelectorAll('.result-card'));
        let reportContent = '';

        resultCards.forEach(card => {
            const cardContent = card.querySelector('.result-content').innerHTML;
            reportContent += `${cardContent}\n\n`;
        });

        try {
            const response = await fetch('/generate_report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: reportContent
                })
            });

            const data = await response.json();
            if (data.report_url) {
                window.open(data.report_url, '_blank');
            } else {
                alert(`生成报告失败: ${data.error}`);
            }
        } catch (error) {
            alert(`生成报告失败: ${error.message}`);
        }
    });

    // 格式切换标签点击事件
    formatTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            formatTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentFormat = tab.getAttribute('data-format');
            updateReportPreview();
        });
    });
});