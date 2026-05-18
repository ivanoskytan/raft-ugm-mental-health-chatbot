document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("aspect-sidebar");
    const toggleBtn = document.getElementById("toggle-aspect-sidebar-btn");
    const chatWindow = document.getElementById("chat-window");
    const chatForm = document.getElementById("chat-form");
    const messageInput = document.getElementById("message-input");
    const newChatBtn = document.getElementById("new-chat-btn");
    const aspectList = document.getElementById("aspect-list");
    const chatList = document.getElementById("chat-list");
    const totalProgressBar = document.getElementById("total_progress-bar");
    const totalProgressInformation = document.getElementById("total_progress-information");
    const userName = document.getElementById("user-name");
    const userEmail = document.getElementById("user-email");

    const renameModal = document.getElementById("rename-modal");
    const renameInput = document.getElementById("rename-input");
    const renameCancelBtn = document.getElementById("rename-cancel-btn");
    const renameSaveBtn = document.getElementById("rename-save-btn");

    const deleteModal = document.getElementById("delete-modal");
    const deleteCancelBtn = document.getElementById("delete-cancel-btn");
    const deleteConfirmBtn = document.getElementById("delete-confirm-btn");
    const toggleSidebarBtn = document.getElementById("toggle-sidebar-btn");
    const mobileToggleAspectBtn = document.getElementById("mobile-toggle-aspect-btn");
    const mainSidebar = document.getElementById("main-sidebar");
    const aspectSidebar = document.getElementById("aspect-sidebar");
    const sidebarOverlay = document.getElementById("sidebar-overlay");

    let activeModalChatId = null;
    let activeModalElement = null;

    function closeAllSidebars() {
        mainSidebar.classList.remove("open");
        aspectSidebar.classList.remove("open");
        sidebarOverlay.classList.remove("show");
    }

    if (toggleSidebarBtn) {
        toggleSidebarBtn.addEventListener("click", () => {
            aspectSidebar.classList.remove("open");
            mainSidebar.classList.toggle("open");
            if (mainSidebar.classList.contains("open")) {
                sidebarOverlay.classList.add("show");
            } else {
                sidebarOverlay.classList.remove("show");
            }
        });
    }

    if (mobileToggleAspectBtn) {
        mobileToggleAspectBtn.addEventListener("click", () => {
            mainSidebar.classList.remove("open");
            aspectSidebar.classList.toggle("open");
            if (aspectSidebar.classList.contains("open")) {
                sidebarOverlay.classList.add("show");
            } else {
                sidebarOverlay.classList.remove("show");
            }
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener("click", closeAllSidebars);
    }
    
    // const SECTION_COLORS = {
    //     "Depression": "#3b82f6",
    //     "Anger": "#ef4444",
    //     "Mania": "#a855f7",
    //     "Anxiety": "#f59e0b",
    //     "Somatic": "#14b8a6",
    //     "Suicidal": "#dc2626",
    //     "Psychosis": "#6366f1",
    //     "Sleep Disturbance": "#0ea5e9",
    //     "Memory": "#22c55e",
    //     "Dissociation": "#eab308",
    //     "Substance Use": "#f97316",
    //     "Repetitive Thought": "#ec4899"
    // }


    let currentChatId = null;
    const user_id = localStorage.getItem("user_id") || null;
    

    async function apiFetch(url, options = {}) {
        const res = await fetch(url, {
            headers: {"Content-Type": "application/json"},
            ...options,
        })
        return res.json();
    }

    function addMessage(text, sender = "bot") {
        const wrapper = document.createElement("div");
        wrapper.className = `chat-message ${sender}`;
        
        const msg = document.createElement("div");
        msg.className = "message";
        msg.textContent = text;

        wrapper.appendChild(msg);
        chatWindow.appendChild(wrapper);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    async function loadUserProfile() {
        const res = await apiFetch(`/api/user/${user_id}`);
        if (res.data) {
            userName.textContent = res.data.username || "Username";
            userEmail.textContent = res.data.email || "username@gmail.com";
        }
    }

    async function loadUserChats() {
        const res = await apiFetch(`/api/chat/user-chats/${user_id}`);
        chatList.innerHTML = "";

        if (res.data && res.data.length > 0) {
            res.data.forEach((chat, index) => {
                const div = document.createElement("div");
                div.className = "chat-item";
                if (currentChatId === chat._id) div.classList.add("active");

                const titleSpan = document.createElement("span");
                titleSpan.className = "chat-title-text"
                titleSpan.textContent = chat.title || `Percakapan ${index + 1}`;
                div.appendChild(titleSpan);
                
                const actionsDiv = document.createElement("div");
                actionsDiv.className = "chat-actions"

                const renameBtn = document.createElement("button");
                renameBtn.className = "material-icons rename-btn";
                renameBtn.textContent = "edit"
                renameBtn.title = "Ubah nama";
                renameBtn.onclick = (e) => {
                    e.stopPropagation();
                    renameChat(chat.id, titleSpan.textContent);
                }

                const deleteBtn = document.createElement("button");
                deleteBtn.className = "material-icons delete-btn";
                deleteBtn.textContent = "delete";
                deleteBtn.title = "Hapus";
                deleteBtn.onclick = (e) => {
                    e.stopPropagation();
                    deleteChat(chat.id, div);
                }   

                actionsDiv.appendChild(renameBtn);
                actionsDiv.appendChild(deleteBtn);
                div.appendChild(actionsDiv);
                
                div.onclick = () => {
                    document.querySelectorAll('.chat-item').forEach(el => el.classList.remove('active'));
                    div.classList.add('active');
                    loadChat(chat._id);
                }
                
                chatList.insertBefore(div, chatList.firstChild);
            });
        }
    }

    async function loadChat(chatId) {
        const res = await apiFetch(`/api/chat/${chatId}`);
        chatWindow.innerHTML = "";
        currentChatId = chatId;

        res.data.items.forEach(item => {
            if (item.user_answer) addMessage(item.user_answer, "user");
            if (item.ai_response) addMessage(item.ai_response, "bot");
        });
        loadAspectProgress();
    }

    function renameChat(chatId, currentTitle) {
        activeModalChatId = chatId;
        renameInput.value = currentTitle;
        renameModal.classList.add("show");
        renameInput.focus();
    }

    function deleteChat(chatId, chatElement) {
        activeModalChatId = chatId;
        activeModalElement = chatElement;
        deleteModal.classList.add("show");
    }

    async function loadAspectProgress() {
        if (!currentChatId) {
            return;
        }
    
        const res = await apiFetch("/api/chat/aspect-progress", {
            method: "POST",
            body: JSON.stringify({
                section: window.currentSection,
                group_id: window.currentGroupId || 0
            }),
        });

        const totalPercentage = res.data["total_percentage"] || 0;
        const totalQuestionAnswered = res.data["total_answered"] || 0;

        totalProgressBar.innerHTML = `
            <div id="total_progress-fill" style="width:${totalPercentage}%"></div>
        `;

        totalProgressInformation.innerHTML = `
            <div id="total_progress-count">${totalQuestionAnswered} / 44 pertanyaan terjawab</div>
            <div id="total_progress-percentage">${totalPercentage}%</div>
        `;
    
        aspectList.innerHTML = "";
    
        // res.data["aspect_progress"].forEach(item => {
        //     const section = item.section;
        //     const percent = item.percentage;
        //     const answered = item.answered;
        //     const total = item.total;
        //     const color = SECTION_COLORS[section] || "#4caf50";
    
        //     const div = document.createElement("div");
        //     div.className = "aspect-item";
    
        //     div.innerHTML = `
        //         <div class="aspect-title">${section}</div>
        //         <div class="progress-count">${answered} / ${total} pertanyaan terjawab</div>
        //         <div class="progress-bar">
        //             <div class="progress-fill"
        //                  style="width:${percent}%; background:${color}"></div>
        //         </div>
        //         <div id="progress-text">${percent}%</div>
        //     `;
    
        //     aspectList.appendChild(div);
        // });
    }
    
    newChatBtn.addEventListener("click", async () => {
        const existingItems = chatList.querySelectorAll('.chat-item').length;
        const nextNumber = existingItems + 1;
        const newTitle = `Percakapan ${nextNumber}`;

        const res = await apiFetch(`/api/chat/start-new-chat`, {
            method: "POST",
            body: JSON.stringify({
                user_id: user_id,
                title: newTitle
            }),
        });
    
        currentChatId = res.data.chat_id;
    
        const chatDiv = document.createElement("div");
        chatDiv.className = "chat-item active";
        chatDiv.textContent = newTitle;
        chatDiv.onclick = () => loadChat(currentChatId);
        
        chatList.insertBefore(chatDiv, chatList.firstChild);

        window.currentGroupId = 0;
        window.currentSection = "Opening";
        window.currentChatId = res.data.chat_id;
        chatWindow.innerHTML = "";
    
        addMessage(res.data.opening_ai_response, "bot");
    });

    renameCancelBtn.addEventListener("click", () => {
        renameModal.classList.remove("show");
        activeModalChatId = null;
    }); 

    renameSaveBtn.addEventListener("click", async () => {
        const newTitle = renameInput.value.trim();
        if (!newTitle || !activeModalChatId) return;

        try {
            const res = await apiFetch(`/api/chat/${activeModalChatId}`, {
                method: 'PUT',
                body: JSON.stringify({
                    "title": newTitle
                })
            });

            if (res.success || res.status === 'success' || res.data) {
                renameModal.classList.remove("show");
                loadUserChats();
            } else {
                alert("Gagal mengubah nama percakapan.");
            }
        } catch (error) {
            console.error("[Client] - Error renaming chat: ", error);
            alert("Terjadi kesalahan koneksi.");
        }
    });

    deleteCancelBtn.addEventListener("click", () => {
        deleteModal.classList.remove("show");
        activeModalChatId = null;
        activeModalElement = null;
    });

    deleteConfirmBtn.addEventListener("click", async () => {
        if (!activeModalChatId) return;

        try {
            const res = await apiFetch(`/api/chat/${activeModalChatId}`, {
                method: 'DELETE'
            });

            if (res.success || res.status === 'success') {
                if (currentChatId === activeModalChatId) {
                    currentChatId = null;
                    chatWindow.innerHTML = "";
                    totalProgressBar.innerHTML = `<div id="total_progress-fill" style="width:0%"></div>`;
                    totalProgressInformation.innerHTML = `<div id="total_progress-count">0 / 44 pertanyaan terjawab</div><div id="total_progress-percentage">0%</div>`;
                    aspectList.innerHTML = "";
                }

                if (activeModalElement) activeModalElement.remove();
                deleteModal.classList.remove("show");
                loadUserChats();
            } else {
                alert("Gagal menghapus percakapan.");
            }
        } catch (error) {
            console.error("[Client] - Error deleting chat: ", error);
            alert("Terjadi kesalahan koneksi saat menghapus.");
        }
    });  

    function showLoading() {
        const wrapper = document.createElement("div");
        wrapper.className = "chat-message bot loading-msg";
        wrapper.id = "typing-indicator";
        
        const loader = document.createElement("div");
        loader.className = "message typing-loader";
        loader.innerHTML = "<span></span><span></span><span></span>";

        wrapper.appendChild(loader);
        chatWindow.appendChild(wrapper);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function removeLoading() {
        const indicator = document.getElementById("typing-indicator");
        if (indicator) indicator.remove();
    }

    function addChatProcessing() {
        const overlay = document.createElement("div");
        overlay.id = "chat-processing-overlay";

        overlay.innerHTML = `
            <div class="processing-box">
                <div class="typing-loader">
                    <span></span><span></span><span></span>
                </div>
                <div class="processing-text">
                    Sedang memproses hasil percakapan...
                </div>
            </div>
        `;

        chatWindow.appendChild(overlay);
    }

    function removeChatProcessing() {
        const overlay = document.getElementById("chat-processing-overlay");
        if (overlay) overlay.remove();
    }

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        if (!currentChatId) {
            alert("Silakan mulai percakapan baru terlebih dahulu.");
            return;
        }

        const userAnswer = messageInput.value.trim();
        if (!userAnswer) return;

        addMessage(userAnswer, "user");
        messageInput.value = "";

        showLoading();

        setTimeout(async () => {
            try {
                const res = await apiFetch("/api/chat/process-user-answer", {
                    method: "POST",
                    body: JSON.stringify({
                        group_id: window.currentGroupId || 0,
                        section: window.currentSection || "",
                        user_answer: userAnswer,
                        chat_id: window.currentChatId,
                    }),
                });
                
                loadAspectProgress();
                const resData = res.data;
                
                window.currentGroupId = resData.next_group_id;
                window.currentSection = resData.next_section;
                
                removeLoading();
                addMessage(resData.ai_response, "bot");

                if (window.currentSection === "Ending") {
                    addChatProcessing();

                    await apiFetch("api/chat/end-chat", {
                        method: "POST",
                        body: JSON.stringify({
                            chat_id: window.currentChatId,
                            user_id: user_id
                        })
                    });

                    removeChatProcessing();
                }
                
            } catch (error) {
                removeLoading();
                addMessage("Maaf, terjadi kesalahan koneksi.", "bot");
                console.log("[Client] - Error: ", error);
            }
        }, 2000);
    });

    window.addEventListener("click", (e) => {
        if (e.target === renameModal) renameModal.classList.remove("show");
        if (e.target === deleteModal) deleteModal.classList.remove("show");
    });
    
    loadUserProfile();
    loadUserChats();
    loadAspectProgress();
});


