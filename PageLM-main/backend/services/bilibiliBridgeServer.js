import express from "express";
import cors from "cors";
import mcpManager from "./mcpManager.js";

const app = express();
const host = process.env.BILIBILI_BRIDGE_HOST || "127.0.0.1";
const port = Number(process.env.BILIBILI_BRIDGE_PORT || 5001);

app.use(cors());
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({
    ok: true,
    service: "bilibili-mcp-bridge",
    ready: Boolean(mcpManager.ready),
  });
});

app.get("/api/bilibili/search", async (req, res) => {
  try {
    const keyword = String(req.query.keyword || "").trim();
    if (!keyword) {
      return res.status(400).json({ ok: false, error: "keyword required" });
    }

    const items = await mcpManager.searchVideos(keyword);
    return res.json({ ok: true, keyword, items });
  } catch (error) {
    return res.status(500).json({
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    });
  }
});

async function bootstrap() {
  await mcpManager.init();

  app.listen(port, host, () => {
    console.log(`[bilibili-bridge] listening on http://${host}:${port}`);
  });
}

bootstrap().catch((error) => {
  console.error("[bilibili-bridge] failed to start:", error);
  process.exit(1);
});

process.on("SIGINT", async () => {
  await mcpManager.close();
  process.exit(0);
});

process.on("SIGTERM", async () => {
  await mcpManager.close();
  process.exit(0);
});
