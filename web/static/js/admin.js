document.addEventListener("DOMContentLoaded", () => {

    const aspects = [
        "Depresi","Amarah","Mania","Kecemasan","Somatik",
        "Kecenderungan Bunuh Diri","Psikosis","Gangguan Tidur","Gangguan Memori",
        "Disosiasi","Penggunaan Substansi","Pemikiran Berulang"
    ];

    let currentUser = null;

    const list = document.querySelector(".conversation-list");
    const userAssessmentsPanel = document.querySelector(".user-assessments");
    const title = document.querySelector(".chat-area h2");
    const search = document.getElementById("user-search");
    
    async function apiFetch(url, options = {}) {
        const res = await fetch(url, {
            headers: {"Content-Type": "application/json"},
            ...options,
        })
        return res.json();
    }

    async function renderUsers() {
        const res = await apiFetch('/api/admin/all-users');

        list.innerHTML = "";

        res.data.forEach(u => {
            const item = document.createElement("div");
            item.className = "conversation-item";
            item.innerHTML = `<strong>${u.username}</strong> — ${u.email}`;
            item.onclick = () => showUser(u);
            list.appendChild(item);
        });

        showUser(res.data[0]);
    }

    async function showUser(user) {
        currentUser = user;
        title.textContent = `Hasil — ${user.username} (${user.email})`;

        const res = await apiFetch(`/api/admin/all-valid-chats/${user._id}`)
        
        res.data.forEach(chat => {
            const box = document.createElement("div");
            box.innerHTML = `
            <div class="chat-box">
                <div class="chat-info">
                    <div class="chat-title">${chat.title}</div>
                    <div class="chat-date">${chat.started_at}</div>
                </div>
                <button class="download-excel-btn">Download Excel</button>
            </div>
            `;

            const btn = box.querySelector(".download-excel-btn");

            btn.addEventListener("click", async () => {
                try {
                    const res = await fetch(`/api/admin/download-excel/${chat._id}`);
                    
                    if (!res.ok) throw new Error("Download failed");
        
                    const blob = await res.blob();
        
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `${chat.title}.xlsx`;
        
                    document.body.appendChild(a);
                    a.click();
        
                    a.remove();
                    window.URL.revokeObjectURL(url);
                } catch (error) {
                    console.error("Error downloading excel:", error);
                }
            });

            userAssessmentsPanel.append(box);
        });


        // aspects.forEach(a => {
        //     const v = user.scores[a];

        //     const box = document.createElement("div");
        //     box.className = "aspect-item";
            // box.innerHTML = `
            //     <div class="aspect-title">${a}</div>
            //     <div class="progress-bar">
            //         <div class="progress-fill"></div>
            //     </div>
            //     <div class="progress-text">${v}%</div>
            // `;

        //     const fill = box.querySelector(".progress-fill");
        //     setTimeout(() => fill.style.width = v + "%", 30);
        // });
    }

    renderUsers();
});