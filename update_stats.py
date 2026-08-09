import os
import re
import json
import requests
from datetime import datetime, timedelta, timezone

# Configurations
LEETCODE_USER = "gauravk006"
CODEFORCES_USER = "gauravkasaudhan206"
GFG_USER = "gauravkasa0dfs"
TIMEZONE_KOLKATA = timezone(timedelta(hours=5, minutes=30))

def get_local_date(ts):
    """Convert unix timestamp to YYYY-MM-DD in IST."""
    return datetime.fromtimestamp(int(ts), tz=TIMEZONE_KOLKATA).strftime('%Y-%m-%d')

def get_today_ist():
    return datetime.now(tz=TIMEZONE_KOLKATA).date()

def calculate_streaks(active_dates):
    """Given a set/list of active YYYY-MM-DD dates, compute current and longest streak."""
    if not active_dates:
        return 0, 0
    
    # Sort unique dates
    sorted_dates = sorted(list(set(active_dates)))
    date_objs = [datetime.strptime(d, "%Y-%m-%d").date() for d in sorted_dates]
    
    longest = 0
    current = 0
    temp_streak = 0
    prev_date = None
    
    for d in date_objs:
        if prev_date is None:
            temp_streak = 1
        elif (d - prev_date).days == 1:
            temp_streak += 1
        elif (d - prev_date).days > 1:
            if temp_streak > longest:
                longest = temp_streak
            temp_streak = 1
        prev_date = d
    
    if temp_streak > longest:
        longest = temp_streak
        
    # Calculate current streak
    today = get_today_ist()
    yesterday = today - timedelta(days=1)
    
    # Trace back from today or yesterday
    if today in date_objs:
        current = 1
        check_date = yesterday
        while check_date in date_objs:
            current += 1
            check_date -= timedelta(days=1)
    elif yesterday in date_objs:
        current = 1
        check_date = yesterday - timedelta(days=1)
        while check_date in date_objs:
            current += 1
            check_date -= timedelta(days=1)
    else:
        current = 0
        
    return current, longest

def fetch_leetcode(username):
    print("Fetching LeetCode stats...")
    url = "https://leetcode.com/graphql"
    query = """
    query userProfileStats($username: String!) {
      matchedUser(username: $username) {
        submitStatsGlobal {
          acSubmissionNum {
            difficulty
            count
          }
        }
        userCalendar {
          streak
          submissionCalendar
        }
      }
    }
    """
    payload = {"query": query, "variables": {"username": username}}
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            res_data = response.json()
            user_data = res_data.get("data", {}).get("matchedUser", {})
            if not user_data:
                print("LeetCode user data not found.")
                return None
            
            # Parse solved count
            solved_stats = user_data.get("submitStatsGlobal", {}).get("acSubmissionNum", [])
            solved = 0
            easy = 0
            medium = 0
            hard = 0
            for item in solved_stats:
                diff = item.get("difficulty")
                count = item.get("count", 0)
                if diff == "All":
                    solved = count
                elif diff == "Easy":
                    easy = count
                elif diff == "Medium":
                    medium = count
                elif diff == "Hard":
                    hard = count
            
            # Parse calendar
            cal_str = user_data.get("userCalendar", {}).get("submissionCalendar", "{}")
            calendar = json.loads(cal_str)
            
            # Get active dates in YYYY-MM-DD
            active_dates = []
            for ts, count in calendar.items():
                if count > 0:
                    active_dates.append(get_local_date(ts))
            
            curr_streak, long_streak = calculate_streaks(active_dates)
            
            return {
                "solved": solved,
                "easy": easy,
                "medium": medium,
                "hard": hard,
                "active_dates": active_dates,
                "current_streak": curr_streak,
                "longest_streak": max(long_streak, user_data.get("userCalendar", {}).get("streak", 0))
            }
    except Exception as e:
        print("LeetCode fetch error:", e)
    return None

