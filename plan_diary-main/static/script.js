let allPlans = [];
let currentPlan = null;
let selectedPlanId = null;
let editing = false;
let isReorderMode = false;
let draggedIndex = null;
let currentPlanExecutions = [];

// 🧭 PDS 3단계 탭 상태 관리 UI 요소
let activePdsTab = "plan";
const tabBtns = document.querySelectorAll(".pds-tab-btn");
const tabBadgePlan = document.getElementById("tab-badge-plan");
const tabBadgeDo = document.getElementById("tab-badge-do");
const tabBadgeSee = document.getElementById("tab-badge-see");
const btnSwitchToPlan = document.getElementById("btn-switch-to-plan");
const drawerGotoDoBtn = document.getElementById("drawer-goto-do-btn");

// HTML 요소
const form = document.getElementById("plan-form");
const formSection = document.getElementById("form-section");

const titleInput = document.getElementById("title");
const formPriorityDisplay = document.getElementById("form-priority-display");
const startDateInput = document.getElementById("start-date");
const endDateInput = document.getElementById("end-date");
const successCriteriaInput = document.getElementById("success-criteria");
const expectedMinutesInput = document.getElementById("expected-minutes");
const tagsInput = document.getElementById("tags");

const submitButton = document.getElementById("submit-button");
const cancelButton = document.getElementById("cancel-button");
const newPlanActionBtn = document.getElementById("new-plan-action-btn");
const newPlanFormBtn = document.getElementById("new-plan-form-btn");
const listNewPlanBtn = document.getElementById("list-new-plan-btn");

const formTitle = document.getElementById("form-title");
const modeText = document.getElementById("mode-text");

const planListSection = document.getElementById("plan-list-section");
const planListContainer = document.getElementById("plan-list");
const planCountSpan = document.getElementById("plan-count");
const reorderToggleBtn = document.getElementById("reorder-toggle-btn");
const reorderGuide = document.getElementById("reorder-guide");
const reorderDoneBtn = document.getElementById("reorder-done-btn");

// 🔍 검색 및 필터 UI 요소
const planSearchInput = document.getElementById("plan-search-input");
const searchClearBtn = document.getElementById("search-clear-btn");
const filterStatus = document.getElementById("filter-status");
const filterPriority = document.getElementById("filter-priority");
const filterTag = document.getElementById("filter-tag");
const sortBy = document.getElementById("sort-by");
const filterResetBtn = document.getElementById("filter-reset-btn");
const filterStatusSummary = document.getElementById("filter-status-summary");
const filterSummaryText = document.getElementById("filter-summary-text");
const planEmptyFilter = document.getElementById("plan-empty-filter");
const emptyResetBtn = document.getElementById("empty-reset-btn");

const currentPlanSection = document.getElementById("current-plan-section");
const displayTags = document.getElementById("display-tags");
const historySection = document.getElementById("history-section");
const historyCountBadge = document.getElementById("history-count-badge");
const historyEmpty = document.getElementById("history-empty");
const historyTableWrapper = document.getElementById("history-table-wrapper");
const historyListBody = document.getElementById("history-list-body");

// 📌 계획에 딸린 세부 할 일 (Subtasks) UI 요소
let currentPlanTasks = [];
const planTasksSection = document.getElementById("plan-tasks-section");
const planTasksCountBadge = document.getElementById("plan-tasks-count-badge");
const tasksProgressText = document.getElementById("tasks-progress-text");
const tasksProgressFill = document.getElementById("tasks-progress-fill");
const planTaskAddForm = document.getElementById("plan-task-add-form");
const taskTitleInput = document.getElementById("task-title-input");
const taskDueDateInput = document.getElementById("task-due-date-input");
const planTasksEmpty = document.getElementById("plan-tasks-empty");
const planTasksList = document.getElementById("plan-tasks-list");

const currentStatusBtn = document.getElementById("current-status-btn");
const displayStatusBadge = document.getElementById("display-status-badge");
const editButton = document.getElementById("edit-button");
const deleteButton = document.getElementById("delete-button");
const statusMessage = document.getElementById("status-message");

// ⚡ Section 04: 실행 기록 (Do) UI 요소
const executionSection = document.getElementById("execution-section");
const targetPlanBadge = document.getElementById("target-plan-badge");
const executionCountBadge = document.getElementById("execution-count-badge");
const executionForm = document.getElementById("execution-form");
const execStartTimeInput = document.getElementById("exec-start-time");
const execEndTimeInput = document.getElementById("exec-end-time");
const execActualMinutesInput = document.getElementById("exec-actual-minutes");
const execBlockerReasonInput = document.getElementById("exec-blocker-reason");
const execMemoInput = document.getElementById("exec-memo");
const execMarkCompleted = document.getElementById("exec-mark-completed");
const execSubmitBtn = document.getElementById("exec-submit-btn");
const btnNowStart = document.getElementById("btn-now-start");
const btnNowEnd = document.getElementById("btn-now-end");
const btnZeroStart = document.getElementById("btn-zero-start");
const btnZeroEnd = document.getElementById("btn-zero-end");
const executionEmpty = document.getElementById("execution-empty");
const executionTableWrapper = document.getElementById("execution-table-wrapper");
const execHistoryCount = document.getElementById("exec-history-count");
const execTotalMinutes = document.getElementById("exec-total-minutes");
const executionListBody = document.getElementById("execution-list-body");

// 📊 Section 05: 돌아보기 (See) UI 요소
let currentSeePeriod = "all";
let seeDataCache = null;

const seeSection = document.getElementById("see-section");
const seeRefreshBtn = document.getElementById("see-refresh-btn");
const seePeriodTabs = document.querySelectorAll(".period-tab-btn");
const seePeriodRangeText = document.getElementById("see-period-range-text");

const seeTotalPlansCount = document.getElementById("see-total-plans-count");
const seeCompletedCount = document.getElementById("see-completed-count");
const seeDelayedCount = document.getElementById("see-delayed-count");
const seeBlockedCount = document.getElementById("see-blocked-count");
const seeCompletionRate = document.getElementById("see-completion-rate");
const seeProgressFill = document.getElementById("see-progress-fill");
const seeTimeSummary = document.getElementById("see-time-summary");
const seeTimeDiff = document.getElementById("see-time-diff");

const kpiCardTotal = document.getElementById("kpi-card-total");
const kpiCardCompleted = document.getElementById("kpi-card-completed");
const kpiCardDelayed = document.getElementById("kpi-card-delayed");
const kpiCardBlocked = document.getElementById("kpi-card-blocked");
const kpiCardTime = document.getElementById("kpi-card-time");

const seeBlockerCountTag = document.getElementById("see-blocker-count-tag");
const seeBlockersEmpty = document.getElementById("see-blockers-empty");
const seeBlockersList = document.getElementById("see-blockers-list");
const seeTableBody = document.getElementById("see-table-body");

const actionBlockerSelect = document.getElementById("action-blocker-select");
const nextActionInput = document.getElementById("next-action-input");
const btnTransferToPlan = document.getElementById("btn-transfer-to-plan");
const nextActionRecentWrap = document.getElementById("next-action-recent-wrap");
const recentActionChips = document.getElementById("recent-action-chips");

// 🗂 Slide-over Drawer (옵션 B) UI 요소
const drawerBackdrop = document.getElementById("drawer-backdrop");
const planDetailDrawer = document.getElementById("plan-detail-drawer");
const drawerCloseBtn = document.getElementById("drawer-close-btn");

// 슬라이드 드로어 열기/닫기 제어 함수 (데스크톱 Modeless Side-Peek & 모바일 Modal Sheet)
function openPlanDrawer() {
    if (planDetailDrawer) {
        if (drawerBackdrop && window.innerWidth <= 768) {
            drawerBackdrop.classList.add("active");
        }
        planDetailDrawer.classList.add("open");
        document.body.classList.add("drawer-open");

        if (window.innerWidth <= 768) {
            document.body.style.overflow = "hidden"; // 모바일에서만 배경 스크롤 방지
        } else {
            document.body.style.overflow = ""; // 데스크톱에서는 메인창 자유 스크롤 및 동시 조작 허용
        }
    }
}

function closePlanDrawer() {
    if (planDetailDrawer) {
        if (drawerBackdrop) {
            drawerBackdrop.classList.remove("active");
        }
        planDetailDrawer.classList.remove("open");
        document.body.classList.remove("drawer-open");
        document.body.style.overflow = "";
    }
}

// 드로어 닫기 이벤트 리스너 등록
if (drawerCloseBtn) {
    drawerCloseBtn.addEventListener("click", closePlanDrawer);
}
if (drawerBackdrop) {
    drawerBackdrop.addEventListener("click", closePlanDrawer);
}
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && planDetailDrawer && planDetailDrawer.classList.contains("open")) {
        closePlanDrawer();
    }
});

// 창 크기 변경 시 모바일/데스크톱 반응형 스크롤 및 딤 오버레이 동적 조정
window.addEventListener("resize", () => {
    if (planDetailDrawer && planDetailDrawer.classList.contains("open")) {
        if (window.innerWidth <= 768) {
            if (drawerBackdrop) drawerBackdrop.classList.add("active");
            document.body.style.overflow = "hidden";
        } else {
            if (drawerBackdrop) drawerBackdrop.classList.remove("active");
            document.body.style.overflow = "";
        }
    }
});

// 페이지 시작
document.addEventListener("DOMContentLoaded", loadPlans);

// 모든 저장된 계획 가져오기
async function loadPlans() {
    try {
        const response = await fetch("/api/plans");
        const data = await response.json();

        allPlans = data.plans || [];

        if (allPlans.length === 0) {
            currentPlan = null;
            selectedPlanId = null;
            planListSection.classList.add("hidden");
            currentPlanSection.classList.add("hidden");
            if (planTasksSection) planTasksSection.classList.add("hidden");
            if (historySection) historySection.classList.add("hidden");
            if (executionSection) executionSection.classList.add("hidden");
            showCreateMode();
            await loadSeeData();
            updateTabViews();
            return;
        }

        // 계획이 있는 경우
        planListSection.classList.remove("hidden");

        // 이전에 선택된 계획이 유지되거나, 첫 번째 계획을 선택
        if (!selectedPlanId || !allPlans.some(p => p.id === selectedPlanId)) {
            selectedPlanId = allPlans[0].id;
        }

        currentPlan = allPlans.find(p => p.id === selectedPlanId) || allPlans[0];
        selectedPlanId = currentPlan.id;

        // 태그 필터 옵션 갱신 & 필터링 렌더링
        updateTagFilterOptions(allPlans);
        applyFiltersAndRender();
        displayPlan(currentPlan);

        currentPlanSection.classList.remove("hidden");
        if (planTasksSection) planTasksSection.classList.remove("hidden");
        if (historySection) historySection.classList.remove("hidden");
        if (executionSection) executionSection.classList.remove("hidden");

        // 📌 [Subtasks] 선택된 계획의 세부 할 일 목록 로드
        await loadPlanTasks(selectedPlanId);

        // [T06-C08] 선택된 계획의 수정 이력(고치기 전 계획들) 로드
        await loadPlanHistory(selectedPlanId);

        // [Do] 선택된 계획의 실행 기록 로드
        await loadPlanExecutions(selectedPlanId);

        // [See] 돌아보기 대시보드 통계 로드
        await loadSeeData();

        if (!editing) {
            showViewMode();
        }

        // 🧭 URL 해시 및 탭 뷰 동기화
        const initialHash = window.location.hash.replace("#", "").toLowerCase();
        if (["plan", "do", "see"].includes(initialHash)) {
            activePdsTab = initialHash;
        }
        updateTabViews();

    } catch (error) {
        console.error(error);
        showStatus("서버와 연결할 수 없습니다.", "error");
    }
}

