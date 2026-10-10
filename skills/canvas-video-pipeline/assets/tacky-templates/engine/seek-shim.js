/*
 * seek-shim.js — 虛擬時鐘墊片（渲染器注入用，須在頁面任何 script 之前執行）
 * 接管 setTimeout / setInterval / requestAnimationFrame / performance.now / Date.now，
 * 讓整頁動畫改由 window.__tick(秒) 驅動：逐格前進、可精準停格，渲染結果 100% 可重現。
 */
(() => {
  "use strict";
  let vnow = 0; // 虛擬時間（ms）

  const timers = [];
  let timerId = 1;
  const rafQ = [];
  let rafId = 1;
  const born = new WeakMap(); // 每個動畫的出生虛擬時間

  window.setTimeout = (fn, d = 0, ...args) => {
    if (typeof fn !== "function") return timerId++;
    timers.push({ id: timerId, at: vnow + Math.max(0, +d || 0), fn, args, every: null });
    return timerId++;
  };
  window.setInterval = (fn, d = 0, ...args) => {
    if (typeof fn !== "function") return timerId++;
    const every = Math.max(1, +d || 1);
    timers.push({ id: timerId, at: vnow + every, fn, args, every });
    return timerId++;
  };
  window.clearTimeout = window.clearInterval = (id) => {
    const i = timers.findIndex((t) => t.id === id);
    if (i >= 0) timers.splice(i, 1);
  };
  window.requestAnimationFrame = (fn) => {
    rafQ.push({ id: rafId, fn });
    return rafId++;
  };
  window.cancelAnimationFrame = (id) => {
    const i = rafQ.findIndex((r) => r.id === id);
    if (i >= 0) rafQ.splice(i, 1);
  };
  performance.now = () => vnow;
  const epoch = Date.now();
  Date.now = () => epoch + vnow;

  // 把「這一刻之後才出現」的動畫（class 觸發的 CSS animation/transition、element.animate）
  // 登記出生時間並暫停，之後全部由 seekAll 撥指針
  function adoptNew() {
    for (const a of document.getAnimations()) {
      if (!born.has(a)) {
        born.set(a, vnow);
        try { a.pause(); } catch (e) {}
      }
    }
  }
  function seekAll() {
    for (const a of document.getAnimations()) {
      if (!born.has(a)) { born.set(a, vnow); }
      try {
        a.pause();
        a.currentTime = Math.max(0, vnow - born.get(a));
      } catch (e) {}
    }
  }

  window.__tick = (tSec) => {
    const target = tSec * 1000;
    // 依序觸發到期的計時器（觸發當下 vnow = 它的到期時間，動畫出生時間才會準）
    for (;;) {
      let next = null;
      for (const t of timers) if (!next || t.at < next.at) next = t;
      if (!next || next.at > target) break;
      vnow = next.at;
      if (next.every) next.at += next.every;
      else timers.splice(timers.indexOf(next), 1);
      try { next.fn(...(next.args || [])); } catch (e) {}
      adoptNew();
    }
    vnow = target;
    // 這一格的 rAF 批次（rAF 裡再排的 rAF 留到下一格，符合瀏覽器語意）
    const batch = rafQ.splice(0);
    for (const r of batch) { try { r.fn(vnow); } catch (e) {} }
    adoptNew();
    seekAll();
    return true;
  };

  // 頁面載入完成後呼叫一次：收編載入即開跑的動畫（出生時間 = 0）
  window.__seekInit = () => { vnow = 0; adoptNew(); seekAll(); return true; };
})();
