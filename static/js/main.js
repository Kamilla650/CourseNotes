
document.addEventListener('DOMContentLoaded', function () {

    // 1. Проверка формы регистрации
    const registerForm = document.getElementById('register-form');

    if (registerForm) {
        const email = document.getElementById('id_email');
        const password1 = document.getElementById('id_password1');
        const password2 = document.getElementById('id_password2');

        function clearError(field) {
            if (!field) return;

            field.classList.remove('error');
            field.removeAttribute('aria-invalid');
            field.removeAttribute('aria-describedby');

            const wrapper = field.closest('.form-field');
            const error = wrapper?.querySelector('.js-field-error');

            if (error) error.remove();
        }

        function showError(field, message) {
            if (!field) return;

            clearError(field);

            const wrapper = field.closest('.form-field');
            if (!wrapper) return;

            const error = document.createElement('span');
            error.className = 'field-error js-field-error';
            error.id = field.id + '-error';
            error.textContent = message;
            error.setAttribute('role', 'alert');

            wrapper.appendChild(error);
            field.classList.add('error');
            field.setAttribute('aria-invalid', 'true');
            field.setAttribute('aria-describedby', error.id);
        }

        function validateEmail() {
            if (!email) return true;

            clearError(email);
            const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

            if (!pattern.test(email.value.trim())) {
                showError(email, 'Введите корректный адрес электронной почты.');
                return false;
            }

            return true;
        }

        function validatePassword() {
            if (!password1) return true;

            clearError(password1);

            if (password1.value.length < 8) {
                showError(password1, 'Пароль должен содержать не менее 8 символов.');
                return false;
            }

            return true;
        }

        function validatePasswordRepeat() {
            if (!password1 || !password2) return true;

            clearError(password2);

            if (!password2.value.trim()) {
                showError(password2, 'Повторите пароль.');
                return false;
            }

            if (password2.value !== password1.value) {
                showError(password2, 'Пароли не совпадают.');
                return false;
            }

            return true;
        }

        if (email) {
            email.addEventListener('blur', validateEmail);
            email.addEventListener('input', () => clearError(email));
        }

        if (password1) {
            password1.addEventListener('blur', validatePassword);
            password1.addEventListener('input', () => {
                clearError(password1);
                if (password2) clearError(password2);
            });
        }

        if (password2) {
            password2.addEventListener('blur', validatePasswordRepeat);
            password2.addEventListener('input', () => clearError(password2));
        }

        registerForm.addEventListener('submit', function (event) {
            const valid =
                validateEmail() &&
                validatePassword() &&
                validatePasswordRepeat();

            if (!valid) event.preventDefault();
        });
    }

    // 2. Проверка формы входа
    const loginForm = document.getElementById('login-form');

    if (loginForm) {
        const email = document.getElementById('id_username');
        const password = document.getElementById('id_password');
        const errorBox = document.getElementById('login-error');

        function clearLoginError(field) {
            if (!field) return;

            field.classList.remove('error');
            field.removeAttribute('aria-invalid');
            field.removeAttribute('aria-describedby');

            const wrapper = field.closest('.form-field');
            const error = wrapper?.querySelector('.js-field-error');

            if (error) error.remove();
        }

        function showLoginError(field, message) {
            if (!field) return;

            clearLoginError(field);

            const wrapper = field.closest('.form-field');
            if (!wrapper) return;

            const error = document.createElement('span');
            error.className = 'field-error js-field-error';
            error.id = field.id + '-js-error';
            error.textContent = message;
            error.setAttribute('role', 'alert');

            wrapper.appendChild(error);
            field.classList.add('error');
            field.setAttribute('aria-invalid', 'true');
            field.setAttribute('aria-describedby', error.id);
        }

        function validateLoginEmail() {
            if (!email) return true;

            clearLoginError(email);

            if (!email.value.trim()) {
                showLoginError(email, 'Введите адрес электронной почты.');
                return false;
            }

            if (!email.validity.valid) {
                showLoginError(email, 'Введите корректный адрес электронной почты.');
                return false;
            }

            return true;
        }

        function validateLoginPassword() {
            if (!password) return true;

            clearLoginError(password);

            if (!password.value.trim()) {
                showLoginError(password, 'Введите пароль.');
                return false;
            }

            return true;
        }

        if (email) {
            email.addEventListener('blur', validateLoginEmail);
            email.addEventListener('input', () => clearLoginError(email));
        }

        if (password) {
            password.addEventListener('blur', validateLoginPassword);
            password.addEventListener('input', () => clearLoginError(password));
        }

        loginForm.addEventListener('submit', function (event) {
            const emailValid = validateLoginEmail();
            const passwordValid = validateLoginPassword();

            if (!emailValid || !passwordValid) {
                event.preventDefault();

                if (errorBox) {
                    errorBox.textContent = 'Пожалуйста, заполните поля правильно.';
                    errorBox.hidden = false;
                }
            } else if (errorBox) {
                errorBox.textContent = '';
                errorBox.hidden = true;
            }
        });
    }

    // 3. Кнопки показа и скрытия пароля
    document.querySelectorAll('input[type="password"]').forEach(function (input) {
        const button = document.createElement('button');

        button.type = 'button';
        button.textContent = 'Показать';
        button.className = 'password-toggle';
        button.setAttribute('aria-label', 'Показать пароль');

        button.style.marginTop = '8px';
        button.style.padding = '6px 12px';
        button.style.cursor = 'pointer';

        input.insertAdjacentElement('afterend', button);

        button.addEventListener('click', function () {
            const isHidden = input.type === 'password';

            input.type = isHidden ? 'text' : 'password';
            button.textContent = isHidden ? 'Скрыть' : 'Показать';
            button.setAttribute(
                'aria-label',
                isHidden ? 'Скрыть пароль' : 'Показать пароль'
            );
        });
    });

    // 4. Автоматическое скрытие уведомлений
    document.querySelectorAll('.message').forEach(function (message) {
        setTimeout(function () {
            message.classList.add('message-hidden');
        }, 5000);
    });

});
