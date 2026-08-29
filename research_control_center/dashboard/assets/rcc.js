"use strict";

(() => {
  const search = document.querySelector("#registry-search");
  const status = document.querySelector("#status-filter");
  const count = document.querySelector("#filter-count");
  const cards = Array.from(document.querySelectorAll(".registry-card"));

  function applyFilters() {
    const query = search.value.trim().toLowerCase();
    const selected = status.value;
    let visible = 0;
    cards.forEach((card) => {
      const matchesQuery = !query || card.dataset.search.includes(query);
      const matchesStatus = !selected || card.dataset.status === selected;
      card.hidden = !(matchesQuery && matchesStatus);
      if (!card.hidden) visible += 1;
    });
    count.textContent = `${visible} of ${cards.length} records`;
  }

  search.addEventListener("input", applyFilters);
  status.addEventListener("change", applyFilters);
  applyFilters();
})();
