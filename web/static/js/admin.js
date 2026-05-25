import { apiFetch } from "./api.js";

document.addEventListener("DOMContentLoaded", () => {
    const menuAnalisis = document.getElementById("menu-analisis");
    const menuDaftar = document.getElementById("menu-daftar");
    const viewAnalisis = document.getElementById("view-analisis");
    const viewDaftar = document.getElementById("view-daftar-pengguna");
    const viewUserDetail = document.getElementById("view-user-detail");
    
    const searchUsernameInput = document.getElementById("search-username-input");
    const searchUserBtn = document.getElementById("search-user-btn");
    const userTableBody = document.getElementById("user-table-body");
    const btnBackToList = document.getElementById("btn-back-to-list");
    const aspectSelector = document.getElementById("aspect-selector");
    const fromDateInput = document.getElementById('fromDate');
    const toDateInput = document.getElementById('toDate');

    const filterBtn = document.getElementById("filter-btn");

    const toggleSidebarBtn = document.getElementById("toggle-sidebar-btn");
    const adminSidebar = document.getElementById("admin-sidebar");
    const sidebarOverlay = document.getElementById("sidebar-overlay");
    const menuItems = document.querySelectorAll(".menu-item");

    function closeSidebar() {
        if (adminSidebar) adminSidebar.classList.remove("open");
        if (sidebarOverlay) sidebarOverlay.classList.remove("show");
    }

    if (toggleSidebarBtn) {
        toggleSidebarBtn.addEventListener("click", () => {
            if (adminSidebar) adminSidebar.classList.toggle("open");
            if (sidebarOverlay) {
                if (adminSidebar.classList.contains("open")) {
                    sidebarOverlay.classList.add("show");
                } else {
                    sidebarOverlay.classList.remove("show");
                }
            }
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener("click", closeSidebar);
    }

    menuItems.forEach(item => {
        item.addEventListener("click", closeSidebar);
    });

    let topUsersData = [];
    let currentPage = 1;
    const rowsPerPage = 5;

    const applyKBtn = document.getElementById("apply-k-btn");
    const kValueInput = document.getElementById("k-value");

    applyKBtn.addEventListener("click", () => {
        const kValue = parseInt(kValueInput.value) || 5;
        const payload = { k: kValue };
        fetchTopUsers(payload);
    });

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

    const setDefaultValues = () => {
        const now = new Date();
        const lastMonth = new Date();

        lastMonth.setMonth(now.getMonth()-1);
        const formatDate = (date) => date.toISOString().split('T')[0];

        fromDateInput.value = formatDate(lastMonth);
        toDateInput.value = formatDate(now);

        aspectSelector.value = "Depression";
    };

    const initAnalysis = () => {
        const aspect = aspectSelector.value;
        const fromDateVal = fromDateInput.value;
        const toDateVal = toDateInput.value;

        const start = new Date(fromDateVal);
        start.setUTCHours(0, 0, 0, 0);

        const end = new Date(toDateVal);
        end.setUTCHours(23, 59, 59, 999);

        const payload = {
            aspect: aspect,
            from_date: start.toISOString(),
            to_date: end.toISOString(),
            top_k: 5
        };

        fetchChartData(payload);
        fetchTopUsers(payload);
    };

    aspectSelector.addEventListener("change", initAnalysis);
    filterBtn.addEventListener('click', initAnalysis);
    setDefaultValues();
    initAnalysis();

    // 1. Render Aspect Analysis Chart
    async function fetchChartData(payload) {
        const res = await apiFetch('/api/admin/real-time-assessment-results', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    
        if (res.data && res.data.results) {
            const chartPoints = res.data.results.map(item => ({
                x: item._id, 
                y: item.user_count
            })).sort((a, b) => a.x - b.x);
    
            const distMap = {};
            res.data.score_distributions.forEach(d => {
                distMap[d.score] = d.description;
            });
    
            renderChart(chartPoints, distMap);
        }
    }

    // 2. Render Top Users by Aspect Highest Avg Score
    async function fetchTopUsers(payload) {
        const  res = await apiFetch('/api/admin/top-scored-users', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        const tbody = document.getElementById("top-users-body");
        tbody.innerHTML = "";

        if (res.data && res.data.length > 0) {
            topUsersData = res.data;
            currentPage = 1; 
            renderTablePage(currentPage);
        } else {
            topUsersData = [];
            const tbody = document.getElementById("top-users-body");
            tbody.innerHTML = "<tr><td colspan='2' style='text-align:center;'>No data found</td></tr>";
            document.getElementById("pagination-container").innerHTML = "";
        }
    }

    function renderTablePage(page) {
        const tbody = document.getElementById("top-users-body");
        tbody.innerHTML = "";
        
        const start = (page - 1) * rowsPerPage;
        const end = start + rowsPerPage;
        const paginatedItems = topUsersData.slice(start, end);

        paginatedItems.forEach(user => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>
                    <div style="display: flex; flex-direction: column;">
                        <span style="font-weight: bold;">${user.username}</span>
                        <span style="font-size: 0.8rem; color: #9ca3af;">${user.email}</span>
                    </div>
                </td>
                <td style="text-align: right; font-weight: 800; color: #2f60f5;">
                    ${user.average_score}
                </td>
            `;
            tbody.appendChild(row);
        });

        setupPaginationUI();
    }

    function setupPaginationUI() {
        const paginationContainer = document.getElementById("pagination-container");
        paginationContainer.innerHTML = "";

        const pageCount = Math.ceil(topUsersData.length / rowsPerPage);
        
        if (pageCount <= 1) return;

        const prevBtn = document.createElement("button");
        prevBtn.textContent = "«";
        prevBtn.disabled = currentPage === 1;
        prevBtn.onclick = () => {
            currentPage--;
            renderTablePage(currentPage);
        };
        paginationContainer.appendChild(prevBtn);

        for (let i = 1; i <= pageCount; i++) {
            const pageBtn = document.createElement("button");
            pageBtn.textContent = i;
            if (i === currentPage) pageBtn.classList.add("active");

            pageBtn.onclick = () => {
                currentPage = i;
                renderTablePage(currentPage);
            };
            paginationContainer.appendChild(pageBtn);
        }

        const nextBtn = document.createElement("button");
        nextBtn.textContent = "»";
        nextBtn.disabled = currentPage === pageCount;
        nextBtn.onclick = () => {
            currentPage++;
            renderTablePage(currentPage);
        };
        paginationContainer.appendChild(nextBtn);
    }

    // 3. Render Table of Users
    searchUserBtn.addEventListener("click", () => {
        renderUserTable();
    });

    searchUsernameInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            renderUserTable();
        }
    });

    async function renderUserTable() {
        const keyword = searchUsernameInput.value.trim();
        const res = await apiFetch('/api/admin/all-users');
        
        if (keyword) {
            const params = new URLSearchParams({ username: keyword });
            url += `?${params.toString()}`;
        }
        
        userTableBody.innerHTML = "<tr><td colspan='3' style='text-align:center; color:#9ca3af;'>Memuat data...</td></tr>";
        
        try {
            userTableBody.innerHTML = "";
            
            if (res.data && res.data.length > 0) {
                res.data.forEach(user => {
                    const row = document.createElement("tr");
                    row.innerHTML = `
                        <td><strong>${user.username}</strong></td>
                        <td>${user.email}</td>
                        <td><button class="download-excel-btn">Lihat Detail</button></td>
                    `;
                    
                    row.onclick = () => showUserDetail(user);
                    
                    userTableBody.appendChild(row);
                });
            }
        } catch (error) {
            console.error("[Client] - Gagal memuat daftar pengguna:", error);
            userTableBody.innerHTML = "<tr><td colspan='3' style='text-align:center; color:#ef4444;'>Terjadi kesalahan koneksi</td></tr>";
        }
    }

    function renderChart(chartPoints, distMap) {
        const ctx = document.getElementById('aspectChart').getContext('2d');
        if (aspectChart) { aspectChart.destroy(); }
    
        aspectChart = new Chart(ctx, {
            type: 'line', 
            data: {
                datasets: [{
                    label: 'Jumlah Pengguna',
                    data: chartPoints, // [{x: 2.0, y: 1}, {x: 2.67, y: 1}]
                    borderColor: '#2f60f5',
                    backgroundColor: 'rgba(47, 96, 245, 0.2)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 6,
                    pointBackgroundColor: '#2f60f5'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'linear',
                        min: 1,
                        max: 5,
                        ticks: {
                            stepSize: 1,
                            color: '#9ca3af',
                            padding: 10, // Gives space between the line and the labels
                            callback: function(value) {
                                const description = distMap[value];
                                if (description) {
                                    return [value, description];
                                }
                                return value;
                            }
                        },
                        grid: { 
                            display: true, 
                            color: 'rgba(255, 255, 255, 0.05)', // Subtle vertical lines at whole numbers
                            drawOnChartArea: true 
                        }
                    },
                    y: { 
                        beginAtZero: true, 
                        ticks: { precision: 0, color: '#9ca3af' },
                        grid: { color: '#1e222b' }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            title: (items) => `Skor: ${items[0].parsed.x.toFixed(2)}`,
                            label: (item) => `Jumlah: ${item.parsed.y} Pengguna`
                        }
                    },
                    legend: { display: false }
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
            const res = await apiFetch(`/api/admin/all-valid-chats/${user.id}`);
            
            if (res.data.length === 0) {
                assessmentsList.innerHTML = "<p>Tidak ada riwayat asesmen untuk pengguna ini.</p>";
            }

            res.data.forEach(chat => {
                const box = document.createElement("div");
                box.className = "chat-box";

                const statusLabel = chat.valid ?
                    `<span class="status-badge valid">Valid</span>` 
                    : `<span class="status-badge invalid">Invalid</span>`;
                    
                const downloadBtn = chat.valid 
                    ? `<button class="download-excel-btn" data-id="${chat.id}">Download Excel</button>` 
                    : ``;

                box.innerHTML = `
                    <div class="chat-info">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div style="font-weight:bold">${chat.title}</div>
                            ${statusLabel}
                        </div>
                        <div style="font-size:0.8rem; color:#9ca3af">${new Date(chat.started_at).toLocaleString()}</div>
                    </div>
                    ${downloadBtn}
                `;

                // Excel Download Logic
                const btn = box.querySelector(".download-excel-btn");
                if (btn) {
                    btn.onclick = (e) => {
                        e.stopPropagation();
                        window.location.href = `/api/admin/download-excel/${chat.id}`;
                    };
                }

                assessmentsList.appendChild(box);
            });

            // Update summary text if available in your user object
            summaryText.textContent = user.summary || "Pengguna belum pernah menyelesaikan asesmen kesehatan mental. Silakan tinjau histori di bawah.";
            
        } catch (err) {
            console.error("Error loading details:", err);
            summaryText.textContent = "Gagal memuat data.";
        }
    }

    // 5. Render admin profile
    async function loadUserProfile() {
        const res = await apiFetch(`/api/user/${user_id}`);
        if (res.data) {
            userName.textContent = res.data.username || "Username";
            userEmail.textContent = res.data.email || "username@gmail.com";
        }
    }

    aspectSelector.addEventListener("change", initAnalysis);
    document.getElementById("menu-analisis").addEventListener("click", initAnalysis);
    loadUserProfile();
});