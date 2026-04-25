document.addEventListener("DOMContentLoaded", () => {
    
    // UI Elements
    const menuAnalisis = document.getElementById("menu-analisis");
    const menuDaftar = document.getElementById("menu-daftar");
    const viewAnalisis = document.getElementById("view-analisis");
    const viewDaftar = document.getElementById("view-daftar-pengguna");
    const viewUserDetail = document.getElementById("view-user-detail");
    
    const userTableBody = document.getElementById("user-table-body");
    const btnBackToList = document.getElementById("btn-back-to-list");
    const aspectSelector = document.getElementById("aspect-selector");

    // --- NAVIGATION LOGIC ---

    const switchView = (viewName) => {
        [viewAnalisis, viewDaftar, viewUserDetail].forEach(v => v.style.display = 'none');
        
        [menuAnalisis, menuDaftar].forEach(m => m.classList.remove('active'));

        if (viewName === 'analisis') {
            viewAnalisis.style.display = 'block';
            menuAnalisis.classList.add('active');
        } else if (viewName === 'daftar') {
            viewDaftar.style.display = 'block';
            menuDaftar.classList.add('active');
            renderUserTable();
        } else if (viewName === 'detail') {
            viewUserDetail.style.display = 'block';
            menuDaftar.classList.add('active'); // Keep menu highlight on users
        }
    };

    menuAnalisis.addEventListener("click", () => switchView('analisis'));
    menuDaftar.addEventListener("click", () => switchView('daftar'));
    btnBackToList.addEventListener("click", () => switchView('daftar'));

    let aspectChart = null;
    const initAnalysis = () => {
        const aspect = aspectSelector.value;
        const now = new Date();
        const lastMonth = new Date();
        lastMonth.setMonth(now.getMonth() - 1);

        const payload = {
            aspect: aspect,
            from_date: lastMonth.toISOString(),
            to_date: now.toISOString(),
            top_k: 5
        };

        fetchChartData(payload);
        fetchTopUsers(payload);
    };

    // --- DATA FETCHING ---

    async function apiFetch(url, options={}) {
        const res = await fetch(url, options);

        if (!res.ok) {
            const errorData= await res.json();
            throw new Error(errorData.error || `Error ${res.status}`);
        }
        return res.json();
    }

    // 1. Render Aspect Analysis Chart
    async function fetchChartData(payload) {
        const res = await apiFetch('/api/admin/real-time-assessment-results', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const labels = res.data.map(item => `Skor ${item._id}`);
        const counts = res.data.map(item => item.user_count);

        renderChart(labels, counts);
    }

    // 2. Render Top Users by Aspect Highest Avg Score
    async function fetchTopUsers(payload) {
        const  res = await apiFetch('/api/admin/top-scored-users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const tbody = document.getElementById("top-users-body");
        tbody.innerHTML = "";

        res.data.forEach(user => {
            const row = `<tr>
                <td>${user.username}</td>
                <td style="color:#ef4444; font-weight:bold;">${user.average_score.toFixed(1)}</td>
            </tr>`;
            tbody.innerHTML += row;
        });
    }

    // 3. Render Table of Users
    async function renderUserTable() {
        const res = await apiFetch('/api/admin/all-users');
        userTableBody.innerHTML = "";

        res.data.forEach(user => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td><strong>${user.username}</strong></td>
                <td>${user.email}</td>
                <td><button class="download-excel-btn">Lihat Detail</button></td>
            `;
            
            // Redirect on row click
            row.onclick = () => showUserDetail(user);
            
            userTableBody.appendChild(row);
        });
    }

    function renderChart(labels, data) {
        const ctx = document.getElementById('aspectChart').getContext('2d');
        
        if (aspectChart) { aspectChart.destroy(); }

        aspectChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Jumlah Pengguna',
                    data: data,
                    backgroundColor: '#2f60f5',
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#1e222b' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // 4. Render Specific User Detail (Redirected View)
    async function showUserDetail(user) {
        switchView('detail');
        
        document.getElementById("detail-title").textContent = `Hasil — ${user.username}`;
        const summaryText = document.getElementById("summary-text");
        const assessmentsList = document.getElementById("user-assessments-list");

        summaryText.textContent = "Memuat analisis pengguna...";
        assessmentsList.innerHTML = "";

        // Fetch User History
        try {
            const res = await apiFetch(`/api/admin/all-valid-chats/${user._id}`);
            
            if (res.data.length === 0) {
                assessmentsList.innerHTML = "<p>Tidak ada riwayat asesmen untuk pengguna ini.</p>";
            }

            res.data.forEach(chat => {
                const box = document.createElement("div");
                box.className = "chat-box";
                box.innerHTML = `
                    <div class="chat-info">
                        <div style="font-weight:bold">${chat.title}</div>
                        <div style="font-size:0.8rem; color:#9ca3af">${chat.started_at}</div>
                    </div>
                    <button class="download-excel-btn" data-id="${chat._id}">Download Excel</button>
                `;

                // Excel Download Logic
                box.querySelector("button").onclick = (e) => {
                    e.stopPropagation();
                    window.location.href = `/api/admin/download-excel/${chat._id}`;
                };

                assessmentsList.appendChild(box);
            });

            // Update summary text if available in your user object
            summaryText.textContent = user.summary || "Pengguna telah menyelesaikan asesmen. Silakan tinjau histori di bawah.";
            
        } catch (err) {
            console.error("Error loading details:", err);
            summaryText.textContent = "Gagal memuat data.";
        }
    }

    aspectSelector.addEventListener("change", initAnalysis);
    document.getElementById("menu-analisis").addEventListener("click", initAnalysis);
});