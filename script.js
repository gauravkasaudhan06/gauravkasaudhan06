let dashboardData = null;
let currentPlatform = 'all';

// Initialize Page
document.addEventListener("DOMContentLoaded", () => {
  fetchData();
  setupTabs();
  setupTooltip();
});

// Fetch stats database
async function fetchData() {
  try {
    const response = await fetch("data.json");
    if (!response.ok) throw new Error("Failed to load dashboard data.");
    dashboardData = await response.json();
    
    // Set sync time
    document.getElementById("sync-time").textContent = dashboardData.last_updated || "Just now";
    
    // Render initial active state (All platforms)
    renderPlatformData(currentPlatform);
  } catch (error) {
    console.error("Error loading dashboard data:", error);
    document.getElementById("sync-time").textContent = "Sync failed";
  }
}

// Handle platform buttons selection
function setupTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      // Toggle active states
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      
      currentPlatform = tab.dataset.platform;
      renderPlatformData(currentPlatform);
    });
  });
}

// Update stats, metrics, progress bars and heatmap
function renderPlatformData(platform) {
  if (!dashboardData) return;
  
  const platformData = dashboardData[platform];
  if (!platformData) return;
  
  // 1. Update Numeric Summary Counters
  animateValue("solved-count", platformData.solved);
  animateValue("current-streak", platformData.current_streak, "🔥 ");
  animateValue("max-streak", platformData.longest_streak, "🔥 ");
  
  // Calculate active days
  let activeDays = 0;
  if (platform === 'all') {
    activeDays = platformData.active_dates.length;
  } else if (platform === 'leetcode' || platform === 'codeforces') {
    activeDays = platformData.active_dates.length;
  } else {
    // GFG doesn't expose active dates, show streak count or estimated days
    activeDays = platformData.solved > 0 ? Math.max(1, platformData.current_streak) : 0;
  }
  
  animateValue("active-days", activeDays);
  
  // 2. Update Difficulty Progress Meters
  const easy = platformData.easy || 0;
  const medium = platformData.medium || 0;
  const hard = platformData.hard || 0;
  const total = easy + medium + hard || 1;
  
  const easyPct = Math.round((easy / total) * 100);
  const mediumPct = Math.round((medium / total) * 100);
  const hardPct = Math.round((hard / total) * 100);
  
  document.getElementById("easy-count").textContent = `${easy} (${easyPct}%)`;
  document.getElementById("medium-count").textContent = `${medium} (${mediumPct}%)`;
  document.getElementById("hard-count").textContent = `${hard} (${hardPct}%)`;
  
  document.getElementById("easy-fill").style.width = `${easyPct}%`;
  document.getElementById("medium-fill").style.width = `${mediumPct}%`;
  document.getElementById("hard-fill").style.width = `${hardPct}%`;
  
  // 3. Render Heatmap Activity Board
  renderHeatmap(platform, platformData.active_dates);
  
  // 4. Update Platform Specific Details panel
  renderPlatformDetails(platform, platformData);
}

// Generate 365-day grid
function renderHeatmap(platform, activeDates) {
  const grid = document.getElementById("heatmap-grid");
  grid.innerHTML = "";
  
  const activeSet = new Set(activeDates || []);
  
  // Calculate date range (53 weeks = 371 days ending on today)
  const today = new Date();
  const calendarCells = 371; // 53 weeks * 7 days
  
  // We want the calendar starting on a Sunday to align rows perfectly
  const startDate = new Date();
  startDate.setDate(today.getDate() - calendarCells + 1);
  
  // Adjust to starting Sunday
  const startDay = startDate.getDay(); // 0=Sun, 1=Mon...
  startDate.setDate(startDate.getDate() - startDay);
  
  const tooltip = document.getElementById("heatmap-tooltip");
  
  // Create 371 cells
  for (let i = 0; i < calendarCells; i++) {
    const currentDate = new Date(startDate);
    currentDate.setDate(startDate.getDate() + i);
    
    const dateString = formatDateString(currentDate);
    const cell = document.createElement("div");
    cell.classList.add("heatmap-cell");
    
    // Determine cell levels
    let level = 0;
    
    if (platform === 'gfg') {
      // GFG has no specific daily dates, but if user solved questions, let's distribute/fill some nodes or keep it simple
      // We will show empty calendar with an informational text or fill the streak dates
      level = 0;
    } else {
      if (activeSet.has(dateString)) {
        level = 3; // Standard active level
      }
    }
    
    if (level > 0) {
      cell.classList.add(`level-${level}`);
    }
    
    // Date formatter for hover text
    const formattedDate = currentDate.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric"
    });
    
    const tooltipText = platform === 'gfg' 
      ? `GeeksforGeeks calendar detail not available` 
      : `${formattedDate}: ${activeSet.has(dateString) ? 'Active coding day 🟢' : 'No activity'}`;
      
    // Cell hover tooltip event listeners
    cell.addEventListener("mouseenter", (e) => {
      tooltip.textContent = tooltipText;
      tooltip.style.opacity = "1";
    });
    
    cell.addEventListener("mousemove", (e) => {
      tooltip.style.left = `${e.pageX + 10}px`;
      tooltip.style.top = `${e.pageY - 25}px`;
    });
    
    cell.addEventListener("mouseleave", () => {
      tooltip.style.opacity = "0";
    });
    
    grid.appendChild(cell);
  }
}

