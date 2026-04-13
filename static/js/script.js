let currentChatId = null;
let isTyping = false;
let contextMenuChat = null;
let sidebarHidden = false;
let previewActive = false;

// Инициализация темы из localStorage
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        document.getElementById('themeIcon').textContent = '🌙';
        const emptyThemeIcon = document.getElementById('emptyThemeIcon');
        if (emptyThemeIcon) emptyThemeIcon.textContent = '🌙';
    }
}

// Переключение темы
function toggleTheme() {
    const body = document.body;
    const themeIcon = document.getElementById('themeIcon');
    const emptyThemeIcon = document.getElementById('emptyThemeIcon');

    if (body.classList.contains('light-theme')) {
        body.classList.remove('light-theme');
        themeIcon.textContent = '☀️';
        if (emptyThemeIcon) emptyThemeIcon.textContent = '☀️';
        localStorage.setItem('theme', 'dark');
    } else {
        body.classList.add('light-theme');
        themeIcon.textContent = '🌙';
        if (emptyThemeIcon) emptyThemeIcon.textContent = '🌙';
        localStorage.setItem('theme', 'light');
    }
}

// Переключение боковой панели
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebarHidden = !sidebarHidden;

    if (sidebarHidden) {
        sidebar.classList.add('hidden');
        localStorage.setItem('sidebarHidden', 'true');
    } else {
        sidebar.classList.remove('hidden');
        localStorage.setItem('sidebarHidden', 'false');
    }
}

// Переключение preview панели
function togglePreview() {
    const previewPanel = document.getElementById('previewPanel');
    const container = document.querySelector('.container');

    previewActive = !previewActive;

    if (previewActive) {
        previewPanel.classList.add('active');
        container.classList.add('preview-active');
        updatePreview();
    } else {
        previewPanel.classList.remove('active');
        container.classList.remove('preview-active');
    }

    // Предотвращаем повторное открытие
    event.stopPropagation();
}

