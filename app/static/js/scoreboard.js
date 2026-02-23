(function () {
    const POLL_INTERVAL = 5000;
    const sport = new URLSearchParams(window.location.search).get("sport") || "all";

    // Track previous scores for flash detection
    const prevScores = {};

    async function refresh() {
        try {
            const res = await fetch(`/api/scoreboard?sport=${sport}`);
            if (!res.ok) return;
            const data = await res.json();

            data.games.forEach(g => {
                const card = document.querySelector(`.game-card[data-game-id="${g.game_id}"]`);
                if (!card) return;

                const homeEl = card.querySelector(".home-score");
                const awayEl = card.querySelector(".away-score");
                const statusEl = card.querySelector(".status-text");

                const key = g.game_id;
                const prev = prevScores[key] || {};

                // Flash animation on score change
                if (homeEl) {
                    if (prev.home !== undefined && prev.home !== g.home_score) {
                        homeEl.classList.remove("score-flash");
                        void homeEl.offsetWidth; // force reflow
                        homeEl.classList.add("score-flash");
                    }
                    homeEl.textContent = g.home_score;
                }
                if (awayEl) {
                    if (prev.away !== undefined && prev.away !== g.away_score) {
                        awayEl.classList.remove("score-flash");
                        void awayEl.offsetWidth;
                        awayEl.classList.add("score-flash");
                    }
                    awayEl.textContent = g.away_score;
                }

                // Update status/period/clock text
                if (statusEl && g.status === "live") {
                    const periodLabel = g.sport === "ncaamb"
                        ? (g.period === 1 ? "1H" : "2H")
                        : `Q${g.period}`;
                    statusEl.textContent = `${periodLabel} ${g.clock}`;
                }

                prevScores[key] = { home: g.home_score, away: g.away_score };
            });
        } catch (e) {
            // silent — retry next interval
        }
    }

    setInterval(refresh, POLL_INTERVAL);
})();