// 🧭 3단계 탭 뷰 가시성 제어 함수 (스크롤 방지 및 모듈형 뷰 전환)
function updateTabViews() {
    // 탭 버튼 active 클래스 갱신
    tabBtns.forEach(btn => {
        if (btn.dataset.tab === activePdsTab) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    if (activePdsTab === "plan") {
        // PLAN 탭: 계획 작성 폼과 계획 목록 노출
        if (allPlans.length === 0) {
            showCreateMode();
            if (planListSection) planListSection.classList.add("hidden");
        } else {
            if (!editing) showViewMode();
            if (planListSection) planListSection.classList.remove("hidden");
        }
        if (executionSection) executionSection.classList.add("hidden");
        if (seeSection) seeSection.classList.add("hidden");
    } else if (activePdsTab === "do") {
        // DO 탭: 실행 기록 폼 및 누적 이력 노출 (계획 작성/목록 숨김)
        if (formSection) formSection.classList.add("hidden");
        if (planListSection) planListSection.classList.add("hidden");
        if (executionSection) executionSection.classList.remove("hidden");
        if (seeSection) seeSection.classList.add("hidden");
    } else if (activePdsTab === "see") {
        // SEE 탭: 돌아보기 대시보드만 노출
        if (formSection) formSection.classList.add("hidden");
        if (planListSection) planListSection.classList.add("hidden");
        if (executionSection) executionSection.classList.add("hidden");
        if (seeSection) seeSection.classList.remove("hidden");
    }

    updateTabBadges();
}

// 탭 뱃지(카운터) 갱신
function updateTabBadges() {
    if (tabBadgePlan) {
        tabBadgePlan.textContent = (allPlans ? allPlans.length : 0);
    }
    if (tabBadgeDo) {
        let totalExecs = 0;
        if (allPlans) {
            totalExecs = allPlans.reduce((sum, p) => sum + (p.execution_count || 0), 0);
        }
        tabBadgeDo.textContent = totalExecs;
    }
    if (tabBadgeSee) {
        if (seeDataCache && seeDataCache.summary) {
            tabBadgeSee.textContent = `${seeDataCache.summary.completion_rate}%`;
        } else if (allPlans && allPlans.length > 0) {
            const completed = allPlans.filter(p => p.status === "완료").length;
            const rate = Math.round((completed / allPlans.length) * 100);
            tabBadgeSee.textContent = `${rate}%`;
        } else {
            tabBadgeSee.textContent = "0%";
        }
    }
}

// 탭 전환 핸들러
function switchPdsTab(targetTab, shouldScroll = false) {
    if (!["plan", "do", "see"].includes(targetTab)) return;
    activePdsTab = targetTab;
    window.location.hash = targetTab;

    updateTabViews();

    if (shouldScroll) {
        window.scrollTo({ top: 0, behavior: "smooth" });
    }
}

// 🏷 태그 파싱 유틸리티 (쉼표 구분 문자열 -> 배열)
function parseTags(tagStr) {
    if (!tagStr) return [];
    return String(tagStr)
        .split(",")
        .map(t => t.trim())
        .filter(t => t.length > 0);
}

// 🏷 태그 뱃지 HTML 생성 유틸리티
function renderTagBadgesHtml(tagStr, isClickable = true) {
    const tags = parseTags(tagStr);
    if (tags.length === 0) return "";
    return `
        <div class="plan-item-tags">
            ${tags.map(t => `<span class="plan-tag-pill ${isClickable ? 'clickable-tag' : ''}" data-tag="${escapeHtml(t)}" title="'#${escapeHtml(t)}' 태그로 필터링">#${escapeHtml(t)}</span>`).join("")}
        </div>
    `;
}

// 🏷 특정 태그 클릭 시 즉시 필터링 적용
function filterByTag(tagName) {
    if (!tagName) return;
    if (filterTag) {
        let matched = false;
        for (let i = 0; i < filterTag.options.length; i++) {
            if (filterTag.options[i].value.toLowerCase() === tagName.toLowerCase()) {
                filterTag.value = filterTag.options[i].value;
                matched = true;
                break;
            }
        }
        if (!matched && planSearchInput) {
            planSearchInput.value = tagName;
        }
    } else if (planSearchInput) {
        planSearchInput.value = tagName;
    }
    applyFiltersAndRender();
}

// 🏷 전체 계획에서 고유 태그를 추출하여 <select id="filter-tag"> 옵션 갱신
function updateTagFilterOptions(plans) {
    if (!filterTag) return;
    const currentVal = filterTag.value;
    const tagSet = new Set();

    plans.forEach(plan => {
        const tags = parseTags(plan.tags);
        tags.forEach(t => tagSet.add(t));
    });

    const sortedTags = Array.from(tagSet).sort();
    let optionsHtml = '<option value="all">전체 태그</option>';
    sortedTags.forEach(t => {
        optionsHtml += `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`;
    });
    filterTag.innerHTML = optionsHtml;

    if (sortedTags.includes(currentVal)) {
        filterTag.value = currentVal;
    } else {
        filterTag.value = "all";
    }
}

// 🔍 모든 필터 및 검색어 초기화
function resetFilters(shouldRender = true) {
    if (planSearchInput) planSearchInput.value = "";
    if (searchClearBtn) searchClearBtn.classList.add("hidden");
    if (filterStatus) filterStatus.value = "all";
    if (filterPriority) filterPriority.value = "all";
    if (filterTag) filterTag.value = "all";
    if (sortBy) sortBy.value = "priority-asc";

    if (shouldRender) {
        applyFiltersAndRender();
    }
}

// 🔍 조건 필터 및 검색 적용 후 목록 렌더링
function applyFiltersAndRender() {
    if (allPlans.length === 0) {
        renderPlanList([]);
        return;
    }

    const query = planSearchInput ? planSearchInput.value.trim().toLowerCase() : "";
    const status = filterStatus ? filterStatus.value : "all";
    const priority = filterPriority ? filterPriority.value : "all";
    const tag = filterTag ? filterTag.value : "all";
    const sort = sortBy ? sortBy.value : "priority-asc";

    // 검색어 지우기(X) 버튼 노출 제어
    if (searchClearBtn) {
        if (query.length > 0) {
            searchClearBtn.classList.remove("hidden");
        } else {
            searchClearBtn.classList.add("hidden");
        }
    }

    // 조건별 필터링
    let filtered = allPlans.filter(plan => {
        // 1. 상태 필터 (진행중 / 완료 / 지연 / 막힘)
        if (status !== "all") {
            if (status === "지연") {
                if (!plan.is_delayed) return false;
            } else if (status === "막힘") {
                if (!plan.blocker_count || plan.blocker_count <= 0) return false;
            } else if (plan.status !== status) {
                return false;
            }
        }

        // 2. 우선순위 필터 (1순위, 2순위, 3순위)
        if (priority !== "all" && plan.current_priority !== priority) {
            return false;
        }

        // 3. 태그 필터
        if (tag !== "all") {
            const planTags = parseTags(plan.tags);
            if (!planTags.some(t => t.toLowerCase() === tag.toLowerCase())) {
                return false;
            }
        }

        // 4. 텍스트 검색 (계획명, 태그, 성공 기준)
        if (query) {
            const matchTitle = (plan.title || "").toLowerCase().includes(query);
            const matchTags = (plan.tags || "").toLowerCase().includes(query);
            const matchCriteria = (plan.current_success_criteria || "").toLowerCase().includes(query);
            if (!matchTitle && !matchTags && !matchCriteria) {
                return false;
            }
        }

        return true;
    });

    // 정렬 기준 적용
    filtered.sort((a, b) => {
        if (sort === "date-desc") {
            return (b.id || 0) - (a.id || 0);
        } else if (sort === "due-asc") {
            const dueA = a.current_end_date || "";
            const dueB = b.current_end_date || "";
            if (dueA !== dueB) return dueA.localeCompare(dueB);
            return (b.id || 0) - (a.id || 0);
        } else if (sort === "time-asc") {
            const timeA = Number(a.current_expected_minutes || 0);
            const timeB = Number(b.current_expected_minutes || 0);
            if (timeA !== timeB) return timeA - timeB;
            return (b.id || 0) - (a.id || 0);
        } else {
            // priority-asc: 1순위, 2순위, 3순위... 순
            const getRank = (p) => {
                const m = String(p.current_priority || "").match(/(\d+)순위/);
                return m ? parseInt(m[1], 10) : 999999;
            };
            const rankA = getRank(a);
            const rankB = getRank(b);
            if (rankA !== rankB) return rankA - rankB;
            return (b.id || 0) - (a.id || 0);
        }
    });

    // 필터 요약 표시
    const isFilterActive = (query !== "" || status !== "all" || priority !== "all" || tag !== "all");
    if (filterStatusSummary && filterSummaryText) {
        if (isFilterActive) {
            filterStatusSummary.classList.remove("hidden");
            const filterTerms = [];
            if (query) filterTerms.push(`검색어 "${query}"`);
            if (status !== "all") filterTerms.push(`상태: ${status}`);
            if (priority !== "all") filterTerms.push(`우선순위: ${priority}`);
            if (tag !== "all") filterTerms.push(`태그: #${tag}`);
            filterSummaryText.innerHTML = `<strong>${filtered.length}개</strong> 결과 (전체 ${allPlans.length}개 중) · <em>${filterTerms.join(" | ")}</em>`;
        } else {
            filterStatusSummary.classList.add("hidden");
            filterSummaryText.textContent = "";
        }
    }

    // 계획 개수 표시 (필터 활성화 시 '필터된 개수/전체 개수')
    if (planCountSpan) {
        planCountSpan.textContent = isFilterActive ? `${filtered.length} / ${allPlans.length}` : allPlans.length;
    }

    // 조건에 맞는 계획이 없을 때 안내 노출
    if (planEmptyFilter) {
        if (allPlans.length > 0 && filtered.length === 0) {
            planEmptyFilter.classList.remove("hidden");
            planListContainer.classList.add("hidden");
        } else {
            planEmptyFilter.classList.add("hidden");
            planListContainer.classList.remove("hidden");
        }
    }

    renderPlanList(filtered);
}

