import random
import time
from .provider import (
    DataProvider, GameSummary, GameDetail, PlayerStats, PlayEvent
)

# ── Lakers roster ───────────────────────────────────────────────────
_LAKERS_PLAYERS = [
    PlayerStats("LeBron James", "SF", "28:14", 21, 7, 9, 1, 1, "8-15", "3-6", "2-2", 8),
    PlayerStats("Anthony Davis", "PF", "26:42", 18, 11, 2, 2, 3, "7-14", "0-1", "4-5", 5),
    PlayerStats("Austin Reaves", "SG", "25:03", 14, 3, 5, 1, 0, "5-11", "2-5", "2-2", 3),
    PlayerStats("D'Angelo Russell", "PG", "22:18", 11, 2, 6, 0, 0, "4-10", "3-7", "0-0", -2),
    PlayerStats("Rui Hachimura", "PF", "20:30", 8, 4, 1, 0, 1, "3-7", "1-3", "1-2", 1),
    PlayerStats("Jarred Vanderbilt", "SF", "14:05", 4, 6, 1, 2, 1, "2-4", "0-0", "0-0", -1),
    PlayerStats("Gabe Vincent", "PG", "12:22", 2, 1, 3, 0, 0, "1-5", "0-3", "0-0", -4),
    PlayerStats("Jaxson Hayes", "C", "10:46", 0, 3, 0, 0, 2, "0-2", "0-0", "0-0", 2),
]

# ── Celtics roster ──────────────────────────────────────────────────
_CELTICS_PLAYERS = [
    PlayerStats("Jayson Tatum", "SF", "27:55", 24, 5, 4, 1, 0, "9-18", "4-8", "2-3", 6),
    PlayerStats("Jaylen Brown", "SG", "26:30", 19, 6, 3, 2, 1, "7-16", "3-6", "2-2", 4),
    PlayerStats("Kristaps Porzingis", "C", "24:12", 16, 8, 1, 0, 3, "6-12", "2-4", "2-2", 7),
    PlayerStats("Derrick White", "PG", "23:48", 10, 3, 5, 1, 1, "4-9", "2-5", "0-0", 5),
    PlayerStats("Jrue Holiday", "PG", "22:06", 8, 4, 6, 2, 0, "3-8", "1-3", "1-2", 3),
    PlayerStats("Al Horford", "C", "14:50", 5, 5, 2, 0, 1, "2-5", "1-3", "0-0", 1),
    PlayerStats("Sam Hauser", "SF", "10:15", 0, 1, 0, 0, 0, "0-3", "0-3", "0-0", -2),
    PlayerStats("Payton Pritchard", "PG", "10:24", 0, 0, 2, 0, 0, "0-4", "0-3", "0-0", -1),
]

# ── Duke roster ─────────────────────────────────────────────────────
_DUKE_PLAYERS = [
    PlayerStats("Cooper Flagg", "PF", "24:30", 16, 7, 3, 1, 2, "6-12", "2-4", "2-3", 5),
    PlayerStats("Tyrese Proctor", "PG", "23:15", 11, 2, 5, 2, 0, "4-9", "2-5", "1-1", 3),
    PlayerStats("Caleb Foster", "SG", "22:00", 8, 1, 3, 0, 0, "3-8", "2-5", "0-0", 1),
    PlayerStats("Kyle Filipowski", "C", "20:45", 6, 8, 2, 0, 1, "3-7", "0-1", "0-0", 2),
    PlayerStats("Mark Mitchell", "SF", "18:30", 4, 3, 1, 1, 0, "2-6", "0-2", "0-0", -1),
]

# ── UNC roster ──────────────────────────────────────────────────────
_UNC_PLAYERS = [
    PlayerStats("RJ Davis", "PG", "25:10", 14, 3, 6, 1, 0, "5-12", "2-6", "2-2", -2),
    PlayerStats("Armando Bacot", "C", "23:45", 10, 9, 1, 0, 2, "5-9", "0-0", "0-1", -3),
    PlayerStats("Harrison Ingram", "SF", "21:30", 8, 5, 2, 1, 0, "3-8", "1-3", "1-2", -1),
    PlayerStats("Seth Trimble", "SG", "20:15", 6, 2, 3, 0, 0, "2-7", "1-4", "1-1", 0),
    PlayerStats("Cormac Ryan", "SG", "16:00", 4, 1, 0, 0, 0, "2-5", "0-2", "0-0", -2),
]

