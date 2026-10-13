// RSA калькуляторы: проверка на простоту, НОД, кері элемент (modinverse), m = c^d mod n.
(function () {
    function isPrime(n) {
        if (n < 2) return false;
        if (n === 2 || n === 3) return true;
        if (n % 2 === 0) return false;
        for (let i = 3; i * i <= n; i += 2) {
            if (n % i === 0) return false;
        }
        return true;
    }

    function gcd(a, b) {
        a = Math.abs(a); b = Math.abs(b);
        while (b) { [a, b] = [b, a % b]; }
        return a;
    }

    function extendedGcd(a, b) {
        if (b === 0) return [a, 1, 0];
        const [g, x1, y1] = extendedGcd(b, a % b);
        return [g, y1, x1 - Math.floor(a / b) * y1];
    }

    function modInverse(a, m) {
        const [g, x] = extendedGcd(a, m);
        if (g !== 1) return null;
        return ((x % m) + m) % m;
    }

    function powMod(base, exp, mod) {
        base = BigInt(base); exp = BigInt(exp); mod = BigInt(mod);
        let result = 1n;
        base = base % mod;
        while (exp > 0n) {
            if (exp % 2n === 1n) result = (result * base) % mod;
            exp = exp / 2n;
            base = (base * base) % mod;
        }
        return result.toString();
    }

    document.getElementById("rsa-prime-btn")?.addEventListener("click", () => {
        const n = parseInt(document.getElementById("rsa-prime-input").value, 10);
        document.getElementById("rsa-prime-out").textContent =
            Number.isInteger(n) ? `${n} — ${isPrime(n) ? "жай сан" : "құрама сан"}` : "Санды енгізіңіз";
    });

    document.getElementById("rsa-gcd-btn")?.addEventListener("click", () => {
        const a = parseInt(document.getElementById("rsa-gcd-a").value, 10);
        const b = parseInt(document.getElementById("rsa-gcd-b").value, 10);
        document.getElementById("rsa-gcd-out").textContent =
            (Number.isInteger(a) && Number.isInteger(b)) ? `ЕҮОБ(${a}, ${b}) = ${gcd(a, b)}` : "Екі санды да енгізіңіз";
    });

    document.getElementById("rsa-inv-btn")?.addEventListener("click", () => {
        const a = parseInt(document.getElementById("rsa-inv-a").value, 10);
        const m = parseInt(document.getElementById("rsa-inv-m").value, 10);
        if (!Number.isInteger(a) || !Number.isInteger(m)) {
            document.getElementById("rsa-inv-out").textContent = "Екі санды да енгізіңіз";
            return;
        }
        const inv = modInverse(a, m);
        document.getElementById("rsa-inv-out").textContent =
            inv === null ? "Кері элемент жоқ (ЕҮОБ ≠ 1)" : `${a}⁻¹ mod ${m} = ${inv}`;
    });

    document.getElementById("rsa-pow-btn")?.addEventListener("click", () => {
        const c = document.getElementById("rsa-pow-c").value;
        const d = document.getElementById("rsa-pow-d").value;
        const n = document.getElementById("rsa-pow-n").value;
        if (!c || !d || !n) {
            document.getElementById("rsa-pow-out").textContent = "Үш санды да енгізіңіз";
            return;
        }
        document.getElementById("rsa-pow-out").textContent = `m = ${powMod(c, d, n)}`;
    });
})();
