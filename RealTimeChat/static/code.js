(function () {

    const app = document.querySelector(".app");
    const socket = io();

    let uname;

    document.getElementById("clear-history").addEventListener("click", () => {
        const token = window.localStorage.getItem("adminToken") || "";
        const headers = token ? { "X-Admin-Token": token } : {};
        fetch("/clear", { method: "POST", headers })
            .then(async (res) => {
                if (res.status === 403) {
                    const t = prompt("Admin token required to clear history:");
                    if (t && t.trim()) {
                        window.localStorage.setItem("adminToken", t.trim());
                        return fetch("/clear", { method: "POST", headers: { "X-Admin-Token": t.trim() } });
                    }
                }
                return res;
            })
            .then(() => location.reload());
    });

    app.querySelector(".join-screen #username")
        .addEventListener("keyup", e => {
            if (e.key === "Enter") {
                app.querySelector(".join-screen #join-user").click();
            }
        });

    app.querySelector(".chat-screen #message-input")
        .addEventListener("keyup", e => {
            if (e.key === "Enter") {
                app.querySelector(".chat-screen #send-message").click();
            }
        });

    app.querySelector(".join-screen #join-user").addEventListener("click", async function () {
        let username = app.querySelector(".join-screen #username").value.trim();
        if (username.length === 0) {
            return;
        }

        uname = username;

        const response = await fetch("/history");
        const history = await response.json();

        history.forEach(message => {
            renderMessage(
                message.username === uname ? "my" : "other",
                message
            );
        });

        socket.emit("newuser", username);

        app.querySelector(".join-screen").classList.remove("active");
        app.querySelector(".chat-screen").classList.add("active");
    });

    const msgInput = app.querySelector(".chat-screen #message-input");
    let typingTimer;

    msgInput.addEventListener("input", () => {
        if (!uname) return;
        socket.emit("typing", { username: uname, typing: true });
        clearTimeout(typingTimer);
        typingTimer = setTimeout(() => {
            socket.emit("typing", { username: uname, typing: false });
        }, 6000);
    });

    msgInput.addEventListener("blur", () => {
        if (uname) socket.emit("typing", { username: uname, typing: false });
    });

    app.querySelector(".chat-screen #send-message").addEventListener("click", function () {
        let message = app.querySelector(".chat-screen #message-input").value;
        if (message.length === 0) {
            return;
        }
        socket.emit("chat", {
            username: uname,
            text: message
        });
        socket.emit("typing", { username: uname, typing: false });
        app.querySelector(".chat-screen #message-input").value = "";
    });

    app.querySelector(".chat-screen #exit-chat").addEventListener("click", function () {
        socket.emit("exituser", uname);
        window.location.href = window.location.href;
    });


    socket.on("update", function (update) {
        renderMessage("update", update);
    });

    socket.on("chat", function (message) {
        renderMessage(
            message.username === uname ? "my" : "other",
            message
        );
    });

    socket.on("typing", function (data) {
        if (data.username === uname) return;
        let msgBox = app.querySelector(".chat-screen .messages");
        let id = "typing-" + data.username.replace(/\W/g, "");
        let el = document.getElementById(id);
        if (data.typing) {
            if (!el) {
                el = document.createElement("div");
                el.id = id;
                el.setAttribute("class", "update typing");
                el.innerText = `${data.username} is typing…`;
                msgBox.appendChild(el);
                msgBox.scrollTop = msgBox.scrollHeight - msgBox.clientHeight;
            }
        } else {
            if (el) el.remove();
        }
    });

    socket.on("history", function (msgs) {
        msgs.forEach(m => {
            const type = (m.username === uname) ? "my" : "other";
            renderMessage(type, m);
        });
    });


    function renderMessage(type, message) {
        let messageContainer = app.querySelector(".chat-screen .messages");

        if (type === "my" || type === "other") {
            let el = document.createElement("div");
            el.classList.add("message");
            el.classList.add(type === "my" ? "my-message" : "other-message");

            let inner = document.createElement("div");

            let nameDiv = document.createElement("div");
            nameDiv.classList.add("name");
            nameDiv.innerText = (type === "my") ? "You" : message.username;

            let textDiv = document.createElement("div");
            textDiv.classList.add("text");
            textDiv.innerText = message.text;

            inner.appendChild(nameDiv);
            inner.appendChild(textDiv);
            el.appendChild(inner);
            messageContainer.appendChild(el);
        } else if (type === "update") {
            let el = document.createElement("div");
            el.setAttribute("class", "update");
            el.innerText = message === `${uname} joined` ? "You joined" : message;
            messageContainer.appendChild(el);
        }

        messageContainer.scrollTop = messageContainer.scrollHeight - messageContainer.clientHeight;
    }

})();