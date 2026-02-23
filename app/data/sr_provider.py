"""SportRadar DataProvider implementation.

Reads from sr_cache, maps SR JSON → our data models.
Handles both NBA (4 quarters) and NCAAMB (2 halves) period structures.
"""

from datetime import datetime, timezone

from .provider import DataProvider, GameSummary, GameDetail, PlayerStats, PlayEvent
from .sr_cache import cache


# SR status → our status
_STATUS_MAP = {
    "scheduled": "scheduled",
    "created": "scheduled",
    "time-tbd": "scheduled",
    "inprogress": "live",
    "halftime": "live",
    "complete": "final",
    "closed": "final",
    "cancelled": "final",
    "postponed": "scheduled",
    "unnecessary": "final",
}


def _map_status(sr_status: str) -> str:
    return _STATUS_MAP.get(sr_status, "scheduled")


def _format_start_time(iso_str: str) -> str:
    """Convert ISO datetime to '7:00 PM ET' style."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        # Convert UTC to ET (UTC-5)
        from datetime import timedelta
        et = dt - timedelta(hours=5)
        hour = et.hour % 12 or 12
        am_pm = "PM" if et.hour >= 12 else "AM"
        return f"{hour}:{et.minute:02d} {am_pm} ET"
    except (ValueError, AttributeError):
        return iso_str or ""


def _get_period_and_clock(game: dict) -> tuple[int, str]:
    """Extract current period and clock from SR game data."""
    clock = game.get("clock", "")
    # Period info might be in different places
    period = 0
    quarter = game.get("quarter", 0)
    half = game.get("half", 0)
    if quarter:
        period = quarter
    elif half:
        period = half
    # Fallback: check periods array
    if not period:
        periods = game.get("periods", [])
        if periods:
            period = len(periods)
    return period, clock or ""


def _game_sport(game_id: str) -> str:
    """Determine sport by checking which schedule contains this game."""
    for sport in cache.schedules:
        entry = cache.schedules[sport]
        for g in entry.data.get("games", []):
            if g.get("id") == game_id:
                return sport
    return "nba"


class SRProvider(DataProvider):

    async def get_scoreboard(self, sport: str = "all") -> list[GameSummary]:
        results = []
        sports = [sport] if sport != "all" else list(cache.schedules.keys())

        for sp in sports:
            schedule = cache.get_schedule(sp)
            if not schedule:
                continue
            for game in schedule.get("games", []):
                gid = game.get("id", "")
                sr_status = game.get("status", "scheduled")
                our_status = _map_status(sr_status)

                # Try to get richer data from summary cache
                summary = cache.get_summary(gid)
                if summary:
                    home_score, away_score, period, clock = self._scores_from_summary(summary)
                    # Update status from summary if available
                    sum_status = summary.get("status", sr_status)
                    our_status = _map_status(sum_status)
                else:
                    home_score = game.get("home_points", 0) or 0
                    away_score = game.get("away_points", 0) or 0
                    period, clock = _get_period_and_clock(game)

                home_team = game.get("home", {}).get("name", "TBD")
                away_team = game.get("away", {}).get("name", "TBD")
                start_time = _format_start_time(game.get("scheduled", ""))

                results.append(GameSummary(
                    game_id=gid,
                    sport=sp,
                    status=our_status,
                    home_team=home_team,
                    away_team=away_team,
                    home_score=home_score,
                    away_score=away_score,
                    period=period,
                    clock=clock,
                    start_time=start_time,
                ))
        return results

    async def get_game(self, game_id: str) -> GameDetail | None:
        # Signal that we want PBP for this game (demand-driven)
        cache.request_pbp(game_id)

        # Build summary from schedule + summary cache
        game_data = self._find_game_in_schedule(game_id)
        if not game_data:
            return None

        sport, sched_game = game_data
        summary_data = cache.get_summary(game_id)

        sr_status = (summary_data or sched_game).get("status", "scheduled")
        our_status = _map_status(sr_status)

        if summary_data:
            home_score, away_score, period, clock = self._scores_from_summary(summary_data)
        else:
            home_score = sched_game.get("home_points", 0) or 0
            away_score = sched_game.get("away_points", 0) or 0
            period, clock = _get_period_and_clock(sched_game)

        home_team = sched_game.get("home", {}).get("name", "TBD")
        away_team = sched_game.get("away", {}).get("name", "TBD")
        start_time = _format_start_time(sched_game.get("scheduled", ""))

        summary = GameSummary(
            game_id=game_id,
            sport=sport,
            status=our_status,
            home_team=home_team,
            away_team=away_team,
            home_score=home_score,
            away_score=away_score,
            period=period,
            clock=clock,
            start_time=start_time,
        )

        # Extract players from summary
        home_players, away_players = self._extract_players(summary_data) if summary_data else ([], [])

        # Extract PBP
        pbp_data = cache.get_pbp_data(game_id)
        play_by_play = self._extract_pbp(pbp_data, sport) if pbp_data else []

        # Extract team stats
        home_stats, away_stats = self._extract_team_stats(summary_data) if summary_data else ({}, {})

        return GameDetail(
            summary=summary,
            home_players=home_players,
            away_players=away_players,
            play_by_play=play_by_play,
            home_team_stats=home_stats,
            away_team_stats=away_stats,
        )

    async def get_play_by_play(self, game_id: str) -> list[PlayEvent]:
        cache.request_pbp(game_id)
        pbp_data = cache.get_pbp_data(game_id)
        if not pbp_data:
            return []
        sport = _game_sport(game_id)
        return self._extract_pbp(pbp_data, sport)

    # ── Internal helpers ────────────────────────────────────────────

    def _find_game_in_schedule(self, game_id: str) -> tuple[str, dict] | None:
        for sport, entry in cache.schedules.items():
            for game in entry.data.get("games", []):
                if game.get("id") == game_id:
                    return sport, game
        return None

    @staticmethod
    def _scores_from_summary(summary: dict) -> tuple[int, int, int, str]:
        """Extract scores, period, clock from a SR game summary."""
        home = summary.get("home", {})
        away = summary.get("away", {})
        home_score = home.get("points", 0) or 0
        away_score = away.get("points", 0) or 0
        clock = summary.get("clock", "")
        period = summary.get("quarter", 0) or summary.get("half", 0) or 0
        # Check periods for more accurate period count
        periods = summary.get("periods", [])
        if periods and not period:
            period = len(periods)
        return home_score, away_score, period, clock or ""

    @staticmethod
    def _extract_players(summary: dict) -> tuple[list[PlayerStats], list[PlayerStats]]:
        """Extract player stats from SR summary."""
        home_players = []
        away_players = []

        for side, dest in [("home", home_players), ("away", away_players)]:
            team = summary.get(side, {})
            players = team.get("players", [])
            for p in players:
                stats = p.get("statistics", {})
                if not stats:
                    continue
                # Only include players who have minutes
                minutes = stats.get("minutes", "")
                if not minutes and not stats.get("field_goals_made"):
                    continue
                dest.append(PlayerStats(
                    name=p.get("full_name", p.get("name", "Unknown")),
                    position=p.get("position", p.get("primary_position", "")),
                    minutes=minutes or "0:00",
                    points=stats.get("points", 0) or 0,
                    rebounds=stats.get("rebounds", 0) or 0,
                    assists=stats.get("assists", 0) or 0,
                    steals=stats.get("steals", 0) or 0,
                    blocks=stats.get("blocks", 0) or 0,
                    fg=f"{stats.get('field_goals_made', 0)}-{stats.get('field_goals_att', 0)}",
                    three_pt=f"{stats.get('three_points_made', 0)}-{stats.get('three_points_att', 0)}",
                    ft=f"{stats.get('free_throws_made', 0)}-{stats.get('free_throws_att', 0)}",
                    plus_minus=stats.get("plus_minus", 0) or 0,
                ))
        return home_players, away_players

    @staticmethod
    def _extract_pbp(pbp_data: dict, sport: str) -> list[PlayEvent]:
        """Extract play-by-play events from SR PBP response."""
        events = []
        event_id = 0
        periods = pbp_data.get("periods", [])

        for per in periods:
            period_num = per.get("number", 0)
            for event in per.get("events", []):
                desc = event.get("description", "")
                if not desc:
                    continue
                clock = event.get("clock", "")
                # Try to determine team
                team = ""
                attribution = event.get("attribution", {})
                if attribution:
                    team = attribution.get("market", attribution.get("name", ""))[:3].upper()

                # Running score
                home_score = event.get("home_points", 0) or 0
                away_score = event.get("away_points", 0) or 0

                # Player name
                player = ""
                if event.get("statistics"):
                    stat = event["statistics"][0] if event["statistics"] else {}
                    player_info = stat.get("player", {})
                    player = player_info.get("full_name", "")

                events.append(PlayEvent(
                    event_id=event_id,
                    clock=clock,
                    period=period_num,
                    team=team,
                    player=player,
                    description=desc,
                    home_score=home_score,
                    away_score=away_score,
                ))
                event_id += 1

        # Return most recent first
        events.reverse()
        return events

    @staticmethod
    def _extract_team_stats(summary: dict) -> tuple[dict, dict]:
        """Extract team-level stats from SR summary."""
        home_stats = {}
        away_stats = {}

        for side, dest in [("home", home_stats), ("away", away_stats)]:
            team = summary.get(side, {})
            stats = team.get("statistics", {})
            if not stats:
                continue
            # Map to display-friendly keys
            fgm = stats.get("field_goals_made", 0)
            fga = stats.get("field_goals_att", 0)
            tpm = stats.get("three_points_made", 0)
            tpa = stats.get("three_points_att", 0)
            ftm = stats.get("free_throws_made", 0)
            fta = stats.get("free_throws_att", 0)

            dest["FG"] = f"{fgm}-{fga}"
            if fga:
                dest["FG%"] = f"{fgm / fga * 100:.1f}%"
            dest["3PT"] = f"{tpm}-{tpa}"
            if tpa:
                dest["3PT%"] = f"{tpm / tpa * 100:.1f}%"
            dest["FT"] = f"{ftm}-{fta}"
            if fta:
                dest["FT%"] = f"{ftm / fta * 100:.1f}%"
            dest["Rebounds"] = stats.get("rebounds", 0)
            dest["Assists"] = stats.get("assists", 0)
            dest["Steals"] = stats.get("steals", 0)
            dest["Blocks"] = stats.get("blocks", 0)
            dest["Turnovers"] = stats.get("turnovers", 0)
            dest["Points in Paint"] = stats.get("points_in_paint", stats.get("paint_pts", 0))
            dest["Fast Break Pts"] = stats.get("fast_break_pts", 0)

        return home_stats, away_stats