// Обновление preview с кодом из чата
function updatePreview() {
    const messages = document.querySelectorAll('.message.ai');
    let htmlCode = '';
    let cssCode = '';
    let jsCode = '';

    messages.forEach(msg => {
        // Ищем в pre > code блоках
        const codeBlocks = msg.querySelectorAll('pre code');

        codeBlocks.forEach(block => {
            const language = block.className.match(/language-(\w+)/)?.[1] || '';
            const code = block.textContent;

            if (language === 'html') {
                htmlCode += code + '\n';
            } else if (language === 'css') {
                cssCode += code + '\n';
            } else if (language === 'javascript' || language === 'js') {
                jsCode += code + '\n';
            }
        });
    });

    // Если HTML код не найден, показываем сообщение
    if (!htmlCode.trim()) {
        const iframe = document.getElementById('previewFrame');
        iframe.srcdoc = '<html><body style="display:flex;align-items:center;justify-content:center;height:100vh;font-family:sans-serif;color:#666;">Нет HTML кода для отображения</body></html>';
        return;
    }

    // Создаем полный HTML документ
    const fullHTML = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>${cssCode}</style>
</head>
<body>
    ${htmlCode}
    <script>${jsCode}<\/script>
</body>
</html>`;

    const iframe = document.getElementById('previewFrame');
    iframe.srcdoc = fullHTML;
}

// Автоматическое изменение высоты textarea
const messageInput = document.getElementById('messageInput');
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

// Отслеживание прокрутки для кнопки "Вниз"
const chatContainer = document.getElementById('chatContainer');
const scrollToBottomBtn = document.getElementById('scrollToBottom');

chatContainer.addEventListener('scroll', function() {
    const isScrolledUp = chatContainer.scrollHeight - chatContainer.scrollTop - chatContainer.clientHeight > 100;

    if (isScrolledUp) {
        scrollToBottomBtn.classList.add('visible');
    } else {
        scrollToBottomBtn.classList.remove('visible');
    }
});

// Функция прокрутки вниз
function scrollToBottom() {
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth'
    });
}

// Загрузка чатов при старте
window.addEventListener('load', async () => {
    initTheme(); // Инициализируем тему
    await loadAnnouncement(); // Загружаем объявление
    await loadUserProfile(); // Загружаем профиль пользователя
    await loadChats();
    updateEmptyState();

    // Автоматически скрываем панель если нет чатов
    const response = await fetch('/api/chats');
    const data = await response.json();

    if (!data.chats || data.chats.length === 0) {
        const sidebar = document.querySelector('.sidebar');
        sidebar.classList.add('hidden');
        sidebarHidden = true;
    } else {
        // Восстанавливаем состояние панели из localStorage
        const savedSidebarState = localStorage.getItem('sidebarHidden');
        if (savedSidebarState === 'true') {
            const sidebar = document.querySelector('.sidebar');
            sidebar.classList.add('hidden');
            sidebarHidden = true;
        }
    }

    // Прокручиваем вниз при загрузке страницы
    const chatContainer = document.getElementById('chatContainer');
    setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 100);

    document.getElementById('messageInput').focus();
});

// Загрузка профиля пользователя
async function loadUserProfile() {
    try {
        const response = await fetch('/api/user/profile');
        const data = await response.json();

        if (response.ok) {
            document.getElementById('userNickname').textContent = data.nickname;
            document.getElementById('userEmail').textContent = data.email;

            // Устанавливаем аватар если есть
            if (data.avatar) {
                const avatarDiv = document.getElementById('userAvatar');
                avatarDiv.innerHTML = `<img src="data:image/jpeg;base64,${data.avatar}" alt="Avatar">`;
            }
        }
    } catch (error) {
        console.error('Ошибка загрузки профиля:', error);
    }
}

// Загрузка объявления
async function loadAnnouncement() {
    try {
        const response = await fetch('/api/announcement');
        const data = await response.json();

        if (response.ok && data.text) {
            const banner = document.getElementById('announcementBanner');
            const text = document.getElementById('announcementText');

            text.textContent = data.text;
            banner.style.backgroundColor = data.color;
            banner.style.display = 'block';
        }
    } catch (error) {
        console.error('Ошибка загрузки объявления:', error);
    }
}

// Открыть модальное окно профиля
function openProfileModal() {
    const modal = document.getElementById('profileModal');
    modal.classList.add('active');

    // Загружаем текущие данные
    const nickname = document.getElementById('userNickname').textContent;
    document.getElementById('modalNicknameInput').value = nickname;

    // Копируем аватар
    const currentAvatar = document.getElementById('userAvatar').innerHTML;
    document.getElementById('modalAvatarPreview').innerHTML = currentAvatar;
}

// Закрыть модальное окно профиля
function closeProfileModal(event) {
    const modal = document.getElementById('profileModal');
    modal.classList.remove('active');
}

// Предпросмотр аватара в модальном окне
function previewModalAvatar(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
        alert('Файл слишком большой. Максимум 5MB');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('modalAvatarPreview');
        preview.innerHTML = `<img src="${e.target.result}" alt="Avatar">`;
    };
    reader.readAsDataURL(file);
}

// Обновить профиль
async function updateProfile(event) {
    event.preventDefault();

    const nickname = document.getElementById('modalNicknameInput').value.trim();
    const avatarInput = document.getElementById('modalAvatarInput');

    if (!nickname) {
        alert('Введи ник');
        return;
    }

    const formData = new FormData();
    formData.append('nickname', nickname);

    if (avatarInput.files[0]) {
        formData.append('avatar', avatarInput.files[0]);
    }

    try {
        const response = await fetch('/api/user/update', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            // Обновляем UI
            await loadUserProfile();
            closeProfileModal();
            showNotification('Профиль обновлён');
        } else {
            alert(data.error || 'Ошибка обновления');
        }
    } catch (error) {
        alert('Ошибка соединения');
    }
}

// Выход из аккаунта
async function logout() {
    if (!confirm('Выйти из аккаунта?')) return;

    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST'
        });

        if (response.ok) {
            window.location.href = '/register';
        }
    } catch (error) {
        alert('Ошибка выхода');
    }
}

// Обновление состояния пустого экрана
function updateEmptyState() {
    const mainContent = document.querySelector('.main-content');
    const emptyStateWrapper = document.querySelector('.empty-state-wrapper');
    const inputArea = document.querySelector('.input-area');
    const chatContainer = document.getElementById('chatContainer');

    if (!currentChatId || (chatContainer && chatContainer.children.length === 0)) {
        mainContent.classList.add('empty');

        // Перемещаем input-area внутрь empty-state-wrapper
        if (emptyStateWrapper && inputArea && inputArea.parentElement !== emptyStateWrapper) {
            emptyStateWrapper.appendChild(inputArea);
        }
    } else {
        mainContent.classList.remove('empty');

        // Возвращаем input-area на место
        if (inputArea && inputArea.parentElement === emptyStateWrapper) {
            mainContent.appendChild(inputArea);
        }
    }
}

// Загрузка списка чатов
async function loadChats() {
    try {
        const response = await fetch('/api/chats');
        const data = await response.json();

        const chatsList = document.getElementById('chatsList');
        chatsList.innerHTML = '';

        if (data.chats && data.chats.length > 0) {
            data.chats.forEach(chat => {
                const btn = document.createElement('button');
                btn.className = 'mode-btn chat-item';
                btn.dataset.chatId = chat.id;

                if (chat.id === data.active_chat) {
                    btn.classList.add('active');
                    currentChatId = chat.id;
                }

                const title = document.createElement('span');
                title.className = 'chat-item-title';
                title.textContent = chat.title;

                const actions = document.createElement('div');
                actions.className = 'chat-item-actions';

                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'chat-action-btn delete';
                deleteBtn.innerHTML = '×';
                deleteBtn.onclick = (e) => {
                    e.stopPropagation();
                    deleteChat(chat.id);
                };

                actions.appendChild(deleteBtn);

                btn.appendChild(title);
                btn.appendChild(actions);

                btn.onclick = () => loadChat(chat.id);

                // Контекстное меню для переименования
                btn.oncontextmenu = (e) => {
                    e.preventDefault();
                    renameChat(chat.id, chat.title);
                };

                chatsList.appendChild(btn);
            });

            // Загружаем активный чат
            if (data.active_chat) {
                await loadChat(data.active_chat);
            }
        } else {
            chatsList.innerHTML = '<p style="color: var(--text-tertiary); font-size: 13px; padding: 10px 12px;">Нет чатов</p>';
            currentChatId = null;
        }

        updateEmptyState();
    } catch (error) {
        console.error('Ошибка загрузки чатов:', error);
    }
}

// Очистить все чаты
async function clearAllChats() {
    if (!confirm('Удалить все чаты? Это действие нельзя отменить.')) return;

    try {
        const response = await fetch('/api/chats');
        const data = await response.json();

        if (data.chats && data.chats.length > 0) {
            // Удаляем все чаты
            for (const chat of data.chats) {
                await fetch(`/api/chat/${chat.id}`, { method: 'DELETE' });
            }

            currentChatId = null;
            await loadChats();
            updateEmptyState();
            showNotification('Все чаты удалены');
        }
    } catch (error) {
        console.error('Ошибка очистки чатов:', error);
        showNotification('Ошибка при удалении чатов');
    }
}

// Экспорт чатов
async function exportChats() {
    try {
        const response = await fetch('/api/chats');
        const data = await response.json();

        if (!data.chats || data.chats.length === 0) {
            showNotification('Нет чатов для экспорта');
            return;
        }

        // Получаем все чаты с сообщениями
        const allChats = [];
        for (const chat of data.chats) {
            const chatResponse = await fetch(`/api/chat/${chat.id}`);
            const chatData = await chatResponse.json();
            allChats.push({
                title: chatData.title,
                messages: chatData.messages,
                created: chat.created
            });
        }

        // Создаем JSON файл
        const exportData = {
            exported: new Date().toISOString(),
            chats: allChats
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `heartai-chats-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showNotification('Чаты экспортированы');
    } catch (error) {
        console.error('Ошибка экспорта:', error);
        showNotification('Ошибка при экспорте');
    }
}