# ── Play-by-play: Lakers vs Celtics ────────────────────────────────
_LAKERS_CELTICS_PBP = [
    PlayEvent(50, "4:32", 3, "BOS", "Jayson Tatum", "Tatum 26' pull-up jumper (24 PTS)", 78, 82),
    PlayEvent(49, "4:55", 3, "LAL", "LeBron James", "James driving layup (21 PTS)", 78, 80),
    PlayEvent(48, "5:12", 3, "BOS", "Derrick White", "White 3PT from left wing (10 PTS)", 76, 80),
    PlayEvent(47, "5:30", 3, "LAL", "Anthony Davis", "Davis dunk off lob from Reaves (18 PTS)", 76, 77),
    PlayEvent(46, "5:48", 3, "BOS", "Jaylen Brown", "Brown steal and fast break layup (19 PTS)", 74, 77),
    PlayEvent(45, "6:05", 3, "LAL", "Austin Reaves", "Reaves 3PT from right corner (14 PTS)", 74, 75),
    PlayEvent(44, "6:22", 3, "BOS", "Kristaps Porzingis", "Porzingis hook shot in lane (16 PTS)", 71, 75),
    PlayEvent(43, "6:40", 3, "LAL", "D'Angelo Russell", "Russell 3PT from top of key (11 PTS)", 71, 73),
    PlayEvent(42, "6:58", 3, "BOS", "Jrue Holiday", "Holiday floating jumper (8 PTS)", 68, 73),
    PlayEvent(41, "7:15", 3, "LAL", "LeBron James", "James 3PT from left wing (19 PTS)", 68, 71),
    PlayEvent(40, "7:33", 3, "BOS", "Jayson Tatum", "Tatum and-one layup (22 PTS)", 65, 71),
    PlayEvent(39, "7:50", 3, "LAL", "Rui Hachimura", "Hachimura mid-range jumper (8 PTS)", 65, 68),
    PlayEvent(38, "8:08", 3, "BOS", "Jaylen Brown", "Brown 3PT from right wing (17 PTS)", 63, 68),
    PlayEvent(37, "8:25", 3, "LAL", "Anthony Davis", "Davis turnaround fadeaway (16 PTS)", 63, 65),
    PlayEvent(36, "8:42", 3, "BOS", "Kristaps Porzingis", "Porzingis 3PT from top (14 PTS)", 61, 65),
    PlayEvent(35, "9:00", 3, "LAL", "Austin Reaves", "Reaves driving floater (11 PTS)", 61, 62),
    PlayEvent(34, "9:18", 3, "BOS", "Derrick White", "White layup off screen (7 PTS)", 59, 62),
    PlayEvent(33, "9:35", 3, "LAL", "LeBron James", "James tomahawk dunk in transition (16 PTS)", 59, 60),
    PlayEvent(32, "9:52", 3, "BOS", "Jayson Tatum", "Tatum step-back 3PT (19 PTS)", 57, 60),
    PlayEvent(31, "10:10", 3, "LAL", "D'Angelo Russell", "Russell pull-up jumper (8 PTS)", 57, 57),
    PlayEvent(30, "10:30", 3, "BOS", "Al Horford", "Horford 3PT from corner (5 PTS)", 55, 57),
    # End of Q2 / halftime plays
    PlayEvent(29, "0:00", 2, "LAL", "", "End of 2nd Quarter", 55, 54),
    PlayEvent(28, "0:05", 2, "LAL", "LeBron James", "James buzzer-beater mid-range (14 PTS)", 55, 54),
    PlayEvent(27, "0:22", 2, "BOS", "Jayson Tatum", "Tatum free throw 2 of 2 (16 PTS)", 53, 54),
    PlayEvent(26, "0:22", 2, "BOS", "Jayson Tatum", "Tatum free throw 1 of 2 (15 PTS)", 53, 53),
    PlayEvent(25, "0:45", 2, "LAL", "Anthony Davis", "Davis block on Brown", 53, 52),
    PlayEvent(24, "1:02", 2, "LAL", "Austin Reaves", "Reaves 3PT from left wing (8 PTS)", 53, 52),
    PlayEvent(23, "1:20", 2, "BOS", "Jaylen Brown", "Brown driving dunk (14 PTS)", 50, 52),
    PlayEvent(22, "1:38", 2, "LAL", "LeBron James", "James no-look pass to Davis — dunk (12 PTS)", 50, 50),
    PlayEvent(21, "1:55", 2, "BOS", "Jrue Holiday", "Holiday 3PT from right wing (6 PTS)", 48, 50),
    PlayEvent(20, "2:12", 2, "LAL", "Rui Hachimura", "Hachimura cutting layup (6 PTS)", 48, 47),
    PlayEvent(19, "2:30", 2, "BOS", "Kristaps Porzingis", "Porzingis alley-oop dunk (11 PTS)", 46, 47),
    PlayEvent(18, "2:48", 2, "LAL", "D'Angelo Russell", "Russell step-back 3PT (5 PTS)", 46, 45),
    PlayEvent(17, "3:05", 2, "BOS", "Derrick White", "White steal and coast-to-coast layup (5 PTS)", 43, 45),
    PlayEvent(16, "3:22", 2, "LAL", "Anthony Davis", "Davis put-back dunk (10 PTS)", 43, 43),
    PlayEvent(15, "3:40", 2, "BOS", "Jayson Tatum", "Tatum 3PT from left corner (14 PTS)", 41, 43),
    PlayEvent(14, "3:58", 2, "LAL", "LeBron James", "James and-one driving layup (10 PTS)", 41, 40),
    PlayEvent(13, "4:15", 2, "BOS", "Jaylen Brown", "Brown mid-range fadeaway (12 PTS)", 38, 40),
    PlayEvent(12, "4:33", 2, "LAL", "Austin Reaves", "Reaves floater in lane (5 PTS)", 38, 38),
    # End of Q1
    PlayEvent(11, "0:00", 1, "BOS", "", "End of 1st Quarter", 36, 38),
    PlayEvent(10, "0:15", 1, "BOS", "Jayson Tatum", "Tatum turnaround jumper (11 PTS)", 36, 38),
    PlayEvent(9, "0:33", 1, "LAL", "LeBron James", "James 3PT from right wing (7 PTS)", 36, 36),
    PlayEvent(8, "0:50", 1, "BOS", "Jaylen Brown", "Brown 3PT catch-and-shoot (10 PTS)", 33, 36),
    PlayEvent(7, "1:08", 1, "LAL", "Anthony Davis", "Davis hook shot over Horford (8 PTS)", 33, 33),
    PlayEvent(6, "1:25", 1, "BOS", "Kristaps Porzingis", "Porzingis 3PT from top of arc (9 PTS)", 31, 33),
    PlayEvent(5, "1:42", 1, "LAL", "D'Angelo Russell", "Russell pull-up 3PT in transition (2 PTS)", 31, 30),
    PlayEvent(4, "2:00", 1, "BOS", "Jrue Holiday", "Holiday driving layup (3 PTS)", 28, 30),
    PlayEvent(3, "2:18", 1, "LAL", "LeBron James", "James slam dunk off Davis screen (4 PTS)", 28, 28),
    PlayEvent(2, "2:35", 1, "BOS", "Jayson Tatum", "Tatum 3PT from right wing (9 PTS)", 26, 28),
    PlayEvent(1, "2:52", 1, "LAL", "Austin Reaves", "Reaves layup in transition (3 PTS)", 26, 25),
]