// 계획 목록 렌더링
function renderPlanList(plansToRender = allPlans) {
    planListContainer.innerHTML = "";

    if (isReorderMode) {
        planListContainer.classList.add("reordering");
    } else {
        planListContainer.classList.remove("reordering");
    }

    const list = plansToRender || [];

    list.forEach((plan, index) => {
        const allIndex = allPlans.findIndex(p => p.id === plan.id);
        const isCompleted = (plan.status === "완료");
        const item = document.createElement("div");
        item.className = `plan-item ${plan.id === selectedPlanId ? "active" : ""} ${isCompleted ? "completed" : ""}`;
        item.dataset.id = plan.id;
        item.dataset.index = (allIndex >= 0 ? allIndex : index);

        // 우선순위 스타일 클래스
        const pVal = plan.current_priority || "1순위";
        let priorityClass = `plan-priority-${pVal}`;
        if (!["1순위", "2순위", "3순위"].includes(pVal)) {
            priorityClass = "plan-priority-rank";
        }

        if (plan.is_delayed) {
            item.classList.add("delayed-item");
        }
        if (plan.blocker_count && plan.blocker_count > 0) {
            item.classList.add("blocked-item");
        }

        const tagsHtml = renderTagBadgesHtml(plan.tags);

        item.innerHTML = `
            <div class="drag-handle" title="마우스로 클릭하여 위아래로 슬라이드(드래그)하세요">⠿</div>
            <div class="reorder-arrows">
                <button type="button" class="reorder-arrow-btn move-up" title="한 단계 위로 이동" ${allIndex <= 0 ? "disabled style='opacity:0.3;cursor:default;'" : ""}>▲</button>
                <button type="button" class="reorder-arrow-btn move-down" title="한 단계 아래로 이동" ${(allIndex < 0 || allIndex === allPlans.length - 1) ? "disabled style='opacity:0.3;cursor:default;'" : ""}>▼</button>
            </div>
            <div class="plan-item-info">
                <div class="plan-item-header">
                    <span class="plan-item-title">${escapeHtml(plan.title)}</span>
                    <span class="plan-status-badge status-${isCompleted ? "완료" : "진행중"}">
                        ${isCompleted ? "완료" : "진행중"}
                    </span>
                    ${plan.is_delayed ? `<span class="plan-status-badge status-지연" title="마감일 초과 미완료 (T06-C30)">⏰ 지연</span>` : ""}
                    ${(plan.blocker_count && plan.blocker_count > 0) ? `<span class="plan-status-badge status-막힘" title="실행 중 병목 발생">🚧 막힘</span>` : ""}
                    <span class="plan-priority-badge ${priorityClass}">${escapeHtml(pVal)}</span>
                    ${(plan.history_count && plan.history_count > 0) ? `<span class="plan-history-count-badge" title="고치기 전 계획 ${plan.history_count}건 보존 중">이력 ${plan.history_count}건</span>` : ""}
                </div>
                ${tagsHtml}
                <div class="plan-item-meta">
                    <span>📅 ${escapeHtml(formatPeriod(plan.current_start_date, plan.current_end_date))}</span>
                    <span>⏱ ${escapeHtml(formatMinutes(plan.current_expected_minutes))}</span>
                    ${(plan.task_count && plan.task_count > 0)
                        ? `<span class="plan-task-count-badge" title="딸린 할 일 ${plan.task_count}개 중 ${plan.completed_task_count || 0}개 완료">☑️ 할 일 ${plan.completed_task_count || 0}/${plan.task_count}</span>`
                        : ""
                    }
                </div>
            </div>
            <div class="plan-item-actions">
                ${isCompleted
                    ? `<button type="button" class="plan-revert-btn" title="이 계획을 다시 진행중으로 변경">↺ 다시 진행</button>`
                    : `<button type="button" class="plan-complete-btn" title="이 계획을 완료로 변경">✓ 완료하기</button>`
                }
                <button type="button" class="plan-do-btn" title="이 계획의 실행(DO)을 기록하러 이동">
                    ⚡ 실행(Do)
                </button>
                <button type="button" class="plan-select-btn" title="계획 상세 및 수정 이력 열기">
                    ${plan.id === selectedPlanId ? "상세보기 ❯" : "상세보기 ❯"}
                </button>
                <button type="button" class="plan-delete-btn" title="계획 삭제">
                    삭제
                </button>
            </div>
        `;

        // 실행(Do) 버튼 클릭 시 해당 계획 선택 후 DO 탭으로 전환
        const doBtn = item.querySelector(".plan-do-btn");
        if (doBtn) {
            doBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                selectPlan(plan.id);
                switchPdsTab("do", true);
            });
        }

        // 태그 뱃지 클릭 시 태그 필터링
        item.querySelectorAll(".plan-tag-pill").forEach(pill => {
            pill.addEventListener("click", (e) => {
                e.stopPropagation();
                filterByTag(pill.dataset.tag);
            });
        });

        // 카드 클릭 시 선택 및 우측 슬라이드 드로어 열기 (재배치 모드가 아닐 때, 또는 상태/삭제/화살표/실행 버튼이 아닐 때)
        item.onclick = (e) => {
            if (e.target.closest(".plan-delete-btn") ||
                e.target.closest(".reorder-arrow-btn") ||
                e.target.closest(".plan-complete-btn") ||
                e.target.closest(".plan-revert-btn") ||
                e.target.closest(".plan-do-btn") ||
                e.target.closest(".plan-tag-pill")) {
                return;
            }
            if (isReorderMode && !e.target.closest(".plan-select-btn")) return;
            selectPlan(plan.id);
            openPlanDrawer();
        };

        // 완료하기 / 다시 진행 버튼 이벤트
        const statusActionBtn = item.querySelector(".plan-complete-btn, .plan-revert-btn");
        if (statusActionBtn) {
            statusActionBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                const target = isCompleted ? "진행중" : "완료";
                togglePlanStatus(plan.id, target);
            });
        }

        // 삭제 버튼 이벤트
        const deleteBtn = item.querySelector(".plan-delete-btn");
        deleteBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            deletePlan(plan.id, plan.title);
        });

        // 위/아래 화살표 버튼 이벤트
        const moveUpBtn = item.querySelector(".move-up");
        const moveDownBtn = item.querySelector(".move-down");

        moveUpBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            if (allIndex > 0) {
                movePlan(allIndex, allIndex - 1);
            }
        });

        moveDownBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            if (allIndex >= 0 && allIndex < allPlans.length - 1) {
                movePlan(allIndex, allIndex + 1);
            }
        });

        // 드래그 앤 드롭 (슬라이드) 이벤트 설정
        if (isReorderMode) {
            item.setAttribute("draggable", "true");

            item.addEventListener("dragstart", (e) => {
                draggedIndex = allIndex;
                item.classList.add("dragging");
                e.dataTransfer.effectAllowed = "move";
                e.dataTransfer.setData("text/plain", allIndex);
            });

            item.addEventListener("dragover", (e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = "move";
                item.classList.add("drag-over");
            });

            item.addEventListener("dragleave", () => {
                item.classList.remove("drag-over");
            });

            item.addEventListener("drop", (e) => {
                e.preventDefault();
                item.classList.remove("drag-over");
                if (draggedIndex !== null && draggedIndex !== allIndex) {
                    movePlan(draggedIndex, allIndex);
                }
            });

            item.addEventListener("dragend", () => {
                item.classList.remove("dragging");
                document.querySelectorAll(".drag-over").forEach(el => el.classList.remove("drag-over"));
                draggedIndex = null;
            });
        }

        planListContainer.appendChild(item);
    });
}

let isStatusUpdating = false;

// 계획 상태 전환 (진행중 <-> 완료)
// [요구사항 4 & 5] 완료 버튼을 2번 눌러도 완료 기록은 한번만 남고, 돌아보기 완료 수도 1만 증가하도록 방어
async function togglePlanStatus(id, explicitStatus = null) {
    if (isStatusUpdating) {
        return;
    }
    isStatusUpdating = true;

    // 더블 클릭 및 중복 전송 방지: 버튼 비활성화 시각 효과
    const buttons = document.querySelectorAll(".plan-complete-btn, .plan-revert-btn, #current-status-btn");
    buttons.forEach(b => {
        b.style.pointerEvents = "none";
        b.style.opacity = "0.6";
    });

    try {
        const bodyData = {};
        if (explicitStatus) {
            bodyData.status = explicitStatus;
        }

        const response = await fetch(`/api/plan/${id}/status`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(bodyData)
        });
        const result = await response.json();

        if (!response.ok) {
            showStatus(result.message || "상태 변경 실패", "error");
            return;
        }

        showStatus(result.message, "success");
        await loadPlans();
        await loadSeeData();

    } catch (error) {
        console.error(error);
        showStatus("서버와 연결할 수 없습니다.", "error");
    } finally {
        isStatusUpdating = false;
        buttons.forEach(b => {
            b.style.pointerEvents = "";
            b.style.opacity = "";
        });
    }
}

// 계획 순서 이동 및 우선순위 갱신
async function movePlan(fromIndex, toIndex) {
    if (fromIndex === toIndex || fromIndex < 0 || toIndex < 0 || fromIndex >= allPlans.length || toIndex >= allPlans.length) {
        return;
    }

    // 배열 내 위치 변경
    const moved = allPlans.splice(fromIndex, 1)[0];
    allPlans.splice(toIndex, 0, moved);

    // 우선순위 텍스트(1순위, 2순위...) 재할당
    allPlans.forEach((plan, idx) => {
        plan.current_priority = `${idx + 1}순위`;
    });

    applyFiltersAndRender();

    if (currentPlan) {
        displayPlan(currentPlan);
    }

    // 백엔드에 즉시 저장
    await savePriorityOrder();
}

// 우선순위 저장 API 호출
async function savePriorityOrder() {
    const order = allPlans.map(p => p.id);

    try {
        const response = await fetch("/api/plans/reorder", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ order })
        });

        const result = await response.json();

        if (!response.ok) {
            showStatus(result.message || "우선순위 저장 실패", "error");
            return;
        }

        showStatus("우선순위가 성공적으로 변경되었습니다.", "success");

    } catch (error) {
        console.error(error);
        showStatus("서버와 연결할 수 없습니다.", "error");
    }
}

// 우선순위 변경 모드 토글
function toggleReorderMode() {
    isReorderMode = !isReorderMode;

    if (isReorderMode) {
        // 우선순위 조정 모드 진입 시 전체 순서 조정을 위해 필터 리셋
        resetFilters(false);
        if (sortBy) sortBy.value = "priority-asc";
        reorderGuide.classList.remove("hidden");
        reorderToggleBtn.textContent = "✅ 변경 완료";
        reorderToggleBtn.className = "primary-button";
    } else {
        reorderGuide.classList.add("hidden");
        reorderToggleBtn.textContent = "🔄 우선순위 변경";
        reorderToggleBtn.className = "secondary-button";
    }

    applyFiltersAndRender();
}

// 특정 계획 선택
function selectPlan(id) {
    selectedPlanId = id;
    currentPlan = allPlans.find(p => p.id === id);

    if (currentPlan) {
        applyFiltersAndRender();
        displayPlan(currentPlan);

        // 📌 [Subtasks] 선택된 계획의 세부 할 일 목록 불러오기
        loadPlanTasks(id);

        // [T06-C08] 선택된 계획의 수정 이력(고치기 전 계획) 불러오기
        loadPlanHistory(id);

        // [Do] 선택된 계획의 실행 기록(이전 기록 누적 보존) 불러오기
        loadPlanExecutions(id);

        if (editing) {
            showEditMode();
        } else {
            showViewMode();
        }
    }
}

// 계획 화면에 표시
function displayPlan(plan) {
    const status = plan.status || "진행중";
    const isCompleted = (status === "완료");

    // 상태 뱃지
    if (displayStatusBadge) {
        displayStatusBadge.textContent = status;
        displayStatusBadge.className = `plan-status-badge status-${status}`;
    }

    if (targetPlanBadge) {
        targetPlanBadge.textContent = `[선택: ${plan.title}]`;
    }

    // 상태 전환 버튼
    if (currentStatusBtn) {
        if (isCompleted) {
            currentStatusBtn.textContent = "↺ 다시 진행중으로";
            currentStatusBtn.className = "status-toggle-btn is-completed";
        } else {
            currentStatusBtn.textContent = "✓ 완료하기";
            currentStatusBtn.className = "status-toggle-btn";
        }
    }

    // 현재 계획 세부 정보
    document.getElementById("display-title").textContent = plan.title;
    document.getElementById("display-priority").textContent = plan.current_priority || "1순위";
    document.getElementById("display-period").textContent = formatPeriod(
        plan.current_start_date,
        plan.current_end_date
    );
    document.getElementById("display-success").textContent = plan.current_success_criteria;
    document.getElementById("display-time").textContent = formatMinutes(plan.current_expected_minutes);
    document.getElementById("display-updated").textContent = plan.updated_at;

    // 🏷 태그 목록 표시
    if (displayTags) {
        const tags = parseTags(plan.tags);
        if (tags.length > 0) {
            displayTags.innerHTML = tags
                .map(t => `<span class="plan-tag-pill clickable-tag" data-tag="${escapeHtml(t)}" title="'#${escapeHtml(t)}' 태그로 필터링">#${escapeHtml(t)}</span>`)
                .join(" ");
            displayTags.querySelectorAll(".plan-tag-pill").forEach(pill => {
                pill.addEventListener("click", (e) => {
                    e.stopPropagation();
                    filterByTag(pill.dataset.tag);
                });
            });
        } else {
            displayTags.innerHTML = `<span class="no-tags">등록된 태그 없음</span>`;
        }
    }
}

