"use strict";

(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const vm = JSON.parse($("#rcc-view-model").textContent);
  const nodeById = new Map(vm.nodes.map((node) => [node.node_id, node]));
  const componentById = new Map(vm.catalog.map((item) => [item.component_id, item]));
  const experimentById = new Map(vm.experiments.map((item) => [item.experiment_id, item]));
  const nav = $("#primary-navigation");
  const mobileToggle = $("#mobile-nav-toggle");
  const drawer = $("#detail-drawer");
  const drawerBackdrop = $("#drawer-backdrop");
  const drawerBody = $("#drawer-body");
  let lastFocus = null;
  let drawerItem = null;
  let drawerMode = "easy";
  let zoom = 1;

  const esc = (value) => String(value ?? "미확인").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[char]));
  const textList = (value) => String(value || "미확인").split(";").filter(Boolean);
  const list = (items) => `<ul>${items.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>`;

  function switchView(viewId, updateHash = true) {
    if (!vm.navigation.some((item) => item.view_id === viewId)) viewId = "overview";
    $$("[data-view-panel]").forEach((panel) => {
      const active = panel.dataset.viewPanel === viewId;
      panel.classList.toggle("is-active", active);
      panel.hidden = !active;
    });
    $$(".primary-nav-item").forEach((button) => {
      const active = button.dataset.view === viewId;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-current", active ? "page" : "false");
    });
    nav.classList.remove("is-open");
    mobileToggle.setAttribute("aria-expanded", "false");
    if (updateHash && location.hash !== `#${viewId}`) history.replaceState(null, "", `#${viewId}`);
    $("#main-workspace").focus({ preventScroll: true });
  }

  $$(".primary-nav-item").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.view)));
  $$('[data-go-view]').forEach((button) => button.addEventListener("click", () => switchView(button.dataset.goView)));
  mobileToggle.addEventListener("click", () => {
    const open = nav.classList.toggle("is-open");
    mobileToggle.setAttribute("aria-expanded", String(open));
  });
  window.addEventListener("hashchange", () => {
    const [viewId, nodeId] = location.hash.slice(1).split("/");
    switchView(viewId, false);
    if (viewId === "architecture" && nodeById.has(nodeId)) selectNode(nodeId, null);
  });

  $$("[data-compact-tab]").forEach((button) => button.addEventListener("click", () => {
    const selected = button.dataset.compactTab;
    $$("[data-compact-tab]").forEach((item) => item.classList.toggle("is-active", item === button));
    $$("[data-compact-panel]").forEach((panel) => { panel.hidden = panel.dataset.compactPanel !== selected; });
  }));

  function statusRail(status) {
    const fields = [["code","코드"],["execution","실행"],["evidence","근거 점검"],["integrity","무결성"],["reproduction","독립 재현"],["scientific_validation","과학 검증"]];
    return `<div class="status-rail">${fields.map(([key,label]) => `<span class="${status?.[key] ? "yes" : "no"}" aria-label="${esc(label)} ${status?.[key] ? "완료" : "미완료"}"><i></i>${esc(label)}</span>`).join("")}</div>`;
  }

  function componentTechnical(component) {
    return `<section class="drawer-section"><h3>Component contract</h3><dl class="technical-list">
      <div><dt>component ID</dt><dd><code>${esc(component.component_id)}</code></dd></div>
      <div><dt>source path</dt><dd>${list(textList(component.representative_path))}</dd></div>
      <div><dt>symbol</dt><dd><code>${esc(component.representative_symbol)}</code></dd></div>
      <div><dt>schema / artifact</dt><dd><code>${esc(component.artifact_refs)}</code></dd></div>
      <div><dt>tests</dt><dd><code>${esc(component.test_refs)}</code></dd></div>
      <div><dt>source ref</dt><dd><code>${esc(component.scientific_source_ref)}</code></dd></div>
    </dl></section>`;
  }

  function renderNodeDrawer(node) {
    const components = node.component_ids.map((id) => componentById.get(id)).filter(Boolean);
    $("#drawer-kicker").textContent = `${node.lane_id} · ${node.node_id}`;
    $("#drawer-title").textContent = node.label_ko;
    if (drawerMode === "easy") {
      drawerBody.innerHTML = `<p>${esc(node.subtitle_ko)}</p>${statusRail(node.status)}
        <section class="drawer-section"><h3>왜 필요한가</h3><p>${esc(node.easy_why_ko)}</p></section>
        <section class="drawer-section ipo-grid"><div><h3>Input</h3><p>${esc(node.input_ko)}</p></div><div><h3>처리</h3><p>${esc(node.process_ko)}</p></div><div><h3>Output</h3><p>${esc(node.output_ko)}</p></div></section>
        <section class="drawer-section"><h3>현재 결과</h3><p>${esc(node.current_result)}</p></section>
        <section class="drawer-section"><h3>아직 검증되지 않은 것</h3><p>${esc(node.unvalidated)}</p></section>
        <section class="drawer-section"><h3>다음 작업</h3><p>${esc(node.next_work)}</p></section>`;
    } else {
      drawerBody.innerHTML = `<section class="drawer-section"><h3>Node identity</h3><p><code>${esc(node.node_id)}</code></p><p>components: <code>${esc(node.component_ids.join("; "))}</code></p></section>
        ${components.map(componentTechnical).join("")}
        <section class="drawer-section"><h3>Audit reports</h3>${list(textList(node.audit_reports))}</section>`;
    }
    renderSubnodes(node.node_id);
  }

  function renderComponentDrawer(component) {
    $("#drawer-kicker").textContent = `Registry component · ${component.component_id}`;
    $("#drawer-title").textContent = component.name;
    drawerBody.innerHTML = drawerMode === "easy"
      ? `<p>${esc(component.research_role)}</p>${statusRail(component.state)}<section class="drawer-section ipo-grid"><div><h3>Input</h3><p>${esc(component.input_summary)}</p></div><div><h3>Output</h3><p>${esc(component.output_summary)}</p></div></section><section class="drawer-section"><h3>현재 상태</h3><p>${esc(component.scientific_status)}</p></section><section class="drawer-section"><h3>주요 위험</h3><p>${esc(component.risk_level)}</p></section><section class="drawer-section"><h3>다음 작업</h3><p>${esc(component.next_action)}</p></section>`
      : componentTechnical(component);
  }

  function renderExperimentDrawer(exp) {
    $("#drawer-kicker").textContent = `Experiment gate · ${exp.experiment_id}`;
    $("#drawer-title").textContent = exp.name;
    drawerBody.innerHTML = drawerMode === "easy"
      ? `<section class="drawer-section"><h3>연구질문</h3><p>${esc(exp.research_question)}</p></section><section class="drawer-section"><h3>현재 상태</h3><p>${esc(vm.labels[exp.gate.ready_now] || exp.gate.ready_now)}</p></section><section class="drawer-section"><h3>현재 근거</h3><p>${esc(exp.current_evidence)}</p></section><section class="drawer-section"><h3>먼저 해결할 것</h3><p>${esc(exp.gate.must_fix_before_start)}</p></section><section class="drawer-section"><h3>Claim impact</h3><p>${esc(exp.claim_impact)}</p></section>`
      : `<section class="drawer-section"><h3>Experiment contract</h3><dl class="technical-list"><div><dt>ID</dt><dd><code>${esc(exp.experiment_id)}</code></dd></div><div><dt>status</dt><dd><code>${esc(exp.status)}</code></dd></div><div><dt>artifact refs</dt><dd><code>${esc(exp.artifact_refs)}</code></dd></div><div><dt>source ref</dt><dd><code>${esc(exp.scientific_source_ref)}</code></dd></div><div><dt>source commit</dt><dd><code>${esc(exp.scientific_source_commit)}</code></dd></div></dl></section>`;
  }

  function renderDrawer() {
    if (!drawerItem) return;
    if (drawerItem.type === "node") renderNodeDrawer(drawerItem.value);
    if (drawerItem.type === "component") renderComponentDrawer(drawerItem.value);
    if (drawerItem.type === "experiment") renderExperimentDrawer(drawerItem.value);
  }

  function openDrawer(type, value, trigger) {
    lastFocus = trigger || document.activeElement;
    drawerItem = { type, value };
    drawerMode = "easy";
    $$("[data-drawer-mode]").forEach((button) => {
      const active = button.dataset.drawerMode === drawerMode;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", String(active));
    });
    renderDrawer();
    drawer.classList.add("is-open");
    drawer.setAttribute("aria-hidden", "false");
    drawerBackdrop.hidden = false;
    $("#drawer-close").focus();
  }

  function closeDrawer() {
    drawer.classList.remove("is-open");
    drawer.setAttribute("aria-hidden", "true");
    drawerBackdrop.hidden = true;
    if (lastFocus?.focus) lastFocus.focus();
  }

  $("#drawer-close").addEventListener("click", closeDrawer);
  drawerBackdrop.addEventListener("click", closeDrawer);
  $$("[data-drawer-mode]").forEach((button) => button.addEventListener("click", () => {
    drawerMode = button.dataset.drawerMode;
    $$("[data-drawer-mode]").forEach((item) => {
      const active = item === button;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-selected", String(active));
    });
    renderDrawer();
  }));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && drawer.classList.contains("is-open")) closeDrawer();
  });

  function graphReach(start, direction) {
    const reached = new Set();
    const queue = [start];
    while (queue.length) {
      const current = queue.shift();
      vm.edges.forEach((edge) => {
        const match = direction === "down" ? edge.source_node_id === current : edge.target_node_id === current;
        const next = direction === "down" ? edge.target_node_id : edge.source_node_id;
        if (match && !reached.has(next)) { reached.add(next); queue.push(next); }
      });
    }
    return reached;
  }

  function selectNode(nodeId, trigger, open = true) {
    const node = nodeById.get(nodeId);
    if (!node) return;
    const related = new Set([...graphReach(nodeId, "up"), ...graphReach(nodeId, "down"), nodeId]);
    const map = $("#view-architecture");
    $$(".arch-node", map).forEach((element) => {
      element.classList.toggle("is-selected", element.dataset.nodeId === nodeId);
      element.classList.toggle("is-related", related.has(element.dataset.nodeId) && element.dataset.nodeId !== nodeId);
      element.classList.toggle("is-dimmed", !related.has(element.dataset.nodeId));
    });
    $$(".arch-edge", map).forEach((edge) => edge.classList.toggle("is-dimmed", !(related.has(edge.dataset.source) && related.has(edge.dataset.target))));
    renderSubnodes(nodeId);
    if ($("#view-architecture").classList.contains("is-active")) history.replaceState(null, "", `#architecture/${nodeId}`);
    if (open) openDrawer("node", node, trigger);
  }

  function renderSubnodes(nodeId) {
    const strip = $("#subnode-strip");
    if (!strip) return;
    const group = vm.groups.expandable_groups.find((item) => item.parent_node_id === nodeId);
    if (!group) {
      strip.innerHTML = "<span>이 node에는 별도 세부 arm이 없습니다.</span>";
      return;
    }
    strip.innerHTML = `<strong>세부 node</strong>${group.detail_nodes.map((detail) => `<button type="button" data-detail-components="${esc(detail.component_ids.join(";"))}">${esc(detail.label)}</button>`).join("")}`;
    $$('[data-detail-components]', strip).forEach((button) => button.addEventListener("click", () => {
      const component = componentById.get(button.dataset.detailComponents.split(";")[0]);
      if (component) openDrawer("component", component, button);
    }));
  }

  $$(".arch-node").forEach((node) => {
    node.addEventListener("click", () => {
      if (node.closest("#view-overview")) switchView("architecture");
      selectNode(node.dataset.nodeId, node);
    });
    node.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); node.click(); }
    });
  });

  function applyMapFilters() {
    const root = $("#view-architecture");
    const query = $("#node-search").value.trim().toLowerCase();
    const lane = $("#lane-filter").value;
    const riskOnly = $("#risk-filter").checked;
    const frozenOnly = $("#frozen-only").checked;
    const showUnknown = $("#show-unknown").checked;
    $$(".arch-node", root).forEach((element) => {
      const node = nodeById.get(element.dataset.nodeId);
      const matches = (!query || `${node.label_ko} ${node.subtitle_ko} ${node.component_ids.join(" ")}`.toLowerCase().includes(query)) && (!lane || node.lane_id === lane) && (!riskOnly || ["HIGH","CRITICAL"].includes(node.risk_level));
      element.style.display = matches ? "" : "none";
      const rail = element.nextElementSibling;
      if (rail?.classList.contains("node-rail-object")) rail.style.display = matches ? "" : "none";
    });
    $$(".arch-edge", root).forEach((edge) => {
      const allowed = (!frozenOnly || edge.dataset.edgeClass === "FROZEN_EXECUTION") && (showUnknown || edge.dataset.edgeClass !== "DESIGN_CONDITIONAL");
      edge.style.display = allowed ? "" : "none";
    });
  }
  ["#node-search","#lane-filter","#risk-filter","#frozen-only","#show-unknown"].forEach((selector) => $(selector)?.addEventListener("input", applyMapFilters));
  function applyZoom() { $("#map-stage").style.transform = `scale(${zoom})`; $("#map-stage").style.width = `${100 / zoom}%`; }
  $("#zoom-in")?.addEventListener("click", () => { zoom = Math.min(1.6, zoom + .1); applyZoom(); });
  $("#zoom-out")?.addEventListener("click", () => { zoom = Math.max(.7, zoom - .1); applyZoom(); });
  $("#fit-view")?.addEventListener("click", () => { zoom = 1; applyZoom(); });
  $("#reset-map")?.addEventListener("click", () => {
    zoom = 1; applyZoom();
    ["#node-search","#lane-filter"].forEach((selector) => { $(selector).value = ""; });
    ["#risk-filter","#frozen-only"].forEach((selector) => { $(selector).checked = false; });
    $("#show-unknown").checked = true;
    $$(".arch-node,.arch-edge", $("#view-architecture")).forEach((element) => element.classList.remove("is-selected","is-related","is-dimmed"));
    applyMapFilters();
  });

  function applyCatalogFilters() {
    const query = $("#catalog-search").value.trim().toLowerCase();
    const lane = $("#catalog-lane").value;
    const risk = $("#catalog-risk").value;
    let visible = 0;
    $$(".catalog-row").forEach((row) => {
      const show = (!query || row.dataset.search.includes(query)) && (!lane || row.dataset.lane === lane) && (!risk || row.dataset.risk === risk);
      row.hidden = !show;
      if (show) visible += 1;
    });
    $("#catalog-count").textContent = `${visible}개`;
  }
  ["#catalog-search","#catalog-lane","#catalog-risk"].forEach((selector) => $(selector)?.addEventListener("input", applyCatalogFilters));
  $$(".catalog-row").forEach((row) => {
    const open = () => { const component = componentById.get(row.dataset.componentId); if (component) openDrawer("component", component, row); };
    row.addEventListener("click", open);
    row.addEventListener("keydown", (event) => { if (event.key === "Enter") open(); });
  });
  $$(".experiment-row").forEach((row) => {
    const open = () => { const exp = experimentById.get(row.dataset.experimentId); if (exp) openDrawer("experiment", exp, row); };
    row.addEventListener("click", open);
    row.addEventListener("keydown", (event) => { if (event.key === "Enter") open(); });
  });
  function applyGapFilters() {
    const disposition = $("#gap-disposition").value;
    const priority = $("#gap-priority").value;
    $$("#gap-table-body tr").forEach((row) => { row.hidden = !((!disposition || row.dataset.disposition === disposition) && (!priority || row.dataset.priority === priority)); });
  }
  $("#gap-disposition")?.addEventListener("input", applyGapFilters);
  $("#gap-priority")?.addEventListener("input", applyGapFilters);

  const [initialView, initialNode] = location.hash.slice(1).split("/");
  switchView(initialView || "overview", false);
  if (initialView === "architecture" && nodeById.has(initialNode)) setTimeout(() => selectNode(initialNode, null), 0);
  applyCatalogFilters();
})();
