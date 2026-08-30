import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const debugPort = process.env.RCC_CHROME_DEBUG_PORT || "9223";
const dashboardUrl = process.env.RCC_DASHBOARD_URL || "http://127.0.0.1:8765/dashboard/index.html";
const outputDir = path.join(path.dirname(fileURLToPath(import.meta.url)), "screenshots");
const captures = [
  ["01_overview_1440x900.png", 1440, 900, "#overview", false],
  ["02_architecture_1440x900.png", 1440, 900, "#architecture", false],
  ["03_architecture_node_selected_1440x900.png", 1440, 900, "#architecture/NODE_D1", false],
  ["04_experiments_1440x900.png", 1440, 900, "#experiments", false],
  ["05_readiness_risk_1440x900.png", 1440, 900, "#readiness", false],
  ["06_overview_1366x768.png", 1366, 768, "#overview", false],
  ["07_overview_1920x1080.png", 1920, 1080, "#overview", false],
  ["08_mobile_390x844.png", 390, 844, "#overview", true],
];

const pause = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
let version;
for (let attempt = 0; attempt < 40; attempt += 1) {
  try {
    const response = await fetch(`http://127.0.0.1:${debugPort}/json/version`);
    if (response.ok) {
      version = await response.json();
      break;
    }
  } catch {
    // Chrome may still be starting.
  }
  await pause(100);
}
if (!version) throw new Error(`Chrome DevTools endpoint unavailable on port ${debugPort}`);

const targetResponse = await fetch(
  `http://127.0.0.1:${debugPort}/json/new?${encodeURIComponent("about:blank")}`,
  { method: "PUT" },
);
if (!targetResponse.ok) throw new Error(`Cannot create Chrome target: ${targetResponse.status}`);
const target = await targetResponse.json();
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});

let messageId = 0;
const pending = new Map();
socket.addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  if (!message.id || !pending.has(message.id)) return;
  const { resolve, reject } = pending.get(message.id);
  pending.delete(message.id);
  if (message.error) reject(new Error(`${message.error.code}: ${message.error.message}`));
  else resolve(message.result || {});
});
const call = (method, params = {}) => new Promise((resolve, reject) => {
  messageId += 1;
  pending.set(messageId, { resolve, reject });
  socket.send(JSON.stringify({ id: messageId, method, params }));
});

await call("Page.enable");
fs.mkdirSync(outputDir, { recursive: true });
for (const [name, width, height, hash, mobile] of captures) {
  await call("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 1,
    mobile,
    screenWidth: width,
    screenHeight: height,
  });
  await call("Page.navigate", { url: `${dashboardUrl}${hash}` });
  await pause(500);
  if (!hash.includes("/NODE_D1")) {
    await call("Runtime.evaluate", {
      expression: "document.querySelector('#drawer-close')?.click()",
      returnByValue: true,
    });
  }
  await pause(400);
  const { data } = await call("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: false,
    fromSurface: true,
  });
  fs.writeFileSync(path.join(outputDir, name), Buffer.from(data, "base64"));
}

socket.close();
await fetch(`http://127.0.0.1:${debugPort}/json/close/${target.id}`);
console.log(`Captured ${captures.length} RCC Dashboard V2 screenshots in ${outputDir}`);