// [T06-C08] 특정 계획의 수정 이력 불러오기 (고치기 전 계획 보존)
async function loadPlanHistory(planId) {
    if (!historySection) return;
    if (!planId) {
        historySection.classList.add("hidden");
        return;
    }

    try {
        const response = await fetch(`/api/plan/${planId}/history`);
        const data = await response.json();
        const histories = data.history || [];
        renderPlanHistory(histories);
    } catch (error) {
        console.error("수정 이력 조회 실패:", error);
    }
}

// [T06-C08] 수정 이력 표 렌더링
function renderPlanHistory(histories) {
    if (!historySection) return;
    historySection.classList.remove("hidden");

    if (historyCountBadge) {
        historyCountBadge.textContent = `이력 ${histories.length}건`;
    }

    if (!histories || histories.length === 0) {
        if (historyEmpty) historyEmpty.classList.remove("hidden");
        if (historyTableWrapper) historyTableWrapper.classList.add("hidden");
        if (historyListBody) historyListBody.innerHTML = "";
        return;
    }

    if (historyEmpty) historyEmpty.classList.add("hidden");
    if (historyTableWrapper) historyTableWrapper.classList.remove("hidden");
    if (historyListBody) historyListBody.innerHTML = "";

    histories.forEach(item => {
        const tr = document.createElement("tr");

        const pVal = item.priority || "1순위";
        let priorityClass = `plan-priority-${pVal}`;
        if (!["1순위", "2순위", "3순위"].includes(pVal)) {
            priorityClass = "plan-priority-rank";
        }

        const itemTags = parseTags(item.tags);
        const tagsHtml = itemTags.length > 0
            ? `<div class="history-tags">${itemTags.map(t => `<span class="plan-tag-pill history-tag-pill">#${escapeHtml(t)}</span>`).join(" ")}</div>`
            : "";

        tr.innerHTML = `
            <td><span class="version-tag">v${item.version} (수정 전)</span></td>
            <td class="history-time-col">${escapeHtml(item.modified_at)}</td>
            <td>
                <div class="history-title-text">${escapeHtml(item.title)}</div>
                ${tagsHtml}
                <div class="history-criteria-text" title="${escapeHtml(item.success_criteria)}">
                    🎯 ${escapeHtml(item.success_criteria)}
                </div>
            </td>
            <td><span class="plan-priority-badge ${priorityClass}">${escapeHtml(pVal)}</span></td>
            <td class="history-period-col">${escapeHtml(formatPeriod(item.start_date, item.end_date))}</td>
            <td>${escapeHtml(formatMinutes(item.expected_minutes))}</td>
            <td>
                <button type="button" class="history-restore-btn" title="이 버전으로 현재 계획 복원">
                    ↺ 복원
                </button>
            </td>
        `;

        const restoreBtn = tr.querySelector(".history-restore-btn");
        if (restoreBtn) {
            restoreBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                restoreHistoryVersion(item.plan_id, item.id, item.version, item.title);
            });
        }

        historyListBody.appendChild(tr);
    });
}

// [T06-C08] 수정 이력 버전으로 복원하기
async function restoreHistoryVersion(planId, historyId, version, title) {
    if (!confirm(`'${title}' (v${version}) 수정 전 버전으로 계획을 복원하시겠습니까?\n현재 계획 내용은 새로운 이력으로 안전하게 보존됩니다.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/plan/${planId}/history/${historyId}/restore`, {
            method: "POST"
        });
        const result = await response.json();

        if (!response.ok) {
            showStatus(result.message || "복원에 실패했습니다.", "error");
            return;
        }

        showStatus(result.message, "success");
        await loadPlans();

    } catch (error) {
        console.error(error);
        showStatus("서버와 연결할 수 없습니다.", "error");
    }
}


// ==========================================================
// 📌 계획에 딸린 세부 할 일 (Subtasks / Plan Tasks) 로직
// [요구사항] 계획별 딸린 할 일 추가, 수정, 삭제, 완료 토글 및 보존
// ==========================================================

async function loadPlanTasks(planId) {
    if (!planTasksSection) return;
    if (!planId) {
        planTasksSection.classList.add("hidden");
        return;
    }
    planTasksSection.classList.remove("hidden");

    try {
        const response = await fetch(`/api/plan/${planId}/tasks`);
        const data = await response.json();
        if (data.success) {
            currentPlanTasks = data.tasks || [];
            renderPlanTasks(currentPlanTasks, data.total_count || 0, data.completed_count || 0);
        }
    } catch (error) {
        console.error("세부 할 일 조회 실패:", error);
    }
}

function renderPlanTasks(tasks, totalCount, completedCount) {
    if (!planTasksList) return;

    // 개수 뱃지 갱신
    if (planTasksCountBadge) {
        planTasksCountBadge.textContent = `할 일 ${totalCount}건`;
    }

    // 진행률 프로그레스 바 갱신
    const pct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;
    if (tasksProgressText) {
        tasksProgressText.textContent = `완료율: ${pct}% (${completedCount} / ${totalCount}개)`;
    }
    if (tasksProgressFill) {
        tasksProgressFill.style.width = `${pct}%`;
    }

    // 빈 상태 처리
    if (!tasks || tasks.length === 0) {
        if (planTasksEmpty) planTasksEmpty.classList.remove("hidden");
        planTasksList.innerHTML = "";
        return;
    }

    if (planTasksEmpty) planTasksEmpty.classList.add("hidden");
    planTasksList.innerHTML = "";

    tasks.forEach(task => {
        const isComp = (task.is_completed === 1 || task.is_completed === true);
        const item = document.createElement("div");
        item.className = `task-item ${isComp ? "completed" : ""}`;
        item.dataset.taskId = task.id;

        const dueHtml = task.due_date ? `<span class="task-due-badge" title="마감일: ${escapeHtml(task.due_date)}">📅 ${escapeHtml(task.due_date)}</span>` : "";

        item.innerHTML = `
            <div class="task-left">
                <input type="checkbox" class="task-checkbox" title="완료 여부 변경" ${isComp ? "checked" : ""}>
                <span class="task-title ${isComp ? "completed" : ""}">${escapeHtml(task.title)}</span>
                ${dueHtml}
            </div>
            <div class="task-actions">
                <button type="button" class="task-btn-edit" title="이 할 일 수정">수정</button>
                <button type="button" class="task-btn-del" title="이 할 일 삭제">삭제</button>
            </div>
        `;

        // 체크박스 완료 토글
        const chk = item.querySelector(".task-checkbox");
        if (chk) {
            chk.addEventListener("change", async () => {
                await toggleTaskCompletion(task.id, chk.checked ? 1 : 0);
            });
        }

        // 수정 버튼 클릭 시 인라인 수정 폼으로 전환
        const editBtn = item.querySelector(".task-btn-edit");
        if (editBtn) {
            editBtn.addEventListener("click", () => {
                enableInlineTaskEdit(item, task);
            });
        }

        // 삭제 버튼 클릭
        const delBtn = item.querySelector(".task-btn-del");
        if (delBtn) {
            delBtn.addEventListener("click", async () => {
                await deleteTask(task.id, task.title);
            });
        }

        planTasksList.appendChild(item);
    });
}

// 인라인 수정 모드 활성화
function enableInlineTaskEdit(item, task) {
    const isComp = (task.is_completed === 1);
    item.innerHTML = `
        <div class="task-inline-edit-row">
            <input type="text" class="task-inline-input" value="${escapeHtml(task.title)}" maxlength="120" required>
            <input type="date" class="task-inline-date" value="${escapeHtml(task.due_date || '')}" title="마감일">
            <button type="button" class="task-btn-save">저장</button>
            <button type="button" class="task-btn-cancel">취소</button>
        </div>
    `;

    const input = item.querySelector(".task-inline-input");
    const dateInput = item.querySelector(".task-inline-date");
    const saveBtn = item.querySelector(".task-btn-save");
    const cancelBtn = item.querySelector(".task-btn-cancel");

    input.focus();

    saveBtn.addEventListener("click", async () => {
        const newTitle = input.value.trim();
        if (!newTitle) {
            showStatus("할 일 내용을 입력해주세요.", "error");
            return;
        }
        const newDueDate = dateInput.value;
        await saveTaskEdit(task.id, newTitle, newDueDate, isComp);
    });

    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            saveBtn.click();
        } else if (e.key === "Escape") {
            loadPlanTasks(selectedPlanId);
        }
    });

    cancelBtn.addEventListener("click", () => {
        loadPlanTasks(selectedPlanId);
    });
}

// 할 일 수정 저장 API 호출
async function saveTaskEdit(taskId, title, dueDate, isCompleted) {
    if (!selectedPlanId) return;
    try {
        const response = await fetch(`/api/plan/${selectedPlanId}/task/${taskId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title: title,
                due_date: dueDate,
                is_completed: isCompleted ? 1 : 0
            })
        });
        const result = await response.json();
        if (!response.ok) {
            showStatus(result.message || "수정에 실패했습니다.", "error");
            return;
        }
        showStatus("세부 할 일이 수정되었습니다.", "success");
        await loadPlanTasks(selectedPlanId);
        await loadPlans();
    } catch (err) {
        console.error(err);
        showStatus("서버와 통신 중 오류가 발생했습니다.", "error");
    }
}

// 할 일 완료 여부 토글 API 호출
async function toggleTaskCompletion(taskId, isCompleted) {
    if (!selectedPlanId) return;
    try {
        const response = await fetch(`/api/plan/${selectedPlanId}/task/${taskId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_completed: isCompleted })
        });
        const result = await response.json();
        if (!response.ok) {
            showStatus(result.message || "상태 변경 실패", "error");
            return;
        }
        showStatus(isCompleted ? "할 일을 완료했습니다! 🎉" : "할 일을 다시 진행중으로 변경했습니다.", "success");
        await loadPlanTasks(selectedPlanId);
        await loadPlans();
    } catch (err) {
        console.error(err);
        showStatus("서버와 통신 중 오류가 발생했습니다.", "error");
    }
}

// 할 일 삭제 API 호출
async function deleteTask(taskId, title) {
    if (!selectedPlanId) return;
    if (!confirm(`'${title}' 할 일을 삭제하시겠습니까?`)) {
        return;
    }
    try {
        const response = await fetch(`/api/plan/${selectedPlanId}/task/${taskId}`, {
            method: "DELETE"
        });
        const result = await response.json();
        if (!response.ok) {
            showStatus(result.message || "삭제 실패", "error");
            return;
        }
        showStatus("할 일이 삭제되었습니다.", "success");
        await loadPlanTasks(selectedPlanId);
        await loadPlans();
    } catch (err) {
        console.error(err);
        showStatus("서버와 통신 중 오류가 발생했습니다.", "error");
    }
}

