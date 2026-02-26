(function () {
    const POLL_INTERVAL = 5000;
    const RECONNECT_DELAY = 3000;
    const sport = new URLSearchParams(window.location.search).get("sport") || "all";

    // Track previous scores for flash detection
    const prevScores = {};
    let pollTimer = null;
    let ws = null;
    let wsConnected = false;

    // ── Shared update logic (used by both WS and HTTP) ───────────

    function updateScoreboard(games) {
        games.forEach(g => {
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
    }

    // ── HTTP polling (fallback) ──────────────────────────────────

    async function refresh() {
        try {
            const res = await fetch(`/api/scoreboard?sport=${sport}`);
            if (!res.ok) return;
            const data = await res.json();
            updateScoreboard(data.games);
        } catch (e) {
            // silent — retry next interval
        }
    }

    function startPolling() {
        if (pollTimer) return;
        pollTimer = setInterval(refresh, POLL_INTERVAL);
    }

    function stopPolling() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    // ── WebSocket connection ─────────────────────────────────────

    function connectWS() {
        const proto = location.protocol === "https:" ? "wss:" : "ws:";
        ws = new WebSocket(`${proto}//${location.host}/ws/live`);

        ws.onopen = function () {
            wsConnected = true;
            stopPolling();
            ws.send(JSON.stringify({ type: "subscribe", topic: "scoreboard" }));
        };

        ws.onmessage = function (evt) {
            try {
                const msg = JSON.parse(evt.data);
                if (msg.type === "scoreboard" && msg.games) {
                    updateScoreboard(msg.games);
                }
            } catch (e) {
                // ignore parse errors
            }
        };

        ws.onclose = function () {
            wsConnected = false;
            ws = null;
            startPolling();
            setTimeout(connectWS, RECONNECT_DELAY);
        };

        ws.onerror = function () {
            // onclose will fire after this
        };
    }

    // ── Initialize: HTTP for immediate data, WS for real-time ────

    refresh();
    startPolling();
    connectWS();
})();
