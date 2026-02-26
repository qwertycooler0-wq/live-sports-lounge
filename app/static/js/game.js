(function () {
    const POLL_INTERVAL = 3000;
    const RECONNECT_DELAY = 3000;
    const container = document.getElementById("game-container");
    if (!container) return;
    const gameId = container.dataset.gameId;
    const gameSport = container.dataset.sport;

    let prevHome = null;
    let prevAway = null;
    let prevPeriod = null;
    let lastEventId = -1;
    let runTracker = { team: null, points: 0 };
    let momentumEvents = []; // { team, points, time }
    let pollTimer = null;
    let ws = null;
    let wsConnected = false;

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

    // ── Play type classification for PBP highlights ────────────────
    function classifyPlay(desc) {
        if (!desc) return '';
        const d = desc.toLowerCase();
        if (/three|3pt|3-point/.test(d)) return 'pbp-three';
        if (/dunk|slam/.test(d)) return 'pbp-dunk';
        if (/block/.test(d)) return 'pbp-block';
        if (/steal/.test(d)) return 'pbp-steal';
        return '';
    }

    // ── Clock parsing ──────────────────────────────────────────────
    function parseClockToSeconds(clock) {
        if (!clock) return 999;
        const parts = clock.split(':');
        if (parts.length === 2) {
            return parseInt(parts[0]) * 60 + parseFloat(parts[1]);
        }
        return parseFloat(clock) || 999;
    }

    // ── Clutch detection ───────────────────────────────────────────
    function checkClutch(period, clock, homeScore, awayScore, status) {
        if (status !== 'live') { effects.clutchMode(false); return; }
        const isFinalPeriod = gameSport === 'ncaamb' ? period >= 2 : period >= 4;
        const clockSecs = parseClockToSeconds(clock);
        const diff = Math.abs(homeScore - awayScore);
        effects.clutchMode(isFinalPeriod && clockSecs <= 120 && diff <= 10);
    }

    // ── Dynamic background ─────────────────────────────────────────
    function updateAtmosphere(homeScore, awayScore, status) {
        const diff = Math.abs(homeScore - awayScore);
        if (diff <= 5 && status === 'live') {
            container.style.setProperty('--bg-intensity', '0.15');
            container.style.setProperty('--bg-hue', '0');
        } else if (diff >= 20) {
            container.style.setProperty('--bg-intensity', '0.03');
            container.style.setProperty('--bg-hue', '220');
        } else {
            container.style.setProperty('--bg-intensity', '0.08');
            container.style.setProperty('--bg-hue', '220');
        }
    }

    // ── Momentum calculation ───────────────────────────────────────
    function updateMomentum(team, points) {
        const now = Date.now();
        momentumEvents.push({ team, points, time: now });
        // Keep only last 2 minutes of events
        const cutoff = now - 120000;
        momentumEvents = momentumEvents.filter(e => e.time > cutoff);

        let homePoints = 0, awayPoints = 0;

        momentumEvents.forEach(e => {
            if (e.team === 'home') homePoints += e.points;
            else awayPoints += e.points;
        });

        const total = homePoints + awayPoints;
        const dot = document.getElementById('momentum-dot');
        if (dot && total > 0) {
            const pct = (homePoints / total) * 100;
            dot.style.left = pct + '%';
        }
    }

    // ── Pulse timeline ─────────────────────────────────────────────
    function buildPulseTimeline(pbpEvents) {
        const timeline = document.getElementById('pulse-timeline');
        if (!timeline || !pbpEvents || pbpEvents.length === 0) return;

        // Group scoring events into time buckets by period+minute
        const buckets = {};
        pbpEvents.forEach(e => {
            if (!isScoringPlay(e.description)) return;
            const clockSecs = parseClockToSeconds(e.clock);
            const minute = Math.floor(clockSecs / 60);
            const key = `${e.period}-${minute}`;
            if (!buckets[key]) buckets[key] = { home: 0, away: 0 };
            const pts = /three|3pt|3-point/i.test(e.description) ? 3
                : /free throw/i.test(e.description) ? 1 : 2;
            if (e.home_score > (buckets[key]._lastHome || 0)) {
                buckets[key].home += pts;
            } else {
                buckets[key].away += pts;
            }
            buckets[key]._lastHome = e.home_score;
        });

        const keys = Object.keys(buckets).sort();
        if (keys.length === 0) return;

        const maxPts = Math.max(...keys.map(k => buckets[k].home + buckets[k].away), 1);
        timeline.innerHTML = '';

        keys.forEach(k => {
            const b = buckets[k];
            const total = b.home + b.away;
            const heightPct = Math.max((total / maxPts) * 100, 8);
            const homeRatio = total > 0 ? b.home / total : 0.5;

            const bar = document.createElement('div');
            bar.className = 'pulse-bar flex-1';
            bar.style.height = heightPct + '%';

            const r = Math.round(239 * (1 - homeRatio) + 59 * homeRatio);
            const g = Math.round(68 * (1 - homeRatio) + 130 * homeRatio);
            const bl = Math.round(68 * (1 - homeRatio) + 246 * homeRatio);
            bar.style.backgroundColor = `rgb(${r}, ${g}, ${bl})`;
            bar.style.opacity = '0.7';

            timeline.appendChild(bar);
        });
    }

    // ── Score change effects ───────────────────────────────────────
    function handleScoreChange(side, delta, desc) {
        const color = side === 'home' ? '#3b82f6' : '#ef4444';
        effects.screenFlash(color);
        effects.shakeElement(document.getElementById(side === 'home' ? 'home-score' : 'away-score'));

        if (typeof gameAudio !== 'undefined') {
            gameAudio.crowdRoar(delta >= 3 ? 1.0 : 0.5);
        }

        if (delta >= 3) {
            effects.confetti();
        }

        // Run tracking
        if (runTracker.team === side) {
            runTracker.points += delta;
        } else {
            runTracker.team = side;
            runTracker.points = delta;
        }
        if (runTracker.points >= 6) {
            effects.showRunBanner(`${runTracker.points}-0 RUN!`, color);
        }

        // Momentum
        updateMomentum(side, delta);
    }

    // ── PBP sound effects ──────────────────────────────────────────
    function pbpSoundEffect(desc) {
        if (typeof gameAudio === 'undefined') return;
        const d = (desc || '').toLowerCase();
        if (d.includes('block') || d.includes('steal')) {
            gameAudio.crowdGasp();
        }
    }

    // ── Shared game data handler (used by both WS and HTTP) ───────

    function handleGameData(data) {
        const s = data.summary;

        // Update scores with flash + effects
        const homeScore = document.getElementById("home-score");
        const awayScore = document.getElementById("away-score");

        const homeDelta = (prevHome !== null) ? (s.home_score - prevHome) : 0;
        const awayDelta = (prevAway !== null) ? (s.away_score - prevAway) : 0;

        if (homeScore) {
            if (prevHome !== null && homeDelta > 0) {
                homeScore.classList.remove("score-flash");
                void homeScore.offsetWidth;
                homeScore.classList.add("score-flash");
                handleScoreChange('home', homeDelta);
            }
            homeScore.textContent = s.home_score;
        }
        if (awayScore) {
            if (prevAway !== null && awayDelta > 0) {
                awayScore.classList.remove("score-flash");
                void awayScore.offsetWidth;
                awayScore.classList.add("score-flash");
                handleScoreChange('away', awayDelta);
            }
            awayScore.textContent = s.away_score;
        }

        prevHome = s.home_score;
        prevAway = s.away_score;

        // Period change → buzzer
        if (prevPeriod !== null && s.period !== prevPeriod && typeof gameAudio !== 'undefined') {
            gameAudio.buzzer();
        }
        prevPeriod = s.period;

        // Update period/clock
        const periodClock = document.getElementById("period-clock");
        if (periodClock && s.status === "live") {
            const periodLabel = gameSport === "ncaamb"
                ? (s.period === 1 ? "1H" : "2H")
                : `Q${s.period}`;
            periodClock.textContent = `${periodLabel} ${s.clock}`;
        }

        // Clutch detection
        checkClutch(s.period, s.clock, s.home_score, s.away_score, s.status);

        // Dynamic background
        updateAtmosphere(s.home_score, s.away_score, s.status);

        // Update PBP feed (incremental)
        const pbpFeed = document.getElementById("pbp-feed");
        if (pbpFeed && data.play_by_play && data.play_by_play.length > 0) {
            const newEvents = data.play_by_play.filter(e => e.event_id > lastEventId);

            if (newEvents.length > 0 && lastEventId >= 0) {
                const fragment = document.createDocumentFragment();
                newEvents.forEach(e => {
                    const scoring = isScoringPlay(e.description) ? "scoring-play" : "";
                    const playType = classifyPlay(e.description);
                    const div = document.createElement('div');
                    div.className = `px-4 py-3 flex items-start gap-3 text-sm pbp-new ${scoring} ${playType}`;
                    div.innerHTML = `
                        <span class="text-gray-500 font-mono text-xs whitespace-nowrap w-16 shrink-0 pt-0.5">Q${e.period} ${e.clock}</span>
                        <span class="font-bold text-xs uppercase w-12 shrink-0 pt-0.5">${e.team}</span>
                        <span class="flex-1 text-gray-300">${e.description}</span>
                        <span class="text-gray-500 font-mono text-xs whitespace-nowrap pt-0.5">${e.away_score}-${e.home_score}</span>`;
                    fragment.appendChild(div);
                    pbpSoundEffect(e.description);
                });
                pbpFeed.insertBefore(fragment, pbpFeed.firstChild);
            } else if (lastEventId < 0) {
                let html = "";
                data.play_by_play.forEach(e => {
                    const scoring = isScoringPlay(e.description) ? "scoring-play" : "";
                    const playType = classifyPlay(e.description);
                    html += `
                    <div class="px-4 py-3 flex items-start gap-3 text-sm ${scoring} ${playType}">
                        <span class="text-gray-500 font-mono text-xs whitespace-nowrap w-16 shrink-0 pt-0.5">Q${e.period} ${e.clock}</span>
                        <span class="font-bold text-xs uppercase w-12 shrink-0 pt-0.5">${e.team}</span>
                        <span class="flex-1 text-gray-300">${e.description}</span>
                        <span class="text-gray-500 font-mono text-xs whitespace-nowrap pt-0.5">${e.away_score}-${e.home_score}</span>
                    </div>`;
                });
                pbpFeed.innerHTML = html;
            }

            const maxId = Math.max(...data.play_by_play.map(e => e.event_id));
            if (maxId > lastEventId) lastEventId = maxId;

            buildPulseTimeline(data.play_by_play);
        }
    }

    // ── HTTP polling (fallback) ──────────────────────────────────

    async function refresh() {
        try {
            const res = await fetch(`/api/game/${gameId}`);
            if (!res.ok) return;
            const data = await res.json();
            handleGameData(data);
        } catch (e) {
            // silent
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
            ws.send(JSON.stringify({ type: "subscribe", topic: `game:${gameId}` }));
        };

        ws.onmessage = function (evt) {
            try {
                const msg = JSON.parse(evt.data);
                if (msg.type === "game_update" && msg.game_id === gameId && msg.data) {
                    handleGameData(msg.data);
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