# ── Play-by-play: Duke vs UNC ──────────────────────────────────────
_DUKE_UNC_PBP = [
    PlayEvent(25, "8:15", 2, "DUKE", "Cooper Flagg", "Flagg 3PT from left wing (16 PTS)", 45, 42),
    PlayEvent(24, "8:35", 2, "UNC", "RJ Davis", "Davis driving floater (14 PTS)", 42, 42),
    PlayEvent(23, "8:52", 2, "DUKE", "Tyrese Proctor", "Proctor step-back jumper (11 PTS)", 42, 40),
    PlayEvent(22, "9:10", 2, "UNC", "Armando Bacot", "Bacot dunk off offensive rebound (10 PTS)", 40, 40),
    PlayEvent(21, "9:28", 2, "DUKE", "Cooper Flagg", "Flagg block on Bacot", 40, 38),
    PlayEvent(20, "9:45", 2, "DUKE", "Caleb Foster", "Foster 3PT from right corner (8 PTS)", 40, 38),
    PlayEvent(19, "10:02", 2, "UNC", "Harrison Ingram", "Ingram mid-range jumper (8 PTS)", 37, 38),
    PlayEvent(18, "10:20", 2, "DUKE", "Kyle Filipowski", "Filipowski hook shot in paint (6 PTS)", 37, 36),
    PlayEvent(17, "10:38", 2, "UNC", "RJ Davis", "Davis 3PT from top of key (12 PTS)", 35, 36),
    PlayEvent(16, "10:55", 2, "DUKE", "Cooper Flagg", "Flagg and-one driving layup (13 PTS)", 35, 33),
    PlayEvent(15, "11:12", 2, "UNC", "Seth Trimble", "Trimble layup off screen (6 PTS)", 32, 33),
    PlayEvent(14, "11:30", 2, "DUKE", "Tyrese Proctor", "Proctor 3PT from left wing (9 PTS)", 32, 31),
    PlayEvent(13, "11:48", 2, "UNC", "Armando Bacot", "Bacot put-back layup (8 PTS)", 29, 31),
    PlayEvent(12, "12:05", 2, "DUKE", "Mark Mitchell", "Mitchell baseline jumper (4 PTS)", 29, 29),
    # End of 1st half
    PlayEvent(11, "0:00", 1, "DUKE", "", "End of 1st Half", 27, 29),
    PlayEvent(10, "0:12", 1, "UNC", "RJ Davis", "Davis buzzer-beater 3PT (9 PTS)", 27, 29),
    PlayEvent(9, "0:30", 1, "DUKE", "Cooper Flagg", "Flagg slam dunk in transition (10 PTS)", 27, 26),
    PlayEvent(8, "0:48", 1, "UNC", "Armando Bacot", "Bacot free throw 2 of 2 (6 PTS)", 25, 26),
    PlayEvent(7, "0:48", 1, "UNC", "Armando Bacot", "Bacot free throw 1 of 2 (5 PTS)", 25, 25),
    PlayEvent(6, "1:05", 1, "DUKE", "Caleb Foster", "Foster pull-up jumper (5 PTS)", 25, 24),
    PlayEvent(5, "1:22", 1, "UNC", "Harrison Ingram", "Ingram 3PT from right wing (6 PTS)", 23, 24),
    PlayEvent(4, "1:40", 1, "DUKE", "Tyrese Proctor", "Proctor driving layup (6 PTS)", 23, 21),
    PlayEvent(3, "1:58", 1, "UNC", "Seth Trimble", "Trimble mid-range jumper (4 PTS)", 21, 21),
    PlayEvent(2, "2:15", 1, "DUKE", "Cooper Flagg", "Flagg 3PT from top of arc (8 PTS)", 21, 19),
    PlayEvent(1, "2:32", 1, "UNC", "RJ Davis", "Davis floater in lane (6 PTS)", 18, 19),
]

