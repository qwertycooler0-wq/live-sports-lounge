(function () {
    const POLL_INTERVAL = 5000;
    const sport = new URLSearchParams(window.location.search).get("sport") || "all";

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
                if (homeEl) homeEl.textContent = g.home_score;
                if (awayEl) awayEl.textContent = g.away_score;
            });
        } catch (e) {
            // silent — retry next interval
        }
    }

    setInterval(refresh, POLL_INTERVAL);
})();