// 새 할 일 추가 폼 제출 이벤트 리스너 등록
if (planTaskAddForm) {
    planTaskAddForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!selectedPlanId) {
            showStatus("먼저 계획을 선택해주세요.", "error");
            return;
        }
        const title = taskTitleInput ? taskTitleInput.value.trim() : "";
        const dueDate = taskDueDateInput ? taskDueDateInput.value : "";
        if (!title) {
            showStatus("할 일 내용을 입력해주세요.", "error");
            return;
        }

        try {
            const response = await fetch(`/api/plan/${selectedPlanId}/tasks`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title, due_date: dueDate })
            });
            const result = await response.json();
            if (!response.ok) {
                showStatus(result.message || "추가 실패", "error");
                return;
            }
            showStatus("새로운 세부 할 일이 추가되었습니다.", "success");
            if (taskTitleInput) taskTitleInput.value = "";
            if (taskDueDateInput) taskDueDateInput.value = "";
            await loadPlanTasks(selectedPlanId);
            await loadPlans();
        } catch (err) {
            console.error(err);
            showStatus("서버와 통신 중 오류가 발생했습니다.", "error");
        }
    });
}

// 기간 표시 포맷
function formatPeriod(start, end) {
    return `${start} ~ ${end}`;
}

// 분을 보기 좋게 표시
function formatMinutes(minutes) {
    const value = Number(minutes);

    if (value < 60) {
        return `${value}분`;
    }

    const hours = Math.floor(value / 60);
    const remainingMinutes = value % 60;

    if (remainingMinutes === 0) {
        return `${hours}시간`;
    }

    return `${hours}시간 ${remainingMinutes}분`;
}

// HTML 이스케이프 유틸
function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// 새로운 계획 작성 모드
function showCreateMode() {
    closePlanDrawer(); // 새 계획 작성 시 열려있던 드로어 닫기
    editing = false;

    formTitle.textContent = "새 계획 작성";
    modeText.textContent = "새 계획";

    submitButton.textContent = "계획 저장";
    submitButton.classList.remove("hidden"); // 저장 버튼 활성화

    cancelButton.classList.add("hidden");
    newPlanFormBtn.classList.add("hidden");
    newPlanActionBtn.classList.add("hidden");

    form.reset();
    if (tagsInput) tagsInput.value = "";
    endDateInput.min = "";

    // 신규 작성 시 배정될 우선순위 표시
    const nextRank = allPlans.length + 1;
    formPriorityDisplay.textContent = `${nextRank}순위 (자동 배정)`;

    if (planTasksSection) planTasksSection.classList.add("hidden");

    // 다른 탭에서 새 계획 작성 클릭 시 PLAN 탭으로 전환
    if (activePdsTab !== "plan") {
        switchPdsTab("plan", true);
    } else if (formSection) {
        formSection.classList.remove("hidden");
        formSection.scrollIntoView({ behavior: "smooth" });
    }
}

// 계획 보기 모드
function showViewMode() {
    editing = false;

    formTitle.textContent = "나의 계획";
    modeText.textContent = "저장됨";

    submitButton.classList.add("hidden");
    cancelButton.classList.add("hidden");

    newPlanFormBtn.classList.remove("hidden");
    newPlanActionBtn.classList.remove("hidden");

    if (currentPlan) {
        formPriorityDisplay.textContent = currentPlan.current_priority || "1순위";
        if (planTasksSection) planTasksSection.classList.remove("hidden");
    }

    if (activePdsTab === "plan" && formSection) {
        formSection.classList.remove("hidden");
    }
}

// 수정 모드
function showEditMode() {
    if (!currentPlan) return;

    if (window.innerWidth <= 768) {
        closePlanDrawer(); // 모바일에서는 화면 공간 확보를 위해 드로어 닫기
    }

    editing = true;

    // 다른 탭에서 수정 클릭 시 PLAN 탭으로 전환
    if (activePdsTab !== "plan") {
        switchPdsTab("plan", true);
    } else if (formSection) {
        formSection.classList.remove("hidden");
    }

    formTitle.textContent = `계획 수정: ${currentPlan.title}`;
    modeText.textContent = "수정 중";

    submitButton.textContent = "수정 저장";
    submitButton.classList.remove("hidden");
    cancelButton.classList.remove("hidden");

    newPlanFormBtn.classList.add("hidden");
    newPlanActionBtn.classList.add("hidden");

    // 현재 선택된 계획 값을 입력창에 채움
    titleInput.value = currentPlan.title;
    formPriorityDisplay.textContent = currentPlan.current_priority || "1순위";
    startDateInput.value = currentPlan.current_start_date;
    endDateInput.value = currentPlan.current_end_date;
    endDateInput.min = currentPlan.current_start_date;
    successCriteriaInput.value = currentPlan.current_success_criteria;
    expectedMinutesInput.value = currentPlan.current_expected_minutes;
    if (tagsInput) tagsInput.value = currentPlan.tags || "";

    formSection.scrollIntoView({ behavior: "smooth" });
}

// 시작일 변경 시 종료일의 최소 날짜(min)를 시작일로 설정하여 과거 날짜 선택 방지
function updateEndDateMin() {
    if (startDateInput.value) {
        endDateInput.min = startDateInput.value;
        if (endDateInput.value && endDateInput.value < startDateInput.value) {
            endDateInput.value = startDateInput.value;
        }
    } else {
        endDateInput.min = "";
    }
}

startDateInput.addEventListener("input", updateEndDateMin);
startDateInput.addEventListener("change", updateEndDateMin);

endDateInput.addEventListener("change", function() {
    if (startDateInput.value && endDateInput.value && endDateInput.value < startDateInput.value) {
        showStatus("종료일은 시작일보다 빠를 수 없습니다.", "error");
        endDateInput.value = startDateInput.value;
    }
});

// 계획 저장 / 수정 전송
form.addEventListener("submit", async function(event) {
    event.preventDefault();

    const planData = {
        title: titleInput.value.trim(),
        start_date: startDateInput.value,
        end_date: endDateInput.value,
        success_criteria: successCriteriaInput.value.trim(),
        expected_minutes: Number(expectedMinutesInput.value),
        tags: tagsInput ? tagsInput.value.trim() : ""
    };

    if (!planData.title) {
        showStatus("계획을 입력해주세요.", "error");
        return;
    }

    if (!planData.start_date || !planData.end_date) {
        showStatus("기간을 입력해주세요.", "error");
        return;
    }

    if (planData.start_date > planData.end_date) {
        showStatus("시작일은 종료일보다 늦을 수 없습니다.", "error");
        return;
    }

    if (!planData.success_criteria) {
        showStatus("성공 기준을 입력해주세요.", "error");
        return;
    }

    if (!planData.expected_minutes || planData.expected_minutes <= 0) {
        showStatus("예상 시간을 입력해주세요.", "error");
        return;
    }

    try {
        let response;

        if (editing) {
            planData.id = currentPlan.id;
            planData.priority = currentPlan.current_priority;
            response = await fetch("/api/plan", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(planData)
            });
        } else {
            response = await fetch("/api/plan", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(planData)
            });
        }

        const result = await response.json();

        if (!response.ok) {
            showStatus(result.message || "저장에 실패했습니다.", "error");
            return;
        }

        showStatus(result.message, "success");

        if (!editing && result.plan_id) {
            selectedPlanId = result.plan_id;
        }

        editing = false;
        await loadPlans();

    } catch (error) {
        console.error(error);
        showStatus("서버와 연결할 수 없습니다.", "error");
    }
});

// 계획 삭제
async function deletePlan(id, title) {
    if (!confirm(`'${title}' 계획을 삭제하시겠습니까?`)) {
        return;
    }

    try {
        const response = await fetch(`/api/plan/${id}`, {
            method: "DELETE"
        });
        const result = await response.json();

        if (!response.ok) {
            showStatus(result.message || "삭제에 실패했습니다.", "error");
            return;
        }

        showStatus(result.message, "success");
        closePlanDrawer(); // 삭제 시 열려있던 드로어 닫기

        if (selectedPlanId === id) {
            selectedPlanId = null;
        }

        await loadPlans();

        // 삭제 후 남은 계획들의 우선순위를 1순위, 2순위...로 재정렬 저장
        if (allPlans.length > 0) {
            allPlans.forEach((plan, idx) => {
                plan.current_priority = `${idx + 1}순위`;
            });
            await savePriorityOrder();
            applyFiltersAndRender();
        }

        // 돌아보기 데이터 갱신
        await loadSeeData();

    } catch (error) {
        console.error(error);
        showStatus("서버와 연결할 수 없습니다.", "error");
    }
}

// 수정 버튼 이벤트
editButton.addEventListener("click", showEditMode);

// 상태 토글 버튼 이벤트 (현재 계획 상세 영역)
// [요구사항 4 & 5] 명시적인 대상 상태를 전달하여 멱등성 및 단일 완료 기록 보장
if (currentStatusBtn) {
    currentStatusBtn.addEventListener("click", () => {
        if (currentPlan) {
            const target = (currentPlan.status === "완료") ? "진행중" : "완료";
            togglePlanStatus(currentPlan.id, target);
        }
    });
}

// 삭제 버튼 이벤트 (현재 계획 영역의 삭제 버튼)
if (deleteButton) {
    deleteButton.addEventListener("click", () => {
        if (currentPlan) {
            deletePlan(currentPlan.id, currentPlan.title);
        }
    });
}

// 수정 취소
cancelButton.addEventListener("click", function() {
    if (currentPlan) {
        displayPlan(currentPlan);
        showViewMode();
    } else {
        showCreateMode();
    }
});

// 새 계획 작성 버튼 이벤트들
newPlanFormBtn.addEventListener("click", showCreateMode);
newPlanActionBtn.addEventListener("click", showCreateMode);
listNewPlanBtn.addEventListener("click", showCreateMode);

// 우선순위 변경 모드 버튼들
reorderToggleBtn.addEventListener("click", toggleReorderMode);
reorderDoneBtn.addEventListener("click", toggleReorderMode);

// 🔍 검색 및 필터 이벤트 리스너 등록
if (planSearchInput) {
    planSearchInput.addEventListener("input", applyFiltersAndRender);
}
if (searchClearBtn) {
    searchClearBtn.addEventListener("click", () => {
        planSearchInput.value = "";
        applyFiltersAndRender();
        planSearchInput.focus();
    });
}
if (filterStatus) {
    filterStatus.addEventListener("change", applyFiltersAndRender);
}
if (filterPriority) {
    filterPriority.addEventListener("change", applyFiltersAndRender);
}
if (filterTag) {
    filterTag.addEventListener("change", applyFiltersAndRender);
}
if (sortBy) {
    sortBy.addEventListener("change", applyFiltersAndRender);
}
if (filterResetBtn) {
    filterResetBtn.addEventListener("click", () => resetFilters(true));
}
if (emptyResetBtn) {
    emptyResetBtn.addEventListener("click", () => resetFilters(true));
}

// 상태 메시지 표시
function showStatus(message, type = "") {
    statusMessage.textContent = message;
    statusMessage.className = "status";

    if (type) {
        statusMessage.classList.add(type);
    }

    setTimeout(function() {
        statusMessage.textContent = "";
        statusMessage.className = "status";
    }, 3000);
}


// ==========================================================
// ⚡ Section 04: 실행 기록 (Do) 로직
// [요구사항 1, 2, 3] 시작/끝 시각, 실제 소요 시간, 막혔던 이유 저장 및 이전 기록 누적 보존
// ==========================================================

// 현재 로컬 일시 문자열 생성 (YYYY-MM-DDTHH:mm)
// zeroMinutes: true 이면 분을 00으로 고정
function getLocalDateTimeString(date = new Date(), zeroMinutes = false) {
    const pad = (n) => String(n).padStart(2, "0");
    const Y = date.getFullYear();
    const M = pad(date.getMonth() + 1);
    const D = pad(date.getDate());
    const h = pad(date.getHours());
    const m = zeroMinutes ? "00" : pad(date.getMinutes());
    return `${Y}-${M}-${D}T${h}:${m}`;
}

// 일시 포맷 (T를 공백으로 변경)
function formatDateTime(dtStr) {
    if (!dtStr) return "";
    return dtStr.replace("T", " ");
}

