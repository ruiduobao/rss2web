document.addEventListener('DOMContentLoaded', function() {
    // 初始化瀑布流布局（如果在主页）
    var grid = document.querySelector('.grid');
    if (grid) {
        var masonry = new Masonry(grid, {
            itemSelector: '.grid-item',
            columnWidth: '.grid-item',
            percentPosition: true
        });

        // 图片加载完成后重新布局
        if (typeof imagesLoaded !== 'undefined') {
            imagesLoaded(grid).on('progress', function() {
                masonry.layout();
            });
        }
    }

    // 语言切换功能
    const langToggle = document.getElementById('langToggle');
    if (langToggle) {
        const langText = langToggle.querySelector('.lang-text');
        let isEnglish = localStorage.getItem('language') === 'en' || true;
        
        // 初始化语言状态
        updateLanguageDisplay(isEnglish);
        
        langToggle.addEventListener('click', function() {
            isEnglish = !isEnglish;
            updateLanguageDisplay(isEnglish);
            localStorage.setItem('language', isEnglish ? 'en' : 'zh');
        });
    }
    
    function updateLanguageDisplay(showEnglish) {
        // 更新按钮文本
        const langText = document.querySelector('.lang-text');
        if (langText) {
            langText.textContent = showEnglish ? 'ZH' : 'EN';
        }
        
        // 更新所有文章的标题和摘要
        document.querySelectorAll('.title-en, .title-zh, .summary-en, .summary-zh').forEach(el => {
            if (el.classList.contains('title-en') || el.classList.contains('summary-en')) {
                el.style.display = showEnglish ? 'block' : 'none';
            } else {
                el.style.display = showEnglish ? 'none' : 'block';
            }
        });

        // 在中文模式下隐藏没有中文翻译的文章（仅在主页）
        if (grid) {
            document.querySelectorAll('.grid-item').forEach(item => {
                const titleZh = item.querySelector('.title-zh');
                const titleEn = item.querySelector('.title-en');
                const hasChinese = titleZh && titleEn && 
                                 titleZh.textContent.trim() !== titleEn.textContent.trim();
                item.style.display = (!showEnglish && !hasChinese) ? 'none' : 'block';
            });
            
            // 重新布局瀑布流
            if (typeof masonry !== 'undefined') {
                setTimeout(() => masonry.layout(), 300);
            }
        }
    }
}); 