# ── Simulated clock drift for live games ────────────────────────────
_CLOCK_BASE = time.time()


def _simulated_clock(base_clock: str, period: int) -> tuple[str, int]:
    """Drift the clock down slowly so the site looks alive."""
    elapsed = (time.time() - _CLOCK_BASE) % 300  # 5-min cycle
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


# ── Mock games ──────────────────────────────────────────────────────
_GAMES = {
    "nba-lal-bos-20260223": {
        "summary_base": GameSummary(
            game_id="nba-lal-bos-20260223",
            sport="nba",
            status="live",
            home_team="Los Angeles Lakers",
            away_team="Boston Celtics",
            home_score=78,
            away_score=82,
            period=3,
            clock="4:32",
            start_time="3:30 PM ET",
        ),
        "home_players": _LAKERS_PLAYERS,
        "away_players": _CELTICS_PLAYERS,
        "pbp": _LAKERS_CELTICS_PBP,
        "home_team_stats": {
            "FG%": "46.3%", "3PT%": "38.5%", "FT%": "81.8%",
            "Rebounds": 37, "Assists": 24, "Turnovers": 8,
            "Steals": 6, "Blocks": 7, "Points in Paint": 34,
            "Fast Break Points": 12,
        },
        "away_team_stats": {
            "FG%": "48.1%", "3PT%": "36.1%", "FT%": "77.8%",
            "Rebounds": 33, "Assists": 21, "Turnovers": 10,
            "Steals": 8, "Blocks": 6, "Points in Paint": 30,
            "Fast Break Points": 16,
        },
    },
    "nba-sas-det-20260223": {
        "summary_base": GameSummary(
            game_id="nba-sas-det-20260223",
            sport="nba",
            status="scheduled",
            home_team="Detroit Pistons",
            away_team="San Antonio Spurs",
            home_score=0,
            away_score=0,
            period=0,
            clock="",
            start_time="7:00 PM ET",
        ),
        "home_players": [],
        "away_players": [],
        "pbp": [],
        "home_team_stats": {},
        "away_team_stats": {},
    },
    "ncaamb-duke-unc-20260223": {
        "summary_base": GameSummary(
            game_id="ncaamb-duke-unc-20260223",
            sport="ncaamb",
            status="live",
            home_team="Duke Blue Devils",
            away_team="North Carolina Tar Heels",
            home_score=45,
            away_score=42,
            period=2,
            clock="8:15",
            start_time="1:00 PM ET",
        ),
        "home_players": _DUKE_PLAYERS,
        "away_players": _UNC_PLAYERS,
        "pbp": _DUKE_UNC_PBP,
        "home_team_stats": {
            "FG%": "44.0%", "3PT%": "35.3%", "FT%": "66.7%",
            "Rebounds": 21, "Assists": 14, "Turnovers": 6,
            "Steals": 4, "Blocks": 3, "Points in Paint": 18,
        },
        "away_team_stats": {
            "FG%": "41.2%", "3PT%": "30.8%", "FT%": "75.0%",
            "Rebounds": 20, "Assists": 12, "Turnovers": 7,
            "Steals": 2, "Blocks": 2, "Points in Paint": 22,
        },
    },
}


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
