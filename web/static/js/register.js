const submitBtn = document.getElementById('submit-btn');
    
const username = document.getElementById('username').value;
const email = document.getElementById('email').value;
const password = document.getElementById('password').value;
const confirm = document.getElementById('confirm').value;
const togglePasswordButtons = document.querySelectorAll('.toggle-password');
const registerForm = document.getElementById('register-form');

togglePasswordButtons.forEach(button => {
    button.addEventListener('click', function() {
        const passwordInput = this.previousElementSibling;

        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        
        this.textContent = type === 'password' ? 'visibility_off' : 'visibility';
    });
});

registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const emailRegex = /@(gmail\.com|mail\.ugm\.ac\.id)$/;
    if (!emailRegex.test(email)) {
        showMessage("Email harus menggunakan domain @gmail.com atau @mail.ugm.ac.id", "red");
        return;
    }

    if (password !== confirm) {
        showMessage("Kata sandi tidak cocok", "red");
        return;
    }

    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/;
    if (!passwordRegex.test(password)) {
        showMessage("Kata sandi harus minimal 8 karakter, mengandung huruf dan angka", "red");
        return;
    }

    const payload = {
        username: username,
        email: email,
        password: password,
        role: "user" 
    };

    try {
        submitBtn.disabled = true;
        submitBtn.innerText = "Memproses...";

        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
            showMessage("Registrasi berhasil! Mengalihkan...", "green");
            setTimeout(() => {
                window.location.href = "/login";
            }, 2000);
        } else {
            showMessage(result.message || "Registrasi gagal", "red");
            submitBtn.disabled = false;
            submitBtn.innerText = "Daftar";
        }
    } catch (error) {
        showMessage("Terjadi kesalahan koneksi", "red");
        submitBtn.disabled = false;
        submitBtn.innerText = "Daftar";
    }
});

function showMessage(text, color) {
    const messageBox = document.getElementById('message-box');
    messageBox.innerText = text;
    messageBox.style.display = 'block';
    messageBox.style.backgroundColor = color === "green" ? "#d4edda" : "#f8d7da";
    messageBox.style.color = color === "green" ? "#155724" : "#721c24";
}