// 특정 입력창의 분을 :00 정각으로 설정하는 헬퍼
function setMinuteToZero(input) {
    if (!input) return;
    if (input.value) {
        input.value = input.value.slice(0, 14) + "00";
    } else {
        input.value = getLocalDateTimeString(new Date(), true);
    }
}

// [요구사항 1] 시작 시각에 맞춰 끝 시각의 최소값(min)을 설정하고, 끝 시각이 시작 시각보다 앞서지 않도록 자동 조정
function updateEndTimeMin() {
    if (!execStartTimeInput || !execEndTimeInput) return;
    const startVal = execStartTimeInput.value;
    if (startVal) {
        execEndTimeInput.min = startVal;
        // 만약 이미 입력된 끝 시각이 시작 시각보다 이전이라면 시작 시각으로 자동 조정
        if (execEndTimeInput.value && execEndTimeInput.value < startVal) {
            execEndTimeInput.value = startVal;
            showStatus("끝 시각이 시작 시각보다 이전이어서 시작 시각과 같게 자동 조정되었습니다.", "info");
            autoCalculateActualMinutes();
        }
    } else {
        execEndTimeInput.min = "";
    }
}

// [요구사항 1] 끝 시각 변경 시 시작 시각보다 이전인지 검증
function validateEndTimeNotBeforeStart() {
    if (!execStartTimeInput || !execEndTimeInput) return;
    const startVal = execStartTimeInput.value;
    const endVal = execEndTimeInput.value;
    if (startVal && endVal && endVal < startVal) {
        execEndTimeInput.value = startVal;
        showStatus("끝 시각은 시작 시각보다 이전일 수 없습니다. 시작 시각으로 자동 조정되었습니다.", "error");
        autoCalculateActualMinutes();
    }
}

// [요구사항 2] 브라우저(크롬 등)의 datetime-local에서 빈 분 필드에 위 화살표 입력 시 01부터 시작하는 현상을 방지하고 00부터 시작하도록 처리
function attachMinuteZeroHandler(input) {
    if (!input) return;

    let previousVal = input.value;
    let upKeyPressed = false;

    input.addEventListener("keydown", (e) => {
        if (e.key === "ArrowUp") {
            upKeyPressed = true;
        } else {
            upKeyPressed = false;
        }
    });

    input.addEventListener("input", () => {
        const currentVal = input.value;
        // 분이 방금 선택되면서 :01로 처음 입력된 경우 (이전 값이 비었거나 :00이 아니었던 상태에서 Up키 등으로 01이 됨) -> 00으로 시작하도록 보정
        if (currentVal && currentVal.endsWith(":01")) {
            if (!previousVal || (!previousVal.endsWith(":00") && upKeyPressed)) {
                input.value = currentVal.slice(0, -2) + "00";
            }
        }
        previousVal = input.value;
    });

    input.addEventListener("change", () => {
        previousVal = input.value;
    });
}

// 시작/끝 시각 입력 시 실제로 걸린 시간(분) 자동 계산
function autoCalculateActualMinutes() {
    if (!execStartTimeInput || !execEndTimeInput || !execActualMinutesInput) return;
    const startVal = execStartTimeInput.value;
    const endVal = execEndTimeInput.value;
    if (startVal && endVal) {
        const start = new Date(startVal);
        const end = new Date(endVal);
        const diffMs = end - start;
        if (diffMs >= 0) {
            const minutes = Math.round(diffMs / 60000);
            execActualMinutesInput.value = minutes;
        } else {
            execActualMinutesInput.value = 0;
        }
    }
}

// 특정 계획의 실행 기록 로드
async function loadPlanExecutions(planId) {
    if (!executionSection) return;
    if (!planId) {
        executionSection.classList.add("hidden");
        return;
    }

    try {
        const response = await fetch(`/api/plan/${planId}/executions`);
        const data = await response.json();
        const executions = data.executions || [];
        currentPlanExecutions = executions;
        const totalMinutes = data.total_actual_minutes || 0;
        renderPlanExecutions(executions, totalMinutes);
    } catch (error) {
        console.error("실행 기록 조회 실패:", error);
    }
}

// 실행 기록 목록 렌더링
function renderPlanExecutions(executions, totalMinutes) {
    if (!executionSection) return;
    if (activePdsTab === "do") {
        executionSection.classList.remove("hidden");
    }

    if (executionCountBadge) {
        executionCountBadge.textContent = `실행 ${executions.length}건`;
    }
    if (execHistoryCount) {
        execHistoryCount.textContent = executions.length;
    }
    if (execTotalMinutes) {
        execTotalMinutes.textContent = formatMinutes(totalMinutes);
    }

    updateTabBadges();

    if (!executions || executions.length === 0) {
        if (executionEmpty) executionEmpty.classList.remove("hidden");
        if (executionTableWrapper) executionTableWrapper.classList.add("hidden");
        if (executionListBody) executionListBody.innerHTML = "";
        return;
    }

    if (executionEmpty) executionEmpty.classList.add("hidden");
    if (executionTableWrapper) executionTableWrapper.classList.remove("hidden");
    if (executionListBody) executionListBody.innerHTML = "";

    const totalCount = executions.length;
    executions.forEach((item, index) => {
        const tr = document.createElement("tr");
        const roundNum = totalCount - index;

        const blockerHtml = item.blocker_reason && item.blocker_reason.trim()
            ? `<span class="blocker-pill" title="${escapeHtml(item.blocker_reason)}">🚧 ${escapeHtml(item.blocker_reason)}</span>`
            : `<span class="no-blocker">-</span>`;

        tr.innerHTML = `
            <td><strong>#${roundNum}회차</strong></td>
            <td style="font-size: 12px; color: #475569;">
                <div>시작: ${escapeHtml(formatDateTime(item.start_time))}</div>
                <div>종료: ${escapeHtml(formatDateTime(item.end_time))}</div>
            </td>
            <td><strong>${escapeHtml(formatMinutes(item.actual_minutes))}</strong></td>
            <td>${blockerHtml}</td>
            <td style="font-size: 12px; color: #64748b;">${escapeHtml(item.memo || "-")}</td>
            <td>
                <button type="button" class="exec-delete-btn" title="이 실행 기록 삭제">
                    삭제
                </button>
            </td>
        `;

        const delBtn = tr.querySelector(".exec-delete-btn");
        if (delBtn) {
            delBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                deleteExecution(item.id, item.plan_id);
            });
        }

        executionListBody.appendChild(tr);
    });
}

// 실행 기록 저장 이벤트 핸들러 (옵션 B: 시간대 겹침 시 확인 창 표시)
async function handleExecutionSubmit(event, confirmedOverlap = false) {
    if (event && event.preventDefault) event.preventDefault();

    if (!selectedPlanId) {
        showStatus("먼저 실행을 기록할 계획을 선택해주세요.", "error");
        return;
    }

    const startTime = execStartTimeInput.value;
    const endTime = execEndTimeInput.value;
    const actualMinutes = Number(execActualMinutesInput.value);
    const blockerReason = execBlockerReasonInput ? execBlockerReasonInput.value.trim() : "";
    const memo = execMemoInput ? execMemoInput.value.trim() : "";
    const markCompleted = execMarkCompleted ? execMarkCompleted.checked : false;

    if (!startTime || !endTime) {
        showStatus("실행 시작 시각과 끝 시각을 모두 입력해주세요.", "error");
        return;
    }

    if (startTime > endTime) {
        showStatus("시작 시각은 끝 시각보다 늦을 수 없습니다.", "error");
        return;
    }

    // 1. 완전 중복 검사 (시작 시각과 끝 시각이 동일한 경우) -> 엄격 차단
    const isExactDuplicate = currentPlanExecutions && currentPlanExecutions.some(item =>
        item.start_time === startTime && item.end_time === endTime
    );

    if (isExactDuplicate) {
        const errorMsg = "동일한 시작 시각과 끝 시각을 가진 실행 기록이 이미 등록되어 있습니다. 중복으로 저장할 수 없습니다.";
        showStatus(errorMsg, "error");
        alert(`⚠️ 실행 기록 중복 오류\n\n${errorMsg}\n\n• 시작 시각: ${formatDateTime(startTime)}\n• 끝 시각: ${formatDateTime(endTime)}`);
        execStartTimeInput.focus();
        return;
    }

    // 2. 시간대 겹침 검사 (동일 계획 내 겹침 확인) -> 옵션 B: 경고 확인창(confirm) 띄우기
    if (!confirmedOverlap && currentPlanExecutions) {
        const overlapping = currentPlanExecutions.filter(item =>
            item.start_time < endTime && item.end_time > startTime
        );

        if (overlapping.length > 0) {
            const overlapLines = overlapping.map(item =>
                `• ${formatDateTime(item.start_time)} ~ ${formatDateTime(item.end_time)} (${formatMinutes(item.actual_minutes)})`
            ).join("\n");

            const proceed = confirm(
                `⚠️ 실행 시간 중복(겹침) 안내\n\n` +
                `입력하신 시간이 기존 실행 기록과 일부 겹칩니다:\n` +
                `${overlapLines}\n\n` +
                `• 새 기록: ${formatDateTime(startTime)} ~ ${formatDateTime(endTime)}\n\n` +
                `시간이 겹쳐도 그대로 저장하시겠습니까?`
            );

            if (!proceed) {
                showStatus("실행 기록 저장을 취소했습니다. 시작/끝 시각을 다시 확인해주세요.", "info");
                execStartTimeInput.focus();
                return;
            }
            confirmedOverlap = true;
        }
    }

    if (!actualMinutes || actualMinutes <= 0) {
        showStatus("실제로 걸린 시간을 1분 이상 입력해주세요.", "error");
        return;
    }

    try {
        if (execSubmitBtn) {
            execSubmitBtn.disabled = true;
            execSubmitBtn.textContent = "저장 중...";
        }

        const response = await fetch(`/api/plan/${selectedPlanId}/execution`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                start_time: startTime,
                end_time: endTime,
                actual_minutes: actualMinutes,
                blocker_reason: blockerReason,
                memo: memo,
                mark_completed: markCompleted,
                confirm_overlap: confirmedOverlap
            })
        });

        const result = await response.json();

        if (!response.ok) {
            // 다른 계획과의 시간대 겹침 확인 (옵션 B)
            if (result.overlap && result.overlaps && !confirmedOverlap) {
                const overlapLines = result.overlaps.map(item =>
                    `• [${item.plan_title}] ${formatDateTime(item.start_time)} ~ ${formatDateTime(item.end_time)} (${formatMinutes(item.actual_minutes)})`
                ).join("\n");

                const proceed = confirm(
                    `⚠️ 실행 시간 중복(겹침) 안내\n\n` +
                    `입력하신 시간이 다른 계획의 기존 실행 기록과 겹칩니다:\n` +
                    `${overlapLines}\n\n` +
                    `• 새 기록: ${formatDateTime(startTime)} ~ ${formatDateTime(endTime)}\n\n` +
                    `시간이 겹쳐도 그대로 저장하시겠습니까?`
                );

                if (proceed) {
                    return handleExecutionSubmit(null, true);
                } else {
                    showStatus("실행 기록 저장을 취소했습니다. 시작/끝 시각을 조정해주세요.", "info");
                    return;
                }
            }

            const errorMsg = result.message || "실행 기록 저장 실패";
            showStatus(errorMsg, "error");
            if (result.duplicate || response.status === 409) {
                alert(`⚠️ 실행 기록 중복 오류\n\n${errorMsg}`);
            }
            return;
        }

        showStatus(result.message, "success");

        // 입력 폼 초기화 (막힌 이유, 메모, 완료 체크박스)
        if (execBlockerReasonInput) execBlockerReasonInput.value = "";
        if (execMemoInput) execMemoInput.value = "";
        if (execMarkCompleted) execMarkCompleted.checked = false;

        // 계획 목록, 실행 기록 및 돌아보기 즉시 갱신
        await loadPlans();
        await loadPlanExecutions(selectedPlanId);
        await loadSeeData();

    } catch (error) {
        console.error(error);
        showStatus("서버와 연결할 수 없습니다.", "error");
    } finally {
        if (execSubmitBtn) {
            execSubmitBtn.disabled = false;
            execSubmitBtn.textContent = "+ 실행 기록 저장";
        }
    }
}

