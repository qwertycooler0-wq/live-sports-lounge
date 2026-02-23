(function () {
    const POLL_INTERVAL = 3000;
    const container = document.getElementById("game-container");
    if (!container) return;
    const gameId = container.dataset.gameId;
    const gameSport = container.dataset.sport;

    let prevHome = null;
    let prevAway = null;

    // ── Tab switching ──────────────────────────────────────────────
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => {
                b.classList.remove("bg-surface-lighter", "text-white");
                b.classList.add("text-gray-500");
            });
            btn.classList.add("bg-surface-lighter", "text-white");
            btn.classList.remove("text-gray-500");

            document.querySelectorAll(".tab-panel").forEach(p => p.classList.add("hidden"));
            document.getElementById(`tab-${btn.dataset.tab}`).classList.remove("hidden");
        });
    });

    // ── Box score sub-tabs ─────────────────────────────────────────
    document.querySelectorAll(".box-tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".box-tab-btn").forEach(b => {
                b.classList.remove("bg-accent", "text-dark");
                b.classList.add("bg-surface-light", "text-gray-400");
            });
            btn.classList.add("bg-accent", "text-dark");
            btn.classList.remove("bg-surface-light", "text-gray-400");

            document.querySelectorAll(".box-panel").forEach(p => p.classList.add("hidden"));
            document.getElementById(`box-${btn.dataset.box}`).classList.remove("hidden");
        });
    });

    // ── Scoring play detection ─────────────────────────────────────
    function isScoringPlay(desc) {
        if (!desc) return false;
        const d = desc.toLowerCase();
        return d.includes("point") || d.includes("dunk") || d.includes("layup")
            || d.includes("three") || d.includes("3pt") || d.includes("free throw")
            || d.includes("jumper") || d.includes("hook") || d.includes("tip");
    }

    // ── Live polling ───────────────────────────────────────────────
    async function refresh() {
        try {
            const res = await fetch(`/api/game/${gameId}`);
            if (!res.ok) return;
            const data = await res.json();
            const s = data.summary;

            // Update scores with flash
            const homeScore = document.getElementById("home-score");
            const awayScore = document.getElementById("away-score");

            if (homeScore) {
                if (prevHome !== null && prevHome !== s.home_score) {
                    homeScore.classList.remove("score-flash");
                    void homeScore.offsetWidth;
                    homeScore.classList.add("score-flash");
                }
                homeScore.textContent = s.home_score;
                prevHome = s.home_score;
            }
            if (awayScore) {
                if (prevAway !== null && prevAway !== s.away_score) {
                    awayScore.classList.remove("score-flash");
                    void awayScore.offsetWidth;
                    awayScore.classList.add("score-flash");
                }
                awayScore.textContent = s.away_score;
                prevAway = s.away_score;
            }

            // Update period/clock
            const periodClock = document.getElementById("period-clock");
            if (periodClock && s.status === "live") {
                const periodLabel = gameSport === "ncaamb"
                    ? (s.period === 1 ? "1H" : "2H")
                    : `Q${s.period}`;
                periodClock.textContent = `${periodLabel} ${s.clock}`;
            }

            // Update PBP feed
            const pbpFeed = document.getElementById("pbp-feed");
            if (pbpFeed && data.play_by_play && data.play_by_play.length > 0) {
                let html = "";
                data.play_by_play.forEach(e => {
                    const scoring = isScoringPlay(e.description) ? "scoring-play" : "";
                    html += `
                    <div class="px-4 py-3 flex items-start gap-3 text-sm ${scoring}">
                        <span class="text-gray-500 font-mono text-xs whitespace-nowrap w-16 shrink-0 pt-0.5">Q${e.period} ${e.clock}</span>
                        <span class="font-bold text-xs uppercase w-12 shrink-0 pt-0.5">${e.team}</span>
                        <span class="flex-1 text-gray-300">${e.description}</span>
                        <span class="text-gray-500 font-mono text-xs whitespace-nowrap pt-0.5">${e.away_score}-${e.home_score}</span>
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
