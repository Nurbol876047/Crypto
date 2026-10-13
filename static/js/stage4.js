// Плейфер: проверка кілт сөз и показ построенной таблицы 5x5.
(function () {
    const btn = document.getElementById("playfair-check-btn");
    const input = document.getElementById("playfair-key-input");
    const feedback = document.getElementById("playfair-key-feedback");
    const container = document.getElementById("playfair-table-container");
    if (!btn) return;

    btn.addEventListener("click", () => {
        fetch("/api/stage/4/check-key", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ keyword: input.value }),
        })
            .then((r) => r.json())
            .then((data) => {
                if (!data.ok) {
                    feedback.textContent = "Кілт сөз дұрыс емес.";
                    feedback.className = "feedback bad";
                    container.innerHTML = "";
                    return;
                }
                feedback.textContent = "Кілт сөз дұрыс! Кесте ашылды.";
                feedback.className = "feedback ok";
                renderTable(data.table);
            });
    });

    function renderTable(table) {
        let html = '<table class="playfair-table">';
        table.forEach((row) => {
            html += "<tr>" + row.map((ch) => `<td>${ch}</td>`).join("") + "</tr>";
        });
        html += "</table>";
        container.innerHTML = html;
    }
})();
