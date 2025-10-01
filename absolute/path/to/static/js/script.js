
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
