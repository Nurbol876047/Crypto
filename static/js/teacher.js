// Кнопка «Кездейсоқ кілт жасау» в конструкторе этапов: AJAX-запрос без сохранения,
// результат сразу подставляется в поля формы и показывается новый шифротекст.
(function () {
    const btn = document.getElementById("randomize-btn");
    if (!btn) return;

    btn.addEventListener("click", () => {
        const plaintext = document.getElementById("f-plaintext")?.value || "";
        const alphabet = document.getElementById("f-alphabet")?.value || "kazakh";

        fetch(`/teacher/editor/${window.TEACHER_STAGE}/randomize`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ plaintext, alphabet }),
        })
            .then((r) => r.json())
            .then((data) => {
                if (data.error) {
                    document.getElementById("randomize-preview").textContent = data.error;
                    return;
                }
                const key = data.key;
                if ("shift" in key) document.getElementById("f-shift").value = key.shift;
                if ("keyword" in key) document.getElementById("f-keyword").value = key.keyword;
                if ("p" in key) document.getElementById("f-p").value = key.p;
                if ("q" in key) document.getElementById("f-q").value = key.q;
                if ("e" in key) document.getElementById("f-e").value = key.e;
                document.getElementById("randomize-preview").textContent =
                    "Жаңа шифрмәтін (сақтамас бұрын қарап шығыңыз): " + data.ciphertext;
            });
    });
})();