// Загрузка конкретного чата
async function loadChat(chatId) {
    try {
        const response = await fetch(`/api/chat/${chatId}`);
        const data = await response.json();

        if (response.ok) {
            currentChatId = chatId;

            // Обновляем активную кнопку
            document.querySelectorAll('.chat-item').forEach(btn => {
                btn.classList.remove('active');
            });
            document.querySelector(`[data-chat-id="${chatId}"]`)?.classList.add('active');

            // Обновляем заголовок
            document.getElementById('mode-title').textContent = data.title;

            // Очищаем контейнер
            const chatContainer = document.getElementById('chatContainer');
            chatContainer.innerHTML = '';

            // Добавляем сообщения
            data.messages.forEach(msg => {
                addMessage(msg.content, msg.role === 'user' ? 'user' : 'ai', false);
            });

            updateEmptyState();

            // Прокручиваем вниз после загрузки
            setTimeout(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }, 100);
        }
    } catch (error) {
        console.error('Ошибка загрузки чата:', error);
    }
}

// Создание нового чата
async function createNewChat() {
    try {
        const response = await fetch('/api/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok) {
            currentChatId = data.chat_id;

            // Очищаем контейнер
            const chatContainer = document.getElementById('chatContainer');
            chatContainer.innerHTML = '';

            // Обновляем заголовок
            document.getElementById('mode-title').textContent = 'Новый чат';

            // Перезагружаем список чатов
            await loadChats();
            updateEmptyState();

            // Фокус на input
            document.getElementById('messageInput').focus();

            showNotification('Создан новый чат');
        }
    } catch (error) {
        console.error('Ошибка создания чата:', error);
    }
}

