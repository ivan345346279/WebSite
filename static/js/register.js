let currentEmail = '';
let verificationCode = '';
let loginEmail = '';

// Показать шаг
function showStep(stepId) {
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active');
    });
    document.getElementById(stepId).classList.add('active');
}

// Показать/скрыть загрузку
function showLoading(show) {
    const loading = document.getElementById('loading');
    if (show) {
        loading.classList.add('active');
    } else {
        loading.classList.remove('active');
    }
}

// Показать ошибку
function showError(message, formId) {
    const form = document.getElementById(formId);

    // Удаляем старую ошибку если есть
    const oldError = form.querySelector('.error-message');
    if (oldError) {
        oldError.remove();
    }

    // Добавляем новую ошибку
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    form.insertBefore(errorDiv, form.firstChild);

    // Удаляем через 5 секунд
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// Шаг 1: Приветствие
window.addEventListener('load', () => {
    // Кнопка "Продолжить" появится через 3 секунды (CSS анимация)
    // Автоматический переход убран
});

// Шаг 2: Отправка кода на почту
async function sendCode(event) {
    event.preventDefault();

    const email = document.getElementById('emailInput').value.trim();

    if (!email) {
        showError('Введи почту', 'emailForm');
        return;
    }

    currentEmail = email;
    showLoading(true);

    try {
        const response = await fetch('/api/auth/send-code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('userEmail').textContent = email;
            showStep('step-code');
        } else {
            showError(data.error || 'Ошибка отправки кода', 'emailForm');
        }
    } catch (error) {
        showError('Ошибка соединения', 'emailForm');
    } finally {
        showLoading(false);
    }
}

// Повторная отправка кода
async function resendCode() {
    if (!currentEmail) return;

    showLoading(true);

    try {
        const response = await fetch('/api/auth/send-code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: currentEmail })
        });

        const data = await response.json();

        if (response.ok) {
            showError('Код отправлен повторно', 'codeForm');
        } else {
            showError(data.error || 'Ошибка отправки кода', 'codeForm');
        }
    } catch (error) {
        showError('Ошибка соединения', 'codeForm');
    } finally {
        showLoading(false);
    }
}

// Шаг 3: Проверка кода
async function verifyCode(event) {
    event.preventDefault();

    const code = document.getElementById('codeInput').value.trim();

    if (!code || code.length !== 6) {
        showError('Введи 6-значный код', 'codeForm');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch('/api/auth/verify-code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: currentEmail, code })
        });

        const data = await response.json();

        if (response.ok) {
            verificationCode = code;
            showStep('step-profile');
        } else {
            showError(data.error || 'Неверный код', 'codeForm');
        }
    } catch (error) {
        showError('Ошибка соединения', 'codeForm');
    } finally {
        showLoading(false);
    }
}

// Предпросмотр аватара
function previewAvatar(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Проверка размера (макс 5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert('Файл слишком большой. Максимум 5MB');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        const preview = document.getElementById('avatarPreview');
        preview.innerHTML = `<img src="${e.target.result}" alt="Avatar">`;
    };
    reader.readAsDataURL(file);
}

// Шаг 4: Завершение регистрации
async function completeRegistration(event) {
    event.preventDefault();

    const nickname = document.getElementById('nicknameInput').value.trim();
    const avatarInput = document.getElementById('avatarInput');

    if (!nickname) {
        showError('Введи ник', 'profileForm');
        return;
    }

    showLoading(true);

    try {
        const formData = new FormData();
        formData.append('email', currentEmail);
        formData.append('code', verificationCode);
        formData.append('nickname', nickname);

        if (avatarInput.files[0]) {
            formData.append('avatar', avatarInput.files[0]);
        }

        const response = await fetch('/api/auth/register', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            // Перенаправляем на главную страницу
            window.location.href = '/';
        } else {
            showError(data.error || 'Ошибка регистрации', 'profileForm');
        }
    } catch (error) {
        showError('Ошибка соединения', 'profileForm');
    } finally {
        showLoading(false);
    }
}

// Вход: отправка кода
async function sendLoginCode(event) {
    event.preventDefault();

    const email = document.getElementById('loginEmailInput').value.trim();

    if (!email) {
        showError('Введи почту', 'loginForm');
        return;
    }

    loginEmail = email;
    showLoading(true);

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('loginUserEmail').textContent = email;
            showStep('step-login-code');
        } else {
            showError(data.error || 'Ошибка отправки кода', 'loginForm');
        }
    } catch (error) {
        showError('Ошибка соединения', 'loginForm');
    } finally {
        showLoading(false);
    }
}

// Повторная отправка кода для входа
async function resendLoginCode() {
    if (!loginEmail) return;

    showLoading(true);

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: loginEmail })
        });

        const data = await response.json();

        if (response.ok) {
            showError('Код отправлен повторно', 'loginCodeForm');
        } else {
            showError(data.error || 'Ошибка отправки кода', 'loginCodeForm');
        }
    } catch (error) {
        showError('Ошибка соединения', 'loginCodeForm');
    } finally {
        showLoading(false);
    }
}

// Проверка кода для входа
async function verifyLoginCode(event) {
    event.preventDefault();

    const code = document.getElementById('loginCodeInput').value.trim();

    if (!code || code.length !== 6) {
        showError('Введи 6-значный код', 'loginCodeForm');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch('/api/auth/login-verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: loginEmail, code })
        });

        const data = await response.json();

        if (response.ok) {
            // Перенаправляем на главную страницу
            window.location.href = '/';
        } else {
            showError(data.error || 'Неверный код', 'loginCodeForm');
        }
    } catch (error) {
        showError('Ошибка соединения', 'loginCodeForm');
    } finally {
        showLoading(false);
    }
}
