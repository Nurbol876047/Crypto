// Встроенный калькулятор SHA-256 на чистом JavaScript (без внешних библиотек
// и без crypto.subtle, чтобы калькулятор работал и при обычном HTTP в локальной сети).

const SHA256_K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

function sha256Rotr(x, n) {
    return (x >>> n) | (x << (32 - n));
}

function sha256Bytes(bytes) {
    const H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
    const l = bytes.length;
    const withPadding = new Uint8Array(((l + 8) >> 6 << 6) + 64);
    withPadding.set(bytes);
    withPadding[l] = 0x80;

    const dv = new DataView(withPadding.buffer);
    const bitLenHi = Math.floor(l / 0x20000000);
    const bitLenLo = (l << 3) >>> 0;
    dv.setUint32(withPadding.length - 8, bitLenHi);
    dv.setUint32(withPadding.length - 4, bitLenLo);

    for (let offset = 0; offset < withPadding.length; offset += 64) {
        const w = new Uint32Array(64);
        for (let i = 0; i < 16; i++) w[i] = dv.getUint32(offset + i * 4);
        for (let i = 16; i < 64; i++) {
            const s0 = sha256Rotr(w[i - 15], 7) ^ sha256Rotr(w[i - 15], 18) ^ (w[i - 15] >>> 3);
            const s1 = sha256Rotr(w[i - 2], 17) ^ sha256Rotr(w[i - 2], 19) ^ (w[i - 2] >>> 10);
            w[i] = (w[i - 16] + s0 + w[i - 7] + s1) >>> 0;
        }
        let [a, b, c, d, e, f, g, h] = H;
        for (let i = 0; i < 64; i++) {
            const S1 = sha256Rotr(e, 6) ^ sha256Rotr(e, 11) ^ sha256Rotr(e, 25);
            const ch = (e & f) ^ (~e & g);
            const temp1 = (h + S1 + ch + SHA256_K[i] + w[i]) >>> 0;
            const S0 = sha256Rotr(a, 2) ^ sha256Rotr(a, 13) ^ sha256Rotr(a, 22);
            const maj = (a & b) ^ (a & c) ^ (b & c);
            const temp2 = (S0 + maj) >>> 0;
            h = g; g = f; f = e; e = (d + temp1) >>> 0;
            d = c; c = b; b = a; a = (temp1 + temp2) >>> 0;
        }
        H[0] = (H[0] + a) >>> 0; H[1] = (H[1] + b) >>> 0; H[2] = (H[2] + c) >>> 0; H[3] = (H[3] + d) >>> 0;
        H[4] = (H[4] + e) >>> 0; H[5] = (H[5] + f) >>> 0; H[6] = (H[6] + g) >>> 0; H[7] = (H[7] + h) >>> 0;
    }
    return H.map((x) => (x >>> 0).toString(16).padStart(8, "0")).join("");
}

function sha256Hex(text) {
    return sha256Bytes(new TextEncoder().encode(text));
}

(function () {
    const refHash = (document.querySelector(".ciphertext-box")?.textContent || "").trim();

    document.querySelectorAll(".hash-calc-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const content = btn.dataset.content;
            const target = document.getElementById(btn.dataset.target);
            const hash = sha256Hex(content);
            target.textContent = hash;
            target.className = "hash-out" + (hash === refHash ? " match" : "");
        });
    });

    const freeBtn = document.getElementById("hash-calc-free-btn");
    if (freeBtn) {
        freeBtn.addEventListener("click", () => {
            const text = document.getElementById("hash-calc-input").value;
            const out = document.getElementById("hash-calc-free-out");
            const hash = sha256Hex(text);
            out.textContent = hash;
            out.className = "hash-out" + (hash === refHash ? " match" : "");
        });
    }
})();