// Populate details section based on selected platform
function renderPlatformDetails(platform, data) {
  const panel = document.getElementById("platform-details");
  panel.innerHTML = "";
  
  let details = [];
  
  if (platform === "all") {
    const lcSolved = dashboardData.leetcode.solved;
    const gfgSolved = dashboardData.gfg.solved;
    const cfSolved = dashboardData.codeforces.solved;
    
    details = [
      { label: "Codeforces solved", value: cfSolved },
      { label: "LeetCode solved", value: lcSolved },
      { label: "GeeksforGeeks solved", value: gfgSolved },
      { label: "Combined Active Days", value: data.active_dates.length }
    ];
  } else if (platform === "leetcode") {
    details = [
      { label: "Platform Name", value: "LeetCode" },
      { label: "Username", value: "gauravk006" },
      { label: "Easy Solved", value: data.easy },
      { label: "Medium Solved", value: data.medium },
      { label: "Hard Solved", value: data.hard }
    ];
  } else if (platform === "gfg") {
    details = [
      { label: "Platform Name", value: "GeeksforGeeks" },
      { label: "Username", value: "gauravkasa0dfs" },
      { label: "Coding Score", value: data.score || "N/A" },
      { label: "Monthly Score", value: data.monthly_score || "N/A" },
      { label: "Institute Rank", value: data.rank || "N/A" }
    ];
  } else if (platform === "codeforces") {
    details = [
      { label: "Platform Name", value: "Codeforces" },
      { label: "Username", value: "gauravkasaudhan206" },
      { label: "Submissions Scan", value: "300+ submissions" },
      { label: "Easy Solved", value: data.easy },
      { label: "Medium Solved", value: data.medium }
    ];
  }
  
  details.forEach(item => {
    const row = document.createElement("div");
    row.classList.add("meta-row");
    
    const labelSpan = document.createElement("span");
    labelSpan.classList.add("meta-label");
    labelSpan.textContent = item.label;
    
    const valSpan = document.createElement("span");
    valSpan.classList.add("meta-value");
    valSpan.textContent = item.value;
    
    row.appendChild(labelSpan);
    row.appendChild(valSpan);
    panel.appendChild(row);
  });
}

// Utility: format Date to YYYY-MM-DD
function formatDateString(date) {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

// Utility: Animate counters counting up
function animateValue(id, startOrEnd, prefix = "") {
  const obj = document.getElementById(id);
  const end = parseInt(startOrEnd, 10);
  
  if (isNaN(end) || end === 0) {
    obj.textContent = prefix + (startOrEnd || "0");
    return;
  }
  
  let start = 0;
  const duration = 500; // ms
  const startTime = performance.now();
  
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // Ease out quad
    const easeProgress = progress * (2 - progress);
    const currentVal = Math.floor(start + easeProgress * (end - start));
    
    obj.textContent = prefix + currentVal;
    
    if (progress < 1) {
      requestAnimationFrame(update);
    } else {
      obj.textContent = prefix + end;
    }
  }
  
  requestAnimationFrame(update);
}

// Tooltip positioning
function setupTooltip() {
  const tooltip = document.getElementById("heatmap-tooltip");
  document.body.appendChild(tooltip);
}