def fetch_codeforces(username):
    print("Fetching Codeforces stats...")
    url = f"https://codeforces.com/api/user.status?handle={username}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "OK":
                submissions = data.get("result", [])
                solved_problems = set()
                active_dates = []
                
                easy = 0
                medium = 0
                hard = 0
                
                for sub in submissions:
                    creation_time = sub.get("creationTimeSeconds")
                    if creation_time:
                        active_dates.append(get_local_date(creation_time))
                    
                    if sub.get("verdict") == "OK":
                        prob = sub.get("problem", {})
                        contest_id = prob.get("contestId")
                        index = prob.get("index")
                        if contest_id and index:
                            prob_id = f"{contest_id}_{index}"
                            if prob_id not in solved_problems:
                                solved_problems.add(prob_id)
                                rating = prob.get("rating")
                                if rating is None:
                                    easy += 1  # default
                                elif rating < 1200:
                                    easy += 1
                                elif rating < 1900:
                                    medium += 1
                                else:
                                    hard += 1
                
                solved = len(solved_problems)
                curr_streak, long_streak = calculate_streaks(active_dates)
                
                return {
                    "solved": solved,
                    "easy": easy,
                    "medium": medium,
                    "hard": hard,
                    "active_dates": active_dates,
                    "current_streak": curr_streak,
                    "longest_streak": long_streak
                }
    except Exception as e:
        print("Codeforces fetch error:", e)
    return None

