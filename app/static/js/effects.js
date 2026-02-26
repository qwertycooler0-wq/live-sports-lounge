/* ── Scoring Effects Engine ─────────────────────────────────────── */
const effects = (function () {

    function screenFlash(color) {
        const el = document.getElementById('screen-flash');
        if (!el) return;
        el.style.setProperty('--flash-color', color);
        el.style.animation = 'none';
        void el.offsetWidth;
        el.style.animation = 'edgeFlash 0.6s ease-out forwards';
    }

    function confetti() {
        const container = document.getElementById('confetti-container');
        if (!container) return;
        const colors = ['#f59e0b', '#e8611a', '#3b82f6', '#ef4444', '#22c55e', '#a855f7'];
        for (let i = 0; i < 30; i++) {
            const piece = document.createElement('div');
            piece.className = 'confetti-piece';
            piece.style.left = Math.random() * 100 + '%';
            piece.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            piece.style.animationDelay = (Math.random() * 0.5) + 's';
            piece.style.animationDuration = (1.5 + Math.random()) + 's';
            container.appendChild(piece);
        }
        setTimeout(() => {
            container.querySelectorAll('.confetti-piece').forEach(p => p.remove());
        }, 2500);
    }

    function shakeElement(el) {
        if (!el) return;
        el.classList.remove('score-shake');
        void el.offsetWidth;
        el.classList.add('score-shake');
        setTimeout(() => el.classList.remove('score-shake'), 500);
    }

    function showRunBanner(text, color) {
        const banner = document.getElementById('run-banner');
        const textEl = document.getElementById('run-text');
        if (!banner || !textEl) return;
        textEl.textContent = text;
        banner.style.borderColor = color || '#e8611a';
        banner.classList.remove('hidden');
        banner.style.animation = 'slideDown 0.4s ease-out forwards';
        setTimeout(() => {
            banner.style.animation = 'slideUp 0.4s ease-in forwards';
            setTimeout(() => banner.classList.add('hidden'), 400);
        }, 3000);
    }

    function clutchMode(enable) {
        const hero = document.querySelector('.hardwood');
        if (!hero) return;
        if (enable) {
            hero.classList.add('clutch-mode');
        } else {
            hero.classList.remove('clutch-mode');
        }
    }

    return { screenFlash, confetti, shakeElement, showRunBanner, clutchMode };
})();
