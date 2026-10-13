// Общие вспомогательные функции: таймер и обратный отсчёт блокировки.

function formatDuration(totalSeconds) {
    totalSeconds = Math.max(0, Math.floor(totalSeconds));
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    const pad = (n) => String(n).padStart(2, "0");
    return h > 0 ? `${pad(h)}:${pad(m)}:${pad(s)}` : `${pad(m)}:${pad(s)}`;
}

function startElapsedTimer(elementId, startedAtIso) {
    const el = document.getElementById(elementId);
    if (!el || !startedAtIso) return;
    const startedAt = new Date(startedAtIso + "Z").getTime();
    function tick() {
        const elapsed = (Date.now() - startedAt) / 1000;
        el.textContent = formatDuration(elapsed);
    }
    tick();
    setInterval(tick, 1000);
}

function startLockCountdown(elementId, seconds, onDone) {
    const el = document.getElementById(elementId);
    if (!el) return;
    let remaining = seconds;
    function render() {
        el.textContent = `Құлыптаулы. Қайта көру үшін: ${remaining} сек.`;
    }
    render();
    const interval = setInterval(() => {
        remaining -= 1;
        if (remaining <= 0) {
            clearInterval(interval);
            el.textContent = "";
            if (onDone) onDone();
        } else {
            render();
        }
    }, 1000);
}
