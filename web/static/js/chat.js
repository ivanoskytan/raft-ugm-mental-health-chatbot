document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("aspect-sidebar");
    const toggleBtn = document.getElementById("toggle-aspect-sidebar-btn");
    const chatWindow = document.getElementById("chat-window");
    const chatForm = document.getElementById("chat-form");
    const messageInput = document.getElementById("message-input");
    const newChatBtn = document.getElementById("new-chat-btn");
    const aspectList = document.getElementById("aspect-list");
    const conversationList = document.getElementById("conversation-list");
    
    const SECTION_COLORS = {
        "Depression": "#3b82f6",
        "Anger": "#ef4444",
        "Mania": "#a855f7",
        "Anxiety": "#f59e0b",
        "Somatic": "#14b8a6",
        "Suicidal": "#dc2626",
        "Psychosis": "#6366f1",
        "Sleep Disturbance": "#0ea5e9",
        "Memory": "#22c55e",
        "Dissociation": "#eab308",
        "Substance Use": "#f97316",
        "Repetitive Thought": "#ec4899"
    };


    let currentChatId = null;
    const user_id = localStorage.getItem("user_id") || null;
        
    toggleBtn.addEventListener("click", () => {
        sidebar.classList.toggle("hidden");

        if (sidebar.classList.contains("hidden")) {
            toggleBtn.textContent = "⮜";
            toggleBtn.style.right = "40px";
        }
        else {
            toggleBtn.textContent = "⮞";
            toggleBtn.style.right = "300px";
        }
    });

    async function apiFetch(url, options = {}) {
        const res = await fetch(url, {
            headers: {"Content-Type": "application/json"},
            ...options,
        })
        return res.json();
    };

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

    async function loadUserChats() {
        const res = await apiFetch(`/api/chat/user-chats/${user_id}`);
        conversationList.innerHTML = "";

        if (res.data && res.data.length > 0) {
            res.data.forEach((chat, index) => {
                const div = document.createElement("div");
                div.className = "conversation-item";
                
                div.textContent = chat.title || `Percakapan ${index + 1}`;
                
                div.onclick = () => {
                    document.querySelectorAll('.conversation-item').forEach(el => el.classList.remove('active'));
                    div.classList.add('active');
                    loadChat(chat._id);
                };
                
                conversationList.insertBefore(div, conversationList.firstChild);
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
    
        aspectList.innerHTML = "";
    
        res.data.forEach(item => {
            const section = item.section;
            const percent = item.percentage;
            const answered = item.answered;
            const total = item.total;
            const color = SECTION_COLORS[section] || "#4caf50";
    
            const div = document.createElement("div");
            div.className = "aspect-item";
    
            div.innerHTML = `
                <div class="aspect-title">${section}</div>
                <div class="progress-count">${answered} / ${total} pertanyaan terjawab</div>
                <div class="progress-bar">
                    <div class="progress-fill"
                         style="width:${percent}%; background:${color}"></div>
                </div>
                <div class="progress-text">${percent}%</div>
            `;
    
            aspectList.appendChild(div);
        });
    }
    

    newChatBtn.addEventListener("click", async () => {
        const existingItems = conversationList.querySelectorAll('.conversation-item').length;
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
        chatDiv.className = "conversation-item active";
        chatDiv.textContent = newTitle;
        chatDiv.onclick = () => loadChat(currentChatId);
        
        conversationList.insertBefore(chatDiv, conversationList.firstChild);

        window.currentGroupId = 0;
        window.currentSection = "Opening";
        window.currentChatId = res.data.chat_id;
        chatWindow.innerHTML = "";
    
        addMessage(res.data.opening_ai_response, "bot");
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
    
    loadUserChats();
    
});