// Переименование чата
async function renameChat(chatId, currentTitle) {
    const newTitle = prompt('Новое название чата:', currentTitle);

    if (newTitle && newTitle.trim() && newTitle !== currentTitle) {
        try {
            const response = await fetch(`/api/chat/${chatId}/rename`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title: newTitle.trim() })
            });

            if (response.ok) {
                await loadChats();
                showNotification('Чат переименован');
            }
        } catch (error) {
            console.error('Ошибка переименования чата:', error);
        }
    }
}

// Удаление чата
async function deleteChat(chatId) {
    try {
        const response = await fetch(`/api/chat/${chatId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            // Если удаляем активный чат
            if (chatId === currentChatId) {
                currentChatId = null;
            }

            await loadChats();
            updateEmptyState();
            showNotification('Чат удален');
        }
    } catch (error) {
        console.error('Ошибка удаления чата:', error);
    }
}

// Обработка нажатия клавиш
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage(event);
    }
}

// Отправка сообщения
async function sendMessage(event) {
    event.preventDefault();

    if (isTyping) return;

    const input = document.getElementById('messageInput');
    const message = input.value.trim();

    if (!message) return;

    // Очищаем input
    input.value = '';
    input.style.height = 'auto';

    // Удаляем welcome message если есть
    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // СРАЗУ убираем пустой экран и показываем чат
    const mainContent = document.querySelector('.main-content');
    mainContent.classList.remove('empty');

    // Возвращаем input-area на место если был пустой экран
    const inputArea = document.querySelector('.input-area');
    const emptyStateWrapper = document.querySelector('.empty-state-wrapper');
    if (inputArea && inputArea.parentElement === emptyStateWrapper) {
        mainContent.appendChild(inputArea);
    }

    // Добавляем сообщение пользователя
    addMessage(message, 'user', true, false);

    // Показываем индикатор печати
    const typingId = showTypingIndicator();
    isTyping = true;

    // Блокируем кнопку отправки
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                chat_id: currentChatId
            })
        });

        const data = await response.json();

        // Удаляем индикатор печати
        removeTypingIndicator(typingId);

        if (response.ok) {
            // Обновляем текущий chat_id
            if (data.chat_id) {
                currentChatId = data.chat_id;
            }

            // Добавляем ответ AI с анимацией - БЕЗ loadChats
            const chatContainer = document.getElementById('chatContainer');

            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ai';

            const content = document.createElement('div');
            content.className = 'message-content';

            const messageText = document.createElement('div');

            content.appendChild(messageText);
            messageDiv.appendChild(content);
            chatContainer.appendChild(messageDiv);

            // ПРОСТАЯ АНИМАЦИЯ
            let i = 0;
            const txt = data.response;
            const speed = 20;

            function typeWriter() {
                if (i < txt.length) {
                    messageText.textContent += txt.charAt(i);
                    i++;
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                    setTimeout(typeWriter, speed);
                } else {
                    // После завершения анимации применяем подсветку кода
                    highlightCode(messageText);
                }
            }

            typeWriter();

        } else {
            // Показываем ошибку
            addMessage(`Ошибка: ${data.error}`, 'ai', true, false);
        }

    } catch (error) {
        removeTypingIndicator(typingId);
        addMessage(`Ошибка соединения: ${error.message}`, 'ai', true, false);
    } finally {
        isTyping = false;
        sendBtn.disabled = false;
        input.focus();
    }
}

// Добавление сообщения в чат
function addMessage(text, type, scroll = true, animate = false) {
    console.log('addMessage called:', { type, animate, textLength: text.length });

    const chatContainer = document.getElementById('chatContainer');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;

    const content = document.createElement('div');
    content.className = 'message-content';

    const messageText = document.createElement('div');

    content.appendChild(messageText);
    messageDiv.appendChild(content);
    chatContainer.appendChild(messageDiv);

    // Анимация печати для AI
    if (type === 'ai' && animate === true) {
        console.log('TYPEWRITER STARTED');
        let currentIndex = 0;
        const speed = 30;

        function type() {
            if (currentIndex < text.length) {
                messageText.textContent = text.slice(0, currentIndex + 1);
                currentIndex++;

                if (scroll) {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }

                setTimeout(type, speed);
            } else {
                console.log('TYPEWRITER FINISHED');
                // Применяем подсветку кода после завершения анимации
                highlightCode(messageText);
            }
        }

        type();
    } else {
        console.log('NO ANIMATION - showing text immediately');
        messageText.textContent = text;

        // Применяем подсветку кода
        highlightCode(messageText);

        if (scroll) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
}

// Подсветка кода в сообщении
function highlightCode(element) {
    const text = element.textContent;

    // Ищем блоки кода ```язык\nкод```
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;

    if (codeBlockRegex.test(text)) {
        let html = text;

        html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            const language = lang || 'plaintext';
            const highlighted = hljs.highlight(code.trim(), { language }).value;
            const codeId = 'code-' + Math.random().toString(36).substr(2, 9);

            // Кнопки для всех блоков кода
            let buttons = `
                <div class="code-actions">
                    <button class="code-btn copy-btn" onclick="copyCode('${codeId}')" title="Копировать">
                        <span>Копировать</span>
                    </button>
                    <button class="code-btn download-btn" onclick="downloadCode('${codeId}', '${language}')" title="Скачать">
                        <span>Скачать</span>
                    </button>`;

            // Добавляем кнопку "Просмотр" только для HTML блоков
            if (language.toLowerCase() === 'html') {
                buttons += `
                    <button class="code-btn preview-btn" onclick="togglePreview()" title="Просмотр">
                        <span>Просмотр</span>
                    </button>`;
            }

            buttons += '</div>';

            return `<div class="code-block-wrapper">${buttons}<pre><code id="${codeId}" class="hljs language-${language}">${highlighted}</code></pre></div>`;
        });

        // Заменяем inline код `код`
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

        element.innerHTML = html;

        // Обновляем preview если активен
        if (previewActive) {
            updatePreview();
        }
    }
}

// Копирование кода
function copyCode(codeId) {
    const codeElement = document.getElementById(codeId);
    const code = codeElement.textContent;

    navigator.clipboard.writeText(code).then(() => {
        showNotification('Код скопирован');
    }).catch(err => {
        console.error('Ошибка копирования:', err);
        showNotification('Ошибка копирования');
    });
}

// Скачивание кода
function downloadCode(codeId, language) {
    const codeElement = document.getElementById(codeId);
    const code = codeElement.textContent;

    // Определяем расширение файла
    const extensions = {
        'html': 'html',
        'css': 'css',
        'javascript': 'js',
        'js': 'js',
        'python': 'py',
        'java': 'java',
        'cpp': 'cpp',
        'c': 'c',
        'php': 'php',
        'ruby': 'rb',
        'go': 'go',
        'rust': 'rs',
        'typescript': 'ts',
        'json': 'json',
        'xml': 'xml',
        'sql': 'sql',
        'bash': 'sh',
        'shell': 'sh'
    };

    const ext = extensions[language.toLowerCase()] || 'txt';
    const filename = `code.${ext}`;

    // Создаем blob и скачиваем
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showNotification(`Файл ${filename} скачан`);
}

// Асинхронная версия с ожиданием завершения анимации
function addMessageAsync(text, type, scroll = true, animate = false) {
    return new Promise((resolve) => {
        const chatContainer = document.getElementById('chatContainer');

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const content = document.createElement('div');
        content.className = 'message-content';

        const messageText = document.createElement('div');

        content.appendChild(messageText);
        messageDiv.appendChild(content);
        chatContainer.appendChild(messageDiv);

        if (type === 'ai' && animate === true) {
            let currentIndex = 0;
            const speed = 20;

            function type() {
                if (currentIndex < text.length) {
                    messageText.textContent = text.slice(0, currentIndex + 1);
                    currentIndex++;

                    if (scroll) {
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    }

                    setTimeout(type, speed);
                } else {
                    resolve(); // Завершаем Promise когда анимация закончена
                }
            }

            type();
        } else {
            messageText.textContent = text;

            if (scroll) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            resolve();
        }
    });
}

// Показать индикатор печати
function showTypingIndicator() {
    const chatContainer = document.getElementById('chatContainer');

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai';
    messageDiv.id = 'typing-indicator-msg';

    const content = document.createElement('div');
    content.className = 'message-content';

    const typing = document.createElement('div');
    typing.className = 'typing-indicator';
    typing.innerHTML = '<span></span><span></span><span></span>';

    content.appendChild(typing);
    messageDiv.appendChild(content);

    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    return 'typing-indicator-msg';
}

// Удалить индикатор печати
function removeTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) {
        indicator.remove();
    }
}

// Показать уведомление
function showNotification(text) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--bg-tertiary);
        color: var(--text-primary);
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid var(--border);
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        z-index: 9999;
        font-size: 14px;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = text;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Добавляем стили для анимации уведомлений
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }

    .delete-chat-btn {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        width: 20px;
        height: 20px;
        display: none;
        align-items: center;
        justify-content: center;
        background: var(--bg-secondary);
        border-radius: 4px;
        font-size: 18px;
        line-height: 1;
        color: var(--text-secondary);
        cursor: pointer;
    }

    .chat-item {
        position: relative;
        padding-right: 35px;
    }

    .chat-item:hover .delete-chat-btn {
        display: flex;
    }

    .delete-chat-btn:hover {
        background: #ef4444;
        color: white;
    }
`;
document.head.appendChild(style);