// 실행 기록 개별 삭제
async function deleteExecution(executionId, planId) {
    if (!confirm("해당 실행 기록을 삭제하시겠습니까?")) {
        return;
    }

    try {
        const response = await fetch(`/api/execution/${executionId}`, {
            method: "DELETE"
        });
        const result = await response.json();

        if (!response.ok) {
            showStatus(result.message || "삭제 실패", "error");
            return;
        }

        showStatus(result.message, "success");
        await loadPlans();
        await loadPlanExecutions(planId);
        await loadSeeData();

    } catch (error) {
        console.error(error);
        showStatus("서버와 연결할 수 없습니다.", "error");
    }
}


// ==========================================================
// 📊 Section 05: 돌아보기 (See) 로직
// [요구사항 4, 5] 완료 버튼 2번 눌러도 완료 수 1만 증가, 계획 vs 실행 비교, 막힌 이유 분석
// ==========================================================

// 돌아보기 데이터 조회 및 렌더링 (첫 행동 1: 기간별로 계획·완료·지연·막힘 & 예상/실제 시간 모아보기)
async function loadSeeData() {
    if (!seeSection) return;

    try {
        const response = await fetch(`/api/see?period=${encodeURIComponent(currentSeePeriod)}`);
        const data = await response.json();
        if (!data.success) return;

        seeDataCache = data;

        // 기간 표시 텍스트 갱신
        if (seePeriodRangeText) {
            seePeriodRangeText.textContent = data.range_label || "전체 기간 집계";
        }

        // KPI 통계 업데이트
        if (seeTotalPlansCount) seeTotalPlansCount.textContent = data.total_plans || 0;
        if (seeCompletedCount) seeCompletedCount.textContent = data.completed_count || 0;
        if (seeDelayedCount) seeDelayedCount.textContent = data.delayed_count || 0;
        if (seeBlockedCount) seeBlockedCount.textContent = data.blocked_count || 0;
        if (seeCompletionRate) seeCompletionRate.textContent = data.completion_rate || 0;
        if (seeProgressFill) {
            seeProgressFill.style.width = `${Math.min(100, Math.max(0, data.completion_rate))}%`;
        }

        if (seeTimeSummary) {
            seeTimeSummary.textContent = `예상 ${formatMinutes(data.total_expected_minutes)} / 실제 ${formatMinutes(data.total_actual_minutes)}`;
        }

        if (seeTimeDiff) {
            const diff = data.time_difference;
            if (diff > 0) {
                seeTimeDiff.innerHTML = `계획 대비 <strong style="color: #c2410c;">+${formatMinutes(diff)}</strong> 더 소요됨`;
            } else if (diff < 0) {
                seeTimeDiff.innerHTML = `계획 대비 <strong style="color: #047857;">-${formatMinutes(Math.abs(diff))}</strong> 절약됨`;
            } else {
                seeTimeDiff.textContent = `계획 예상 시간과 실제 소요 시간 일치`;
            }
        }

        // 막혔던 이유 모아보기 렌더링
        renderSeeBlockers(data.blockers || []);

        // 계획 vs 실제 실행 비교 분석 표 렌더링
        renderSeeTable(data.plan_do_summaries || []);

        // 고칠 점 선택용 막힘 사유 드롭다운 갱신
        populateBlockerSelect(data.blockers || []);

        // 최근 전달된 고칠 점 목록 렌더링
        renderRecentActions(data.recent_actions || []);

        // 탭 뱃지(돌아보기 완료율 등) 갱신
        updateTabBadges();

    } catch (error) {
        console.error("돌아보기 데이터 조회 실패:", error);
    }
}

// 막혔던 이유 드롭다운 채우기
function populateBlockerSelect(blockers) {
    if (!actionBlockerSelect) return;
    actionBlockerSelect.innerHTML = `<option value="">-- 막혔던 이유 목록에서 선택 (클릭 시 자동 입력) --</option>`;

    if (!blockers || blockers.length === 0) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "(기록된 막힘 사유가 없습니다)";
        opt.disabled = true;
        actionBlockerSelect.appendChild(opt);
        return;
    }

    const seenReasons = new Set();
    blockers.forEach(b => {
        const reason = (b.blocker_reason || "").trim();
        if (reason && !seenReasons.has(reason)) {
            seenReasons.add(reason);
            const opt = document.createElement("option");
            opt.value = reason;
            opt.textContent = `[${b.plan_title}] ${reason}`;
            actionBlockerSelect.appendChild(opt);
        }
    });
}

// 최근 다음 계획으로 넘긴 고칠 점 칩 렌더링
function renderRecentActions(actions) {
    if (!nextActionRecentWrap || !recentActionChips) return;

    if (!actions || actions.length === 0) {
        nextActionRecentWrap.classList.add("hidden");
        recentActionChips.innerHTML = "";
        return;
    }

    nextActionRecentWrap.classList.remove("hidden");
    recentActionChips.innerHTML = "";

    actions.forEach(act => {
        const chip = document.createElement("span");
        chip.className = "recent-chip";
        chip.title = "클릭하여 다시 가져오기";
        chip.innerHTML = `<span>✏️ ${escapeHtml(act.action_text)}</span>`;
        chip.addEventListener("click", () => {
            if (nextActionInput) {
                nextActionInput.value = act.action_text;
                nextActionInput.focus();
            }
        });
        recentActionChips.appendChild(chip);
    });
}

// 막혔던 이유 모아보기 렌더링
function renderSeeBlockers(blockers) {
    if (!seeBlockersEmpty || !seeBlockersList) return;

    if (seeBlockerCountTag) {
        seeBlockerCountTag.textContent = `${blockers.length}건`;
    }

    if (!blockers || blockers.length === 0) {
        seeBlockersEmpty.classList.remove("hidden");
        seeBlockersList.classList.add("hidden");
        seeBlockersList.innerHTML = "";
        return;
    }

    seeBlockersEmpty.classList.add("hidden");
    seeBlockersList.classList.remove("hidden");
    seeBlockersList.innerHTML = "";

    blockers.forEach(b => {
        const card = document.createElement("div");
        card.className = "blocker-card";
        card.innerHTML = `
            <div class="blocker-card-header">
                <span class="blocker-plan-name">📌 ${escapeHtml(b.plan_title)}</span>
                <span class="blocker-time">${escapeHtml(formatDateTime(b.created_at))}</span>
            </div>
            <div class="blocker-card-body">
                🚧 ${escapeHtml(b.blocker_reason)}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px;">
                <span style="font-size: 11px; color: #64748b;">
                    소요: ${escapeHtml(formatMinutes(b.actual_minutes))}
                </span>
                <button type="button" class="trace-link-btn" title="이 문제를 고칠 점으로 입력창에 복사">
                    이 문제 고치기 ↗
                </button>
            </div>
        `;

        // '이 문제 고치기' 버튼 클릭 시 바로 고칠 점 입력창에 반영
        const fixBtn = card.querySelector(".trace-link-btn");
        if (fixBtn) {
            fixBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                if (nextActionInput) {
                    nextActionInput.value = `[개선] ${b.blocker_reason} 방지 및 대책 마련`;
                    const actionBox = document.getElementById("see-next-action-box");
                    if (actionBox) {
                        actionBox.scrollIntoView({ behavior: "smooth", block: "center" });
                        actionBox.classList.remove("pulse-highlight");
                        void actionBox.offsetWidth;
                        actionBox.classList.add("pulse-highlight");
                    }
                    nextActionInput.focus();
                }
            });
        }

        seeBlockersList.appendChild(card);
    });
}

