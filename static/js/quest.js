// Общая логика страницы этапа: отправка ответа, подсказки, блокировка после перебора.
(function () {
    const Q = window.QUEST;
    if (!Q) return;

    const feedbackEl = document.getElementById("feedback");
    const answerInput = document.getElementById("answer-input");
    const submitBtn = document.getElementById("submit-btn");
    const lockBanner = document.getElementById("lock-banner");

    function setLockedUi(seconds) {
        if (answerInput) answerInput.disabled = true;
        if (submitBtn) submitBtn.disabled = true;
        if (lockBanner) {
            lockBanner.style.display = "block";
            startLockCountdown("lock-banner", seconds, () => {
                if (answerInput) answerInput.disabled = false;
                if (submitBtn) submitBtn.disabled = false;
                lockBanner.style.display = "none";
            });
        }
    }

    if (Q.locked && Q.lockSeconds > 0) {
        setLockedUi(Q.lockSeconds);
    }

    if (submitBtn) {
        submitBtn.addEventListener("click", submitAnswer);
        answerInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") submitAnswer();
        });
    }

    function submitAnswer() {
        const answer = answerInput.value;
        if (!answer.trim()) return;
        submitBtn.disabled = true;

        fetch(`/api/stage/${Q.stageNumber}/submit`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ answer: answer }),
        })
            .then((r) => r.json().then((data) => ({ status: r.status, data })))
            .then(({ status, data }) => {
                const counter = document.getElementById("attempts-counter");
                if (counter && typeof data.attempts === "number") counter.textContent = data.attempts;

                if (status === 423 || data.locked) {
                    feedbackEl.textContent = "Көп қате әрекет! Уақытша құлыпталды.";
                    feedbackEl.className = "feedback bad";
                    setLockedUi(data.lock_seconds || 30);
                    return;
                }
                if (data.correct) {
                    feedbackEl.textContent = `Дұрыс! Балл: ${data.score}. Фрагмент: ${data.fragment}`;
                    feedbackEl.className = "feedback ok";
                    answerInput.disabled = true;
                    setTimeout(() => {
                        window.location.href = data.finished ? "/final" : "/bunker";
                    }, 1500);
                } else {
                    feedbackEl.textContent = `Қате жауап. Құлыптаналуға дейін: ${data.attempts_before_lock} әрекет.`;
                    feedbackEl.className = "feedback bad";
                    submitBtn.disabled = false;
                }
            })
            .catch(() => {
                feedbackEl.textContent = "Қате орын алды. Қайталап көріңіз.";
                feedbackEl.className = "feedback bad";
                submitBtn.disabled = false;
            });
    }

    const revealBtn = document.getElementById("reveal-answer-btn");
    if (revealBtn) {
        revealBtn.addEventListener("click", () => {
            revealBtn.disabled = true;
            fetch(`/api/stage/${Q.stageNumber}/answer`, { method: "POST" })
                .then((r) => r.json())
                .then((data) => {
                    const box = document.getElementById("answer-reveal-box");
                    box.innerHTML = "";

                    const label = document.createElement("p");
                    label.className = "answer-reveal-label";
                    label.textContent = "«Жауап» өрісіне дәл осыны жазу керек:";
                    box.appendChild(label);

                    const codeRow = document.createElement("div");
                    codeRow.className = "answer-code-row";

                    const codeBox = document.createElement("div");
                    codeBox.className = "answer-code-box";
                    codeBox.textContent = data.answer;
                    codeRow.appendChild(codeBox);

                    const insertBtn = document.createElement("button");
                    insertBtn.type = "button";
                    insertBtn.className = "btn btn-secondary";
                    insertBtn.textContent = "Өріске қою";
                    insertBtn.addEventListener("click", () => {
                        if (answerInput) {
                            answerInput.value = data.answer;
                            answerInput.focus();
                        }
                    });
                    codeRow.appendChild(insertBtn);

                    box.appendChild(codeRow);

                    const explP = document.createElement("p");
                    explP.className = "explanation";
                    explP.textContent = data.explanation;
                    box.appendChild(explP);

                    if (data.fragment && data.fragment !== data.answer) {
                        const fragP = document.createElement("p");
                        fragP.className = "fragment-note";
                        const fragLabel = document.createElement("strong");
                        fragLabel.textContent = "Бұл есікті шешкенде алатын код фрагменті: ";
                        fragP.appendChild(fragLabel);
                        fragP.appendChild(document.createTextNode(data.fragment));
                        fragP.appendChild(document.createTextNode(" (оны ештеңеге енгізудің қажеті жоқ, ол автоматты түрде беріледі)."));
                        box.appendChild(fragP);
                    }

                    box.style.display = "block";
                })
                .catch(() => {
                    revealBtn.disabled = false;
                });
        });
    }

    document.querySelectorAll(".hint-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const level = parseInt(btn.dataset.level, 10);
            fetch(`/api/stage/${Q.stageNumber}/hint`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ level: level }),
            })
                .then((r) => r.json())
                .then((data) => {
                    if (data.error) return;
                    const container = document.getElementById("hints-container");
                    const div = document.createElement("div");
                    div.className = "hint-text";
                    div.textContent = data.text;
                    container.appendChild(div);
                    btn.disabled = true;
                    const next = document.querySelector(`.hint-btn[data-level="${level + 1}"]`);
                    if (next) next.disabled = false;
                });
        });
    });
})();
