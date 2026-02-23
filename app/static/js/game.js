(function () {
    const POLL_INTERVAL = 3000;
    const container = document.getElementById("game-container");
    if (!container) return;
    const gameId = container.dataset.gameId;

    // ── Tab switching ──────────────────────────────────────────────
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => {
                b.classList.remove("border-brand", "text-brand");
                b.classList.add("border-transparent", "text-gray-500");
            });
            btn.classList.add("border-brand", "text-brand");
            btn.classList.remove("border-transparent", "text-gray-500");

            document.querySelectorAll(".tab-panel").forEach(p => p.classList.add("hidden"));
            document.getElementById(`tab-${btn.dataset.tab}`).classList.remove("hidden");
        });
    });

    // ── Box score sub-tabs ─────────────────────────────────────────
    document.querySelectorAll(".box-tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".box-tab-btn").forEach(b => {
                b.classList.remove("bg-brand", "text-white");
                b.classList.add("bg-white", "text-gray-600");
            });
            btn.classList.add("bg-brand", "text-white");
            btn.classList.remove("bg-white", "text-gray-600");

            document.querySelectorAll(".box-panel").forEach(p => p.classList.add("hidden"));
            document.getElementById(`box-${btn.dataset.box}`).classList.remove("hidden");
        });
    });

    // ── Live polling ───────────────────────────────────────────────
    async function refresh() {
        try {
            const res = await fetch(`/api/game/${gameId}`);
            if (!res.ok) return;
            const data = await res.json();
            const s = data.summary;

            // Update scores
            const homeScore = document.getElementById("home-score");
            const awayScore = document.getElementById("away-score");
            if (homeScore) homeScore.textContent = s.home_score;
            if (awayScore) awayScore.textContent = s.away_score;

            // Update period/clock
            const periodClock = document.getElementById("period-clock");
            if (periodClock && s.status === "live") {
                const periodLabel = s.sport === "ncaamb" ? (s.period === 1 ? "1H" : "2H") : `Q${s.period}`;
                periodClock.textContent = `${periodLabel} ${s.clock}`;
            }

            // Update PBP feed
            const pbpFeed = document.getElementById("pbp-feed");
            if (pbpFeed && data.play_by_play && data.play_by_play.length > 0) {
                let html = "";
                data.play_by_play.forEach(e => {
                    html += `
                    <div class="px-4 py-3 flex items-start gap-3 text-sm">
                        <span class="text-gray-400 tabular-nums whitespace-nowrap w-16 shrink-0">Q${e.period} ${e.clock}</span>
                        <span class="font-semibold text-xs uppercase w-12 shrink-0">${e.team}</span>
                        <span class="flex-1">${e.description}</span>
                        <span class="text-gray-500 tabular-nums whitespace-nowrap">${e.away_score}-${e.home_score}</span>
                    </div>`;
                });
                pbpFeed.innerHTML = html;
            }
        } catch (e) {
            // silent
        }
    }

    setInterval(refresh, POLL_INTERVAL);
})();
