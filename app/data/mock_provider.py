import random
import time
from .provider import (
    DataProvider, GameSummary, GameDetail, PlayerStats, PlayEvent
)


def _sched(game_id, sport, home, away, start_time):
    """Shorthand to build a scheduled game entry."""
    return {
        "summary_base": GameSummary(
            game_id=game_id, sport=sport, status="scheduled",
            home_team=home, away_team=away,
            home_score=0, away_score=0, period=0, clock="",
            start_time=start_time,
        ),
        "home_players": [],
        "away_players": [],
        "pbp": [],
        "home_team_stats": {},
        "away_team_stats": {},
    }


# ═══════════════════════════════════════════════════════════════════
# TODAY'S GAMES — Monday, February 23, 2026
# ═══════════════════════════════════════════════════════════════════

_GAMES = {
    # ── NBA (3 games) ───────────────────────────────────────────────
    "nba-sas-det-20260223": _sched(
        "nba-sas-det-20260223", "nba",
        "Detroit Pistons", "San Antonio Spurs", "7:00 PM ET",
    ),
    "nba-sac-mem-20260223": _sched(
        "nba-sac-mem-20260223", "nba",
        "Memphis Grizzlies", "Sacramento Kings", "8:00 PM ET",
    ),
    "nba-uta-hou-20260223": _sched(
        "nba-uta-hou-20260223", "nba",
        "Houston Rockets", "Utah Jazz", "9:30 PM ET",
    ),

    # ── NCAAMB — Major conference (2 games) ─────────────────────────
    "ncaamb-lou-unc-20260223": _sched(
        "ncaamb-lou-unc-20260223", "ncaamb",
        "North Carolina Tar Heels", "Louisville Cardinals", "7:00 PM ET",
    ),
    "ncaamb-hou-kan-20260223": _sched(
        "ncaamb-hou-kan-20260223", "ncaamb",
        "Kansas Jayhawks", "Houston Cougars", "9:00 PM ET",
    ),

    # ── NCAAMB — Southland Conference (6 games) ─────────────────────
    "ncaamb-tamucc-sela-20260223": _sched(
        "ncaamb-tamucc-sela-20260223", "ncaamb",
        "SE Louisiana Lions", "Texas A&M-Corpus Christi Islanders", "7:00 PM ET",
    ),
    "ncaamb-nich-lam-20260223": _sched(
        "ncaamb-nich-lam-20260223", "ncaamb",
        "Lamar Cardinals", "Nicholls State Colonels", "7:00 PM ET",
    ),
    "ncaamb-uiw-nwst-20260223": _sched(
        "ncaamb-uiw-nwst-20260223", "ncaamb",
        "Northwestern State Demons", "Incarnate Word Cardinals", "7:30 PM ET",
    ),
    "ncaamb-uno-sfa-20260223": _sched(
        "ncaamb-uno-sfa-20260223", "ncaamb",
        "Stephen F. Austin Lumberjacks", "New Orleans Privateers", "7:30 PM ET",
    ),
    "ncaamb-utrgv-mcn-20260223": _sched(
        "ncaamb-utrgv-mcn-20260223", "ncaamb",
        "McNeese Cowboys", "UT Rio Grande Valley Vaqueros", "7:30 PM ET",
    ),
    "ncaamb-hcu-etamu-20260223": _sched(
        "ncaamb-hcu-etamu-20260223", "ncaamb",
        "East Texas A&M Lions", "Houston Christian Huskies", "7:30 PM ET",
    ),

    # ── NCAAMB — SWAC (1 game) ──────────────────────────────────────
    "ncaamb-mvsu-gram-20260223": _sched(
        "ncaamb-mvsu-gram-20260223", "ncaamb",
        "Grambling State Tigers", "Mississippi Valley State Delta Devils", "8:00 PM ET",
    ),
}


# ── Simulated clock drift for live games ────────────────────────────
_CLOCK_BASE = time.time()


def _simulated_clock(base_clock: str, period: int) -> tuple[str, int]:
    """Drift the clock down slowly so the site looks alive."""
    elapsed = (time.time() - _CLOCK_BASE) % 300
    parts = base_clock.split(":")
    if len(parts) != 2:
        return base_clock, period
    mins, secs = int(parts[0]), int(parts[1])
    total = mins * 60 + secs
    total = max(0, total - int(elapsed))
    return f"{total // 60}:{total % 60:02d}", period


def _jitter_score(base: int) -> int:
    """Tiny random jitter so scores feel alive between polls."""
    return base + random.choice([0, 0, 0, 0, 0, 0, 0, 0, 0, 1])


class MockProvider(DataProvider):

    async def get_scoreboard(self, sport: str = "all") -> list[GameSummary]:
        results = []
        for g in _GAMES.values():
            base = g["summary_base"]
            if sport != "all" and base.sport != sport:
                continue
            s = GameSummary(
                game_id=base.game_id,
                sport=base.sport,
                status=base.status,
                home_team=base.home_team,
                away_team=base.away_team,
                home_score=_jitter_score(base.home_score) if base.status == "live" else base.home_score,
                away_score=_jitter_score(base.away_score) if base.status == "live" else base.away_score,
                period=base.period,
                clock=_simulated_clock(base.clock, base.period)[0] if base.status == "live" else base.clock,
                start_time=base.start_time,
            )
            results.append(s)
        return results

    async def get_game(self, game_id: str) -> GameDetail | None:
        g = _GAMES.get(game_id)
        if not g:
            return None
        base = g["summary_base"]
        clock = _simulated_clock(base.clock, base.period)[0] if base.status == "live" else base.clock
        summary = GameSummary(
            game_id=base.game_id,
            sport=base.sport,
            status=base.status,
            home_team=base.home_team,
            away_team=base.away_team,
            home_score=_jitter_score(base.home_score) if base.status == "live" else base.home_score,
            away_score=_jitter_score(base.away_score) if base.status == "live" else base.away_score,
            period=base.period,
            clock=clock,
            start_time=base.start_time,
        )
        return GameDetail(
            summary=summary,
            home_players=g["home_players"],
            away_players=g["away_players"],
            play_by_play=g["pbp"],
            home_team_stats=g["home_team_stats"],
            away_team_stats=g["away_team_stats"],
        )

    async def get_play_by_play(self, game_id: str) -> list[PlayEvent]:
        g = _GAMES.get(game_id)
        return g["pbp"] if g else []