// 계획 vs 실제 실행 비교 분석 표 렌더링 (원래 계획을 덮어쓰지 않고 나란히 비교 & 근거 추적 링크)
function renderSeeTable(summaries) {
    if (!seeTableBody) return;
    seeTableBody.innerHTML = "";

    if (!summaries || summaries.length === 0) {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td colspan="7" style="text-align: center; color: #94a3b8; padding: 20px;">선택된 기간에 해당하는 계획이 없습니다.</td>`;
        seeTableBody.appendChild(tr);
        return;
    }

    summaries.forEach(item => {
        const tr = document.createElement("tr");
        const isComp = (item.status === "완료");

        const statusBadge = `<span class="plan-status-badge status-${isComp ? "완료" : "진행중"}">${escapeHtml(item.status)}</span>`;

        const expMin = Number(item.current_expected_minutes || 0);
        const actMin = Number(item.actual_total_minutes || 0);

        let diffBadge = `<span class="diff-badge-zero">-</span>`;
        if (actMin > 0) {
            const diff = actMin - expMin;
            if (diff > 0) {
                diffBadge = `<span class="diff-badge-plus">+${formatMinutes(diff)}</span>`;
            } else if (diff < 0) {
                diffBadge = `<span class="diff-badge-minus">-${formatMinutes(Math.abs(diff))}</span>`;
            } else {
                diffBadge = `<span class="diff-badge-zero">0분 (일치)</span>`;
            }
        }

        const actText = actMin > 0
            ? `<strong>${formatMinutes(actMin)}</strong> <span style="font-size: 11px; color: #64748b;">(${item.execution_count}회)</span>`
            : `<span style="color: #94a3b8;">미실행 (0분)</span>`;

        const completedText = item.completed_at
            ? `<span style="color: #047857; font-weight: 600;">✓ ${escapeHtml(formatDateTime(item.completed_at))}</span>`
            : `<span style="color: #94a3b8;">진행중</span>`;

        const delayBadge = item.is_delayed ? `<span class="plan-status-badge status-지연" style="font-size: 10px; margin-left: 4px;">지연</span>` : "";

        tr.innerHTML = `
            <td>
                <strong>${escapeHtml(item.title)}</strong>
                ${delayBadge}
            </td>
            <td>${statusBadge}</td>
            <td>${escapeHtml(formatMinutes(expMin))}</td>
            <td>${actText}</td>
            <td>${diffBadge}</td>
            <td style="font-size: 12px;">${completedText}</td>
            <td>
                <button type="button" class="trace-link-btn row-trace-btn" title="이 계획의 실행 및 수정 기록 보기">
                    기록 보기 ↗
                </button>
            </td>
        `;

        const traceBtn = tr.querySelector(".row-trace-btn");
        if (traceBtn) {
            traceBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                selectPlan(item.id);
                openPlanDrawer();
                loadPlanExecutions(item.id);
                showStatus(`'${item.title}' 계획의 근거 기록(실행 및 수정 이력)을 열었습니다.`, "info");
            });
        }

        seeTableBody.appendChild(tr);
    });
}

// -------------------------------------------------------------
// 🔗 첫 행동 2: 집계 숫자를 눌렀을 때 그 숫자가 나온 기록으로 갈 수 있게 연결
// -------------------------------------------------------------

// 1. [계획 수] 카드 클릭 -> PLAN 탭의 전체 계획 목록으로 이동
if (kpiCardTotal) {
    kpiCardTotal.addEventListener("click", () => {
        switchPdsTab("plan", false);
        if (filterStatus) filterStatus.value = "all";
        applyFiltersAndRender();
        setTimeout(() => {
            if (planListSection) {
                planListSection.scrollIntoView({ behavior: "smooth", block: "start" });
                planListSection.classList.remove("pulse-highlight");
                void planListSection.offsetWidth;
                planListSection.classList.add("pulse-highlight");
            }
        }, 50);
        showStatus(`📋 PLAN 탭의 전체 계획 목록 (${seeDataCache ? seeDataCache.total_plans : 0}개)으로 이동했습니다.`, "info");
    });
}

// 2. [완료 수] 카드 클릭 -> PLAN 탭으로 이동 & 완료된 계획 목록으로 필터링
if (kpiCardCompleted) {
    kpiCardCompleted.addEventListener("click", () => {
        switchPdsTab("plan", false);
        if (filterStatus) filterStatus.value = "완료";
        applyFiltersAndRender();
        setTimeout(() => {
            if (planListSection) {
                planListSection.scrollIntoView({ behavior: "smooth", block: "start" });
                planListSection.classList.remove("pulse-highlight");
                void planListSection.offsetWidth;
                planListSection.classList.add("pulse-highlight");
            }
        }, 50);
        showStatus(`🎯 완료된 계획 (${seeDataCache ? seeDataCache.completed_count : 0}개) 목록으로 이동했습니다.`, "info");
    });
}

// 3. [지연 수] 카드 클릭 -> PLAN 탭으로 이동 & 지연된 계획 목록으로 필터링
if (kpiCardDelayed) {
    kpiCardDelayed.addEventListener("click", () => {
        switchPdsTab("plan", false);
        if (filterStatus) filterStatus.value = "지연";
        applyFiltersAndRender();
        setTimeout(() => {
            if (planListSection) {
                planListSection.scrollIntoView({ behavior: "smooth", block: "start" });
                planListSection.classList.remove("pulse-highlight");
                void planListSection.offsetWidth;
                planListSection.classList.add("pulse-highlight");
            }
        }, 50);
        showStatus(`⏰ 마감일이 지난 미완료 지연 계획 (${seeDataCache ? seeDataCache.delayed_count : 0}개) 목록으로 이동했습니다.`, "warning");
    });
}

// 4. [막힘 수] 카드 클릭 -> 막혔던 이유 모아보기 박스로 이동
if (kpiCardBlocked) {
    kpiCardBlocked.addEventListener("click", () => {
        const blockerBox = document.getElementById("see-blockers-box");
        if (blockerBox) {
            blockerBox.scrollIntoView({ behavior: "smooth", block: "center" });
            blockerBox.classList.remove("pulse-highlight");
            void blockerBox.offsetWidth;
            blockerBox.classList.add("pulse-highlight");
        }
        showStatus(`🚧 실행 중 막힘/병목이 발생했던 기록 (${seeDataCache ? seeDataCache.blocked_count : 0}건)입니다.`, "warning");
    });
}

// 5. [시간 분석] 카드 클릭 -> 계획 vs 실제 실행 비교 분석 표로 이동
if (kpiCardTime) {
    kpiCardTime.addEventListener("click", () => {
        const tableBox = document.getElementById("see-table-box");
        if (tableBox) {
            tableBox.scrollIntoView({ behavior: "smooth", block: "center" });
            tableBox.classList.remove("pulse-highlight");
            void tableBox.offsetWidth;
            tableBox.classList.add("pulse-highlight");
        }
        showStatus(`⏱ 계획 예상 시간과 실제 소요 시간의 차이를 비교한 표입니다.`, "info");
    });
}

// -------------------------------------------------------------
// 💡 첫 행동 3: 돌아보기에서 다음 계획으로 넘길 한 줄을 정합니다 (See → Plan 연결)
// -------------------------------------------------------------

// 막힘 사유 드롭다운 선택 시 고칠 점 입력창에 프리필
if (actionBlockerSelect) {
    actionBlockerSelect.addEventListener("change", () => {
        const selectedReason = actionBlockerSelect.value;
        if (selectedReason && nextActionInput) {
            nextActionInput.value = `[개선] ${selectedReason} 방지 및 선제 대응`;
            nextActionInput.focus();
        }
    });
}

// '🚀 다음 계획으로 넘기기' 버튼 클릭 이벤트 핸들러
if (btnTransferToPlan) {
    btnTransferToPlan.addEventListener("click", async () => {
        const text = nextActionInput ? nextActionInput.value.trim() : "";
        if (!text) {
            showStatus("다음 계획에서 개선할 고칠 점을 1가지 입력해주세요.", "error");
            if (nextActionInput) nextActionInput.focus();
            return;
        }

        try {
            // 서버에 고칠 점(액션 아이템) 보존
            await fetch("/api/see/next-action", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    action_text: text,
                    source_type: "reflection"
                })
            });
        } catch (err) {
            console.warn("고칠 점 저장 중 경고:", err);
        }

        // 새 계획 작성 모드로 폼 초기화 및 프리필
        if (typeof resetForm === "function") {
            resetForm();
        } else if (newPlanActionBtn) {
            newPlanActionBtn.click();
        }

        // 고칠 점 내용을 새 계획의 제목, 성공 기준, 태그에 반영
        if (titleInput) {
            titleInput.value = text.startsWith("[개선]") ? text : `[개선] ${text}`;
        }
        if (successCriteriaInput) {
            successCriteriaInput.value = `${text} 실천을 통해 지연과 막힘 없이 성공적으로 완수`;
        }
        if (tagsInput) {
            const currentTags = tagsInput.value.trim();
            tagsInput.value = currentTags ? `${currentTags}, 개선, 돌아보기` : `개선, 돌아보기`;
        }

        // 오늘 날짜로 시작일/종료일 기본 설정
        const todayStr = getLocalDateString();
        if (startDateInput) startDateInput.value = todayStr;
        if (endDateInput) endDateInput.value = todayStr;

        // 상단 새 계획 작성 폼으로 부드럽게 스크롤 이동 및 시각적 강조
        if (formSection) {
            formSection.scrollIntoView({ behavior: "smooth", block: "start" });
            formSection.classList.remove("pulse-highlight");
            void formSection.offsetWidth;
            formSection.classList.add("pulse-highlight");
        }

        if (expectedMinutesInput) {
            expectedMinutesInput.focus();
        }

        showStatus("✨ 돌아보기에서 정한 고칠 점이 새 계획(PLAN) 폼에 반영되었습니다! 예상 시간을 입력하고 저장하세요.", "success");

        // 입력창 비우고 돌아보기 최신화
        if (nextActionInput) nextActionInput.value = "";
        if (actionBlockerSelect) actionBlockerSelect.value = "";
        await loadSeeData();
    });
}

// 기간 선택 탭 이벤트 리스너 등록
if (seePeriodTabs) {
    seePeriodTabs.forEach(tab => {
        tab.addEventListener("click", async () => {
            seePeriodTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            currentSeePeriod = tab.dataset.period || "all";
            await loadSeeData();
        });
    });
}

// ⚡ Section 04 실행 기록 폼 이벤트 연결
if (executionForm) {
    executionForm.addEventListener("submit", handleExecutionSubmit);
}

// [요구사항 2] 브라우저 분 선택 시 00부터 시작하도록 핸들러 등록
attachMinuteZeroHandler(execStartTimeInput);
attachMinuteZeroHandler(execEndTimeInput);

// 시작 시각 '🕒 지금 시각' 버튼
if (btnNowStart) {
    btnNowStart.addEventListener("click", () => {
        if (execStartTimeInput) {
            execStartTimeInput.value = getLocalDateTimeString();
            updateEndTimeMin();
            autoCalculateActualMinutes();
        }
    });
}

// 시작 시각 ':00 정각' 버튼
if (btnZeroStart) {
    btnZeroStart.addEventListener("click", () => {
        if (execStartTimeInput) {
            setMinuteToZero(execStartTimeInput);
            updateEndTimeMin();
            autoCalculateActualMinutes();
        }
    });
}

// 끝 시각 '🕒 지금 시각' 버튼
if (btnNowEnd) {
    btnNowEnd.addEventListener("click", () => {
        if (execEndTimeInput) {
            execEndTimeInput.value = getLocalDateTimeString();
            validateEndTimeNotBeforeStart();
            autoCalculateActualMinutes();
        }
    });
}

// 끝 시각 ':00 정각' 버튼
if (btnZeroEnd) {
    btnZeroEnd.addEventListener("click", () => {
        if (execEndTimeInput) {
            setMinuteToZero(execEndTimeInput);
            validateEndTimeNotBeforeStart();
            autoCalculateActualMinutes();
        }
    });
}

// 시작 시각 입력/변경 시 끝 시각 min 제약 갱신 및 소요 시간 계산
if (execStartTimeInput) {
    execStartTimeInput.addEventListener("change", () => {
        updateEndTimeMin();
        autoCalculateActualMinutes();
    });
    execStartTimeInput.addEventListener("input", () => {
        updateEndTimeMin();
        autoCalculateActualMinutes();
    });
}

// 끝 시각 입력/변경 시 시작 시각 이전 선택 방지 검증 및 소요 시간 계산
if (execEndTimeInput) {
    execEndTimeInput.addEventListener("change", () => {
        validateEndTimeNotBeforeStart();
        autoCalculateActualMinutes();
    });
    execEndTimeInput.addEventListener("input", () => {
        validateEndTimeNotBeforeStart();
        autoCalculateActualMinutes();
    });
}

// 📊 Section 05 돌아보기 새로고침 버튼 이벤트
if (seeRefreshBtn) {
    seeRefreshBtn.addEventListener("click", async () => {
        await loadSeeData();
        showStatus("돌아보기(See) 데이터가 새로고침되었습니다.", "success");
    });
}

// 📥 전체 데이터 단일 파일(JSON) 내보내기 기능
function handleExportData() {
    showStatus("📥 내 계획과 기록 전체를 파일로 내보내는 중입니다...", "info");
    const downloadAnchor = document.createElement("a");
    downloadAnchor.href = "/api/export";
    downloadAnchor.download = "";
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    document.body.removeChild(downloadAnchor);
    setTimeout(() => {
        showStatus("✨ 내 계획과 기록 전체가 파일 하나(JSON)로 안전하게 내보내졌습니다!", "success");
    }, 600);
}

const exportTopBtn = document.getElementById("export-top-btn");
if (exportTopBtn) {
    exportTopBtn.addEventListener("click", handleExportData);
}

const seeExportBtn = document.getElementById("see-export-btn");
if (seeExportBtn) {
    seeExportBtn.addEventListener("click", handleExportData);
}

// ==========================================================
// 🧭 PDS 3단계 탭 네비게이션 이벤트 리스너 등록
// ==========================================================

// 1. 상단 탭 버튼 클릭 이벤트
if (tabBtns && tabBtns.length > 0) {
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const target = btn.dataset.tab;
            if (target) {
                switchPdsTab(target, true);
            }
        });
    });
}

// 2. 브라우저 뒤로가기/앞으로가기 URL 해시 변경 감지
window.addEventListener("hashchange", () => {
    const hash = window.location.hash.replace("#", "").toLowerCase();
    if (["plan", "do", "see"].includes(hash) && hash !== activePdsTab) {
        switchPdsTab(hash, false);
    }
});

// 3. DO 탭에서 다른 계획 선택하러 PLAN 탭으로 이동
if (btnSwitchToPlan) {
    btnSwitchToPlan.addEventListener("click", () => {
        switchPdsTab("plan", true);
    });
}

// 4. 드로어(상세)에서 이 계획의 실행 기록하러 DO 탭으로 이동
if (drawerGotoDoBtn) {
    drawerGotoDoBtn.addEventListener("click", () => {
        closePlanDrawer();
        switchPdsTab("do", true);
        if (execStartTimeInput) {
            execStartTimeInput.focus();
        }
    });
}
