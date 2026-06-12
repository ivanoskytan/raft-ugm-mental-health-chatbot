const submitBtn = document.getElementById('submit-btn');

const email = document.getElementById('email');
const password = document.getElementById('password');
const tooglePasswordButton = document.querySelector('.toggle-password');

tooglePasswordButton.addEventListener('click', function() {
    const passwordInput = this.previousElementSibling;
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    this.textContent = type === 'password' ? 'visibility_off' : 'visibility';
});

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const emailValue = email.value;
    const passwordValue = password.value;

    const cleanedEmail = emailValue.trim();
    const emailRegex = /@(gmail\.com|mail\.ugm\.ac\.id)$/;
    if (!emailRegex.test(cleanedEmail)) {
        showMessage("Email admin harus menggunakan domain @mail.ugm.ac.id", "red");
        return;
    }

    const payload = {
        email: cleanedEmail,
        role: "admin",
        password: passwordValue
    };

    try {
        submitBtn.disabled = true;
        submitBtn.innerText = "Masuk...";

        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
            localStorage.setItem('access_token', result.data.token);
            localStorage.setItem('user_id', result.data.user_id);
            
            showMessage("Login berhasil! Mengalihkan ke halaman admin...", "green");
            
            setTimeout(() => {
                window.location.href = "/admin"; 
            }, 1500);
        } else {
            showMessage(result.message || "Email atau password salah", "red");
            submitBtn.disabled = false;
            submitBtn.innerText = "Masuk";
        }
    } catch (error) {
        showMessage("Terjadi kesalahan koneksi", "red");
        submitBtn.disabled = false;
        submitBtn.innerText = "Masuk";
    }
});

function showMessage(text, color) {
    const messageBox = document.getElementById('message-box');
    messageBox.innerText = text;
    messageBox.style.display = 'block';
    messageBox.style.backgroundColor = color === "green" ? "#d4edda" : "#f8d7da";
    messageBox.style.color = color === "green" ? "#155724" : "#721c24";
}