def fetch_gfg(username):
    print("Fetching GeeksforGeeks stats...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    profile_url = f"https://www.geeksforgeeks.org/profile/{username}"
    
    solved = 0
    easy = 0
    medium = 0
    hard = 0
    school = 0
    basic = 0
    curr_streak = 0
    long_streak = 0
    score = 0
    rank = 0
    monthly_score = 0
    
    # Method 1: Try scraping profile HTML for Next.js props
    try:
        response = requests.get(profile_url, headers=headers, timeout=15)
        if response.status_code == 200:
            html = response.text
            
            # Find stats in JSON format using regex
            match_stats = re.search(r'"total_problems_solved":\s*(\d+)', html)
            if match_stats:
                solved = int(match_stats.group(1))
            
            match_score = re.search(r'"score":\s*(\d+)', html)
            if match_score:
                score = int(match_score.group(1))
                
            match_rank = re.search(r'"institute_rank":\s*(\d+)', html)
            if match_rank:
                rank = int(match_rank.group(1))
                
            match_monthly = re.search(r'"monthly_score":\s*(\d+)', html)
            if match_monthly:
                monthly_score = int(match_monthly.group(1))
                
            match_curr = re.search(r'"pod_solved_current_streak":\s*(\d+)', html)
            if match_curr:
                curr_streak = int(match_curr.group(1))
                
            match_long = re.search(r'"pod_solved_longest_streak":\s*(\d+)', html)
            if match_long:
                long_streak = int(match_long.group(1))
                
            # Parse levels
            for lvl, field in [("school", "school"), ("basic", "basic"), ("easy", "easy"), ("medium", "medium"), ("hard", "hard")]:
                lvl_match = re.search(rf'"{lvl}":\s*(\d+)', html)
                if lvl_match:
                    val = int(lvl_match.group(1))
                    if field == "school": school = val
                    elif field == "basic": basic = val
                    elif field == "easy": easy = val
                    elif field == "medium": medium = val
                    elif field == "hard": hard = val
            
            print("GFG Direct Scraping Solved Count:", solved)
    except Exception as e:
        print("GFG profile page scrape error:", e)

    # Method 2: Fallback to SVG stats card if solved count is 0
    if solved == 0:
        print("GFG scraping returned 0 or failed. Falling back to Stats Card...")
        svg_url = f"https://gfgstatscard.vercel.app/{username}"
        try:
            response = requests.get(svg_url, headers=headers, timeout=15)
            if response.status_code == 200:
                svg_content = response.text
                
                # Extract level counts using regex
                lvl_counts = {}
                for lvl in ["school", "basic", "easy", "medium", "hard"]:
                    match = re.search(rf'id="{lvl}-solved-count">(\d+)</text>', svg_content)
                    lvl_counts[lvl] = int(match.group(1)) if match else 0
                
                school = lvl_counts.get("school", 0)
                basic = lvl_counts.get("basic", 0)
                easy = lvl_counts.get("easy", 0)
                medium = lvl_counts.get("medium", 0)
                hard = lvl_counts.get("hard", 0)
                solved = sum(lvl_counts.values())
                
                # Fetch streak if present
                streak_match = re.search(r'id="total-streak-text">(\d+)\s*/', svg_content)
                if streak_match:
                    curr_streak = int(streak_match.group(1))
                    long_streak = curr_streak
                print("GFG SVG Fallback Solved Count:", solved)
        except Exception as e:
            print("GFG SVG fallback fetch error:", e)
            
    # Normalize difficulties: School + Basic count as GFG Easy
    return {
        "solved": solved,
        "easy": easy + basic + school,
        "medium": medium,
        "hard": hard,
        "current_streak": curr_streak,
        "longest_streak": long_streak,
        "active_dates": [],  # GFG active dates are not publicly scrapeable, streak will be calculated from GFG profile properties
        "score": score,
        "rank": rank,
        "monthly_score": monthly_score
    }

def generate_svg(data):
    """Draw a professional dynamic SVG showing statistics."""
    solved_all = data["all"]["solved"]
    solved_lc = data["leetcode"]["solved"]
    solved_gfg = data["gfg"]["solved"]
    solved_cf = data["codeforces"]["solved"]
    
    streak_all = data["all"]["current_streak"]
    streak_lc = data["leetcode"]["current_streak"]
    streak_gfg = data["gfg"]["current_streak"]
    streak_cf = data["codeforces"]["current_streak"]
    
    # Combined heatmap calculations (last 12 weeks = 84 days)
    today = get_today_ist()
    start_date = today - timedelta(days=83)
    
    # Fill submission counts
    lc_calendar = set(data["leetcode"]["active_dates"])
    cf_calendar = set(data["codeforces"]["active_dates"])
    combined_active = lc_calendar.union(cf_calendar)
    
    # SVG construction (dimensions: 820 x 280)
    svg = f"""<svg width="820" height="280" viewBox="0 0 820 280" version="1.1" xmlns="http://www.w3.org/2000/svg" style="background:#0d1117; font-family:'Segoe UI',Ubuntu,sans-serif; border-radius:12px; border:1px solid #30363d;">
    <style>
        .title {{ fill: #f0f6fc; font-size: 18px; font-weight: 700; }}
        .subtitle {{ fill: #8b949e; font-size: 12px; }}
        .header-line {{ stroke: #30363d; stroke-width: 1; }}
        .card-bg {{ fill: #161b22; stroke: #30363d; stroke-width: 1; rx: 8px; }}
        .stat-label {{ fill: #8b949e; font-size: 10px; font-weight: 700; letter-spacing: 0.5px; }}
        .stat-value {{ fill: #f0f6fc; font-size: 24px; font-weight: 800; }}
        .stat-streak {{ fill: #ff9f43; font-size: 13px; font-weight: 600; }}
        .badge-lc {{ fill: #ffa116; font-size: 11px; font-weight: 700; }}
        .badge-gfg {{ fill: #2f8d46; font-size: 11px; font-weight: 700; }}
        .badge-cf {{ fill: #3182ce; font-size: 11px; font-weight: 700; }}
    </style>
    
    <!-- Header -->
    <text x="25" y="35" class="title">🧠 Coding Progress Dashboard</text>
    <text x="25" y="55" class="subtitle">Real-time stats synced from LeetCode, GFG &amp; Codeforces</text>
    <line x1="25" y1="70" x2="795" y2="70" class="header-line" />
    
    <!-- Left Column: Unified Stats Card -->
    <rect x="25" y="90" width="220" height="165" class="card-bg" />
    <text x="45" y="120" class="stat-label">TOTAL PROBLEMS SOLVED</text>
    <text x="45" y="155" class="stat-value" style="font-size:32px; fill:#58a6ff;">{solved_all}</text>
    
    <text x="45" y="195" class="stat-label">COMBINED STREAK</text>
    <text x="45" y="225" class="stat-value" style="fill:#ff9f43;">🔥 {streak_all} <tspan font-size="12" font-weight="600" fill="#8b949e">days</tspan></text>
    
    <!-- Middle Column: Platform Cards -->
    <!-- Codeforces -->
    <rect x="265" y="90" width="165" height="165" class="card-bg" />
    <text x="285" y="115" class="badge-cf">🔵 CODEFORCES</text>
    <text x="285" y="150" class="stat-value">{solved_cf}</text>
    <text x="285" y="170" class="stat-label">Solved</text>
    <text x="285" y="205" class="stat-streak">🔥 {streak_cf} days</text>
    <text x="285" y="235" class="stat-streak">🏆 {data["codeforces"]["longest_streak"]} days max</text>

    <!-- LeetCode -->
    <rect x="445" y="90" width="165" height="165" class="card-bg" />
    <text x="465" y="115" class="badge-lc">🟠 LEETCODE</text>
    <text x="465" y="150" class="stat-value">{solved_lc}</text>
    <text x="465" y="170" class="stat-label">Solved</text>
    <text x="465" y="205" class="stat-streak">🔥 {streak_lc} days</text>
    <text x="465" y="235" class="stat-streak">🏆 {data["leetcode"]["longest_streak"]} days max</text>

    <!-- GFG -->
    <rect x="625" y="90" width="165" height="165" class="card-bg" />
    <text x="645" y="115" class="badge-gfg">🟢 GEEKFORGEEKS</text>
    <text x="645" y="150" class="stat-value">{solved_gfg}</text>
    <text x="645" y="170" class="stat-label">Solved</text>
    <text x="645" y="205" class="stat-streak">🔥 {streak_gfg} days</text>
    <text x="645" y="235" class="stat-streak">🏆 {data["gfg"]["longest_streak"]} days max</text>

    </svg>
    """
    return svg

def main():
    print("Starting data gathering...")
    
    # 1. Fetch from platforms
    lc_data = fetch_leetcode(LEETCODE_USER)
    cf_data = fetch_codeforces(CODEFORCES_USER)
    gfg_data = fetch_gfg(GFG_USER)
    
    # Handle failures with empty data placeholders
    if not lc_data:
        lc_data = {"solved": 0, "easy": 0, "medium": 0, "hard": 0, "active_dates": [], "current_streak": 0, "longest_streak": 0}
    if not cf_data:
        cf_data = {"solved": 0, "easy": 0, "medium": 0, "hard": 0, "active_dates": [], "current_streak": 0, "longest_streak": 0}
    if not gfg_data:
        gfg_data = {"solved": 0, "easy": 0, "medium": 0, "hard": 0, "active_dates": [], "current_streak": 0, "longest_streak": 0, "score": 0, "rank": 0, "monthly_score": 0}
        
    # 2. Combined calculations
    solved_all = lc_data["solved"] + cf_data["solved"] + gfg_data["solved"]
    easy_all = lc_data["easy"] + cf_data["easy"] + gfg_data["easy"]
    medium_all = lc_data["medium"] + cf_data["medium"] + gfg_data["medium"]
    hard_all = lc_data["hard"] + cf_data["hard"] + gfg_data["hard"]
    
    # Combined calendar
    combined_dates = set(lc_data["active_dates"]).union(set(cf_data["active_dates"]))
    streak_all, longest_streak_all = calculate_streaks(combined_dates)
    
    all_data = {
        "solved": solved_all,
        "easy": easy_all,
        "medium": medium_all,
        "hard": hard_all,
        "current_streak": streak_all,
        "longest_streak": longest_streak_all,
        "active_dates": sorted(list(combined_dates))
    }
    
    # Save to data.json
    result_data = {
        "last_updated": datetime.now(tz=TIMEZONE_KOLKATA).strftime('%Y-%m-%d %H:%M:%S IST'),
        "all": all_data,
        "leetcode": lc_data,
        "gfg": gfg_data,
        "codeforces": cf_data
    }
    
    # Ensure assets directory exists
    os.makedirs("assets", exist_ok=True)
    
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    print("Saved stats to data.json successfully.")
    
    # 3. Generate SVG
    svg_content = generate_svg(result_data)
    with open("assets/coding-dashboard.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Generated assets/coding-dashboard.svg successfully.")

if __name__ == "__main__":
